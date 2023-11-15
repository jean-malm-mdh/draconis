import functools
import json
import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

import regex

from checks.rule_utility_functions import unique
from .point import Point
from .ast_typing import DataflowDirection, ParameterType, SafeClass
from .blocks import FBD_Block, VarBlock
from .path import PathDivide
from .comment_box import CommentBox
from .utilities import indexOrNone
from .variables import VariableWorkSheet, VariableLine
from .block_port import Port


def dropWhile(aList: list, p):
    for i in range(len(aList)):
        if not (p(aList[i])):
            return aList[i:]
    return []


@dataclass()
class Program:
    progName: str
    varHeader: VariableWorkSheet
    behaviourElements: List[FBD_Block]
    behaviour_id_map: Dict[int, FBD_Block]
    backward_flow: Optional[Dict[str, List[int]]]
    forward_flow: Optional[Dict[str, List[int]]]
    lines: List[Tuple[Point, Point]]
    comments: List[CommentBox]

    def toJSON(self):
        import json

        var_group_dict = self.varHeader.toJSON()
        behaviour_id_elements = ", ".join([e.toJSON() for e in self.behaviourElements])
        lines = ", ".join([f"[{p1.toJSON()}, {p2.toJSON()}]" for p1, p2 in self.lines])
        comments = ", ".join([com.toJSON() for com in self.comments])
        json_result = f"""
        {{
            "progName": "{self.progName}",
            "variableGroups": {var_group_dict},
            "behaviourElements": [
                {behaviour_id_elements}
            ],
            "lines": [{lines}],
            "comments": [{comments}]
        }}
        """
        return (
            json.dumps(json.loads(json_result), indent=2)
            # The JSON parser does not like quoted strings
            .replace('"true"', "true").replace('"false"', "false")
        )

    @classmethod
    def fromJSON(cls, json_s):
        d = json.loads(json_s)

        varSheet_fromjson = VariableWorkSheet.fromJSON(d["variableGroups"])
        behaviour_elements_json = [e for e in d["behaviourElements"]]
        # prog = Program(d["progName"], varSheet_fromjson, )
        pass

    def __init__(
            self,
            name,
            varWorkSheet,
            behaviourElementList=None,
            behaviourIDMap=None,
            lines=None,
    ):
        self.progName = name
        self.varHeader = varWorkSheet
        self.behaviourElements = behaviourElementList or []
        self.lines = lines or []
        self.behaviour_id_map = behaviourIDMap or {}

        # These values are computed after construction
        self.backward_flow = None
        self.forward_flow = None

        self.ports = {}

    def post_parsing_analysis(self):
        """
        Performs some necessary pre-steps for other analyses.
        Returns:
            No return value - will mutate the instance object
        """

        def make_ADT_consistent():
            """
            Sets up and connects all the ports mapping
            Returns:

            """

            def addPortConnectionToBlock(blockID, portID, connection):
                targetPort = self.ports.get(portID, None)
                if targetPort is None:
                    targetPort = Port(
                        portID=portID,
                        blockID=blockID,
                        rel_connection_direction=connection.connectionDir,
                        rel_position=Point(
                            connection.data.position.x, connection.data.position.y
                        ),
                        connections=set(),
                    )
                    self.ports[portID] = targetPort
                    self.behaviour_id_map[blockID].ports[portID] = targetPort
                for conn in connection.connections:
                    start_point = conn.startPoint.connectionIndex
                    otherPoint = start_point if start_point is not None else conn.endPoint.connectionIndex
                    targetPort.connections.add(otherPoint)

            # First, fill all forwards connections
            fbd_blocks = [
                block
                for block in self.behaviourElements
                if isinstance(block, FBD_Block)
            ]
            for block in fbd_blocks:
                for ID, conn in [
                    (c.ID, c.connectionPoint) for c in block.getInputVars()
                ]:
                    addPortConnectionToBlock(block.getID(), ID, conn)
                for ID, conn in [
                    (c.ID, c.connectionPoint) for c in block.getOutputVars()
                ]:
                    addPortConnectionToBlock(block.getID(), ID, conn)
            output_blocks = [
                block for block in self.behaviourElements if isinstance(block, VarBlock)
            ]
            for block in output_blocks:
                addPortConnectionToBlock(
                    block.getID(), block.getID(), block.outConnection
                )

            ports = list(self.ports.items())
            for p_id, p_data in ports:
                for conn in p_data.connections:
                    startPort = self.ports.get(conn, None)
                    startPort.connections.add(p_id)

        def correctGraphicalDetails():
            # Lines are in their own coordinate space.
            # To ease work during rendering, they are moved once into the model's space
            self.lines = [(
                Point(line[0].x * 2, line[0].y * 2),
                (Point(line[1].x * 2, line[1].y * 2)),
            ) for line in self.lines]

        make_ADT_consistent()
        correctGraphicalDetails()

    def getVarGroups(self):
        return self.varHeader.varGroups

    def getVarInfo(self):
        """
        Computes and returns a number of metrics related to variables in a lookup table.
        Returns:
            A python dictionary with the following lookups:
            'OutputVariables': The output variables of the program
            'InputVariables': The input variables of the program
            'InternalVariables': The 'other' variables of the program
            'Safeness': A classification if the variable is of a _safe_ type.
        Usage:
            Given a program p, the following would provide information about the input variable 'input1':
            p.getVarInfo()["InputVariables"]["input1"]
        """

        def list_to_name_dict(allVars: list[VariableLine]):
            return {v.name: v for v in allVars}

        res = dict()
        res["OutputVariables"] = list_to_name_dict(
            self.varHeader.getVarsByType(ParameterType.OutputVar)
        )
        res["InputVariables"] = list_to_name_dict(
            self.varHeader.getVarsByType(ParameterType.InputVar)
        )
        res["InternalVariables"] = list_to_name_dict(
            self.varHeader.getVarsByType(ParameterType.InternalVar)
        )
        res["Safeness"] = dict(
            [
                (
                    name_type[0],
                    SafeClass.Safe if "SAFE" in name_type[1] else SafeClass.Unsafe,
                )
                for name_type in self.getVarDataColumns("name", "valueType")
            ]
        )
        return res

    def getVarDataColumns(self, *args):
        """

        Args:
            *args: The columns to extract, as strings

        Returns:
            a list l of list v where v are the properties extracted from the variable sheet

        Example:
            Given a program p, the following function calls would extract the name and description of all variables:
            p.getVarDataColumns("name", "description")
        """

        def getFieldContent(fieldList, element):
            theVars = vars(element)
            return [str(theVars.get(k, None)) for k in fieldList]

        _fields = (
            VariableLine.__dict__["__annotations__"].keys() if len(args) == 0 else args
        )
        return [getFieldContent(_fields, e) for e in self.varHeader.getAllVariables()]

    def performBackTraceFromBlock(self, bID, trace_from_portID=None):
        def appendIfNotInListEnd(l, elem):
            if not l or l[-1] != elem:
                l.append(elem)

        def extendIfFirstIsSame(acc, l):
            if len(acc) == 0:
                return []
            if l[0] == acc[-1]:
                acc.extend(l[1:])

        b = (
                self.behaviour_id_map.get(bID, None)
                or self.behaviour_id_map[self.ports[bID].blockID]
        )
        result = []
        # flow is a list of tuples of (startPort, [(endPorts, end_connection_ports)])
        flow = b.getFlow(DataflowDirection.Backward, trace_from_portID)
        if flow == []:
            return [bID]
        elif len(flow) == 1:  # The number of output ports is one
            startPort, connectionPorts = flow[0]
            appendIfNotInListEnd(result, startPort)

            if len(connectionPorts) == 1:  # The number of input ports is one
                appendIfNotInListEnd(result, connectionPorts[0][0])
                appendIfNotInListEnd(result, connectionPorts[0][1])
                recurse = self.performBackTraceFromBlock(
                    connectionPorts[0][1], connectionPorts[0][1]
                )
                for r in recurse:
                    appendIfNotInListEnd(result, r)
            else:
                recurse = [
                    (
                        toPort,
                        self.performBackTraceFromBlock(connectingPort, connectingPort),
                    )
                    for toPort, connectingPort in connectionPorts
                ]
                dividing_paths = []
                for toPort, r in recurse:
                    _recurse = []
                    appendIfNotInListEnd(_recurse, toPort)
                    for _r in r:
                        appendIfNotInListEnd(_recurse, _r)
                    dividing_paths.append(_recurse)
                result.append(PathDivide(dividing_paths))
            return result

        return result

    def getBackwardTrace(self):
        """

        Returns: A backwards trace starting from all outputs.

        """

        def split_paths(
                paths: list[Tuple[int, List[Tuple[int, int]]]], computed_subpaths
        ):
            def get_path_given_start_point(start_id, end_id, computed_subpaths):
                for subPath in computed_subpaths:
                    if start_id == subPath[0]:
                        return subPath
                return [start_id] if end_id is None else [start_id, end_id]

            result = [
                [p[0]]
                + get_path_given_start_point(p[1][0][0], p[1][0][1], computed_subpaths)
                for p in paths
            ]
            return PathDivide(result)

        def performTrace(start_blocks):
            result = dict()
            for b in start_blocks:
                result[b.getVarExpr()] = self.performBackTraceFromBlock(b.getID())
            return result

        # Check if value is memoized, if so - return memoized version
        if self.backward_flow is not None:
            return self.backward_flow

        outport_blocks = [
            e
            for e in self.behaviourElements
            if (e.getBlockType() == "Port") and e.data.type == "outVariable"
        ]
        result = performTrace(outport_blocks)
        # Memoize backward trace
        self.backward_flow = result

        return result

    def getTrace(self, direction=DataflowDirection.Backward):
        def ComputeForwardFlowFromBack(back_flow):
            """

            Args:
                back_flow: The computed backwards flow

            Returns: From each inport, provides the dataflow paths to the outports

            """
            if self.forward_flow is not None:
                return self.forward_flow

            flattened_flow = [
                e for e in [PathDivide.unpack_pathlist([f]) for f in back_flow.values()]
            ]
            interface_blocks = [
                e for e in self.behaviourElements if e.getBlockType() == "Port"
            ]
            # Assumption: We care only about inports
            start_blocks = [b for b in interface_blocks if b.data.type == "inVariable"]
            result = dict()

            # Add all results to entry with key 'expr
            for block in start_blocks:
                expr = (
                    # Variable name or constant. if constant, has form <TYPE>#<VALUE> (e.g., UINT#3)
                    block.getVarExpr()
                )
                # To trace from front to back, we need to find IDs of all inports
                ID = block.data.localID
                # Check if the result list already exists - otherwise will clear previous computations
                if result.get(expr, None) is None:
                    result[expr] = []  # Initialize a new list to fill up with paths

                # Extract related paths from backward flow
                for outport_pathlist in flattened_flow:
                    for path in outport_pathlist:
                        # Find if path contains the ID of interest, and where
                        i = indexOrNone(path, ID)
                        if i is not None:
                            # slice so that ID is at end, then reverse
                            _res = path[: (i + 1)]
                            _res.reverse()
                            result[expr].append(_res)
            self.forward_flow = result
            return result

        if direction == DataflowDirection.Backward:
            return self.getBackwardTrace()
        else:
            backwards = self.getBackwardTrace()
            return ComputeForwardFlowFromBack(backwards)

    def getMetrics(self):
        res = dict()
        res["NrOfVariables"] = len(self.varHeader.getAllVariables())

        blocks = [
            e for e in self.behaviourElements if "FunctionBlock" in e.getBlockType()
        ]
        res["NrOfFuncBlocks"] = len(blocks)
        res["NrInputVariables"] = len(
            self.varHeader.getVarsByType(ParameterType.InputVar)
        )
        res["NrOutputVariables"] = len(
            self.varHeader.getVarsByType(ParameterType.OutputVar)
        )
        backwards_flow = self.getBackwardTrace()

        res["LongestSignalPath"] = max(map(len, backwards_flow.values()))
        res["ShortestSignalPath"] = min(map(len, backwards_flow.values()))

        return res

    def checkSafeDataFlow(self):
        def exprIsConsideredSafe(safenessProperties, candidate_expr):
            # it is a constant
            if "#" in candidate_expr:
                return "SAFE" in candidate_expr
            else:
                res = safenessProperties.get(candidate_expr, None)
                if res is None:
                    # log issue
                    logging.log(
                        level=logging.WARNING,
                        msg=f"No safety information for {candidate_expr} found. Assuming it is unsafe.",
                    )
                    # We have no info, err on the side of caution, it is considered unsafe
                    return False
                return res

        safeness_properties = self.getVarInfo()["Safeness"]
        outDependencies = self.getBackwardTrace()
        result = []
        for name, depNodeIDs in outDependencies.items():
            safeFact = safeness_properties.get(name, None)
            if safeFact == SafeClass.Unsafe:
                continue
            # The output shall be safe - check that direct dependencies are safe
            nameDependencyPaths = PathDivide.unpack_pathlist([outDependencies[name]])
            for p in nameDependencyPaths:
                source = self.behaviour_id_map.get(p[-1], None)
                if source is None:
                    # Source does not exist in mapping
                    continue
                if source.getBlockType() == "Port":
                    expr = source.getVarExpr()
                    if not exprIsConsideredSafe(safeness_properties, expr):
                        result.append(
                            f"ERROR: Unsafe data ('{expr}') flowing to safe output ('{name}')"
                        )
        return result

    def compute_delta(self, other_program):
        def find_variable_changes():
            vars_1 = set(self.varHeader.getAllVariables())
            vars_2 = set(other_program.varHeader.getAllVariables())
            variable_changes_old_to_new = {v.name: v for v in vars_1.difference(vars_2)}
            variable_changes_new_to_old = {v.name: v for v in vars_2.difference(vars_1)}

            _res = [
                (str(v), str(variable_changes_new_to_old.pop(n, "")))
                for n, v in variable_changes_old_to_new.items()
            ]
            # at this point, we have processed all common variables and those found in first set.
            # The remaining variables represent additions during the change
            _res.extend(("", str(v)) for v in variable_changes_new_to_old.values())

            return _res

        def find_changes_in_blocks():
            """

            Returns:

            """
            result = []
            blocks1 = set(self.behaviourElements)
            blocks2 = set(other_program.behaviourElements)
            differences = {b.getID() for b in blocks1.difference(blocks2)}
            for diff_id in differences:
                # if the ID exists in both programs, it's likely a change
                pot_block1 = self.behaviour_id_map.get(diff_id, None)
                pot_block2 = other_program.behaviour_id_map.get(diff_id, None)

                isABlockChange = pot_block1 is not None and pot_block2 is not None
                if isABlockChange:
                    if pot_block1.data.boundary_box != pot_block2.data.boundary_box:
                        result.append(
                            f"Block '{pot_block1.data.type}' moved. Re-run graphical checks"
                        )
                    if pot_block1.data.type != pot_block2.data.type:
                        result.append(
                            f"Block '{pot_block1.data.type}' changed to '{pot_block2.data.type}'. Re-run functional checks"
                        )

            return result

        if not isinstance(other_program, Program):
            raise ValueError(
                "Trying to compute delta between a program and a " + type(other_program)
            )
        if self == other_program:
            return []
        if self.progName != other_program.progName:
            # Slightly nuclear option for determining programs should not be compared. For now it works with intended
            # use case.
            return [
                (
                    "Program names are different. Delta analysis will not continue",
                    f"{self.progName} != {other_program.progName}",
                )
            ]
        res = []
        res.extend(find_variable_changes())
        res.extend(find_changes_in_blocks())

        return res

    def get_dependencies_names(self):
        backward_trace = {}
        for name, paths in self.getBackwardTrace().items():
            backward_trace[name] = [
                self.behaviour_id_map[e[-1]].expr.expr
                for e in PathDivide.unpack_pathlist([paths])
            ]
        return backward_trace

    def __str__(self):
        return f"Program: {self.progName}\nVariables:\n{self.varHeader}"

    def report_as_text(self):
        def gen_variable_string():
            _variables_part = f"Variables:"
            for vData in self.getVarDataColumns(
                    "name", "varType", "valueType", "initVal", "description"
            ):
                _variables_part = f"{_variables_part}\n{'(' + ', '.join(vData) + ')'}"
            return _variables_part

        num_inputs = self.getMetrics()["NrInputVariables"]
        metrics_part = f"Metrics:\nNum_Inputs: {num_inputs}\nNum_Outputs: {self.getMetrics()['NrOutputVariables']}"
        variables_part = gen_variable_string()
        rule_violations = self.get_rule_violation_report()
        return f"{rule_violations}\n{variables_part}\n{metrics_part}"

    def get_rule_violation_report(self):
        res = "Design Rule Report:"
        for rule_report in self.check_rules():
            [name, verdict, justification] = rule_report
            res = f"{res}\n{name:40}{verdict:4}: {justification}\n"
        return res

    def check_rules(self) -> List[List[str]]:
        metrics = self.getMetrics()

        def evaluate_rule(
                ruleName, defaultVerdict, defaultJustification, evaluate_func
        ):
            verdict = defaultVerdict
            justification = defaultJustification
            results = evaluate_func()
            if any(results):
                verdict = "Fail"
                justification = "\n".join(results)
            return [ruleName, verdict, justification]

        def evaluate_variable_limit_rule(metrics, varLimit):
            ruleName = "FBD.MetricRule.TooManyVariables"
            verdict = "Pass"
            justification = f"The number of variables ({metrics['NrOfVariables']}) does not exceed chosen limit of {varLimit}"
            if metrics["NrOfVariables"] > varLimit:
                verdict = "Fail"
                justification = f"number of variables ({metrics['NrOfVariables']}) exceeds chosen limit of {varLimit}"
            return [ruleName, verdict, justification]

        def evaluate_safeness_data_flow():
            ruleName = "FBD.DataFlow.SafenessProperty"
            verdict = "Pass"
            justification = (
                f"No unjustified conversion between safe and unsafe data detected."
            )
            return evaluate_rule(
                ruleName, verdict, justification, self.checkSafeDataFlow
            )

        def evaluate_var_group_cohesion_rules():
            ruleName = "FBD.Variables.GroupCohesion"
            verdict = "Pass"
            justification = (
                "Variables are properly sorted into inputs and outputs groups"
            )
            return evaluate_rule(
                ruleName,
                verdict,
                justification,
                self.varHeader.evaluate_cohesion_of_sheet,
            )

        def evaluate_var_group_structure_rules():
            ruleName = "FBD.Variables.GroupStructure"
            verdict = "Pass"
            justification = "The mandatory groups (Inputs and Outputs) exists. At least one input and output variable is defined"
            return evaluate_rule(
                ruleName,
                verdict,
                justification,
                self.varHeader.evaluate_structure_of_var_sheet,
            )

        def check_variable_naming_uniqueness(aProgram, max_length_to_check):
            def find_in_list_from_start_index(e, l, startI):
                for i in range(startI, len(l)):
                    if l[i] == e:
                        return i
                return None

            violations = []
            variable_names = [v.name for v in aProgram.varHeader.getAllVariables()]
            stripped_variable_names = list(map(lambda e: e[:max_length_to_check], variable_names))
            if unique(stripped_variable_names):
                return []
            else:
                non_unique_signals = set()
                for it, name in enumerate(stripped_variable_names):
                    found_name_index = find_in_list_from_start_index(name, stripped_variable_names, it + 1)
                    if found_name_index:
                        non_unique_signals.add(variable_names[it])
                        non_unique_signals.add(variable_names[found_name_index])
                return [sorted([name for name in non_unique_signals])]

        def evaluate_variable_uniqueness_rules():
            rulename = "FBD.Naming.Uniqueness"
            verdict = "Pass"
            justification = "The variable names are suitably unique to be told apart by compilers"
            return evaluate_rule(
                rulename,
                verdict,
                justification,
                functools.partial(check_variable_naming_uniqueness, self,
                                  30))

        result = []
        result.append(evaluate_variable_limit_rule(metrics, 40))
        result.append(evaluate_safeness_data_flow())
        result.append(evaluate_var_group_cohesion_rules())
        result.append(evaluate_var_group_structure_rules())
        result.append(evaluate_variable_uniqueness_rules())

        return result

    def transform_to_ST(self):
        def path_to_ST_expression(path):
            """

            Args:
                path: The path to generate expression for

            Returns:
                ST representation of the path
            """

            def consume_path_within_block(block, _path):
                """

                Args:
                    block: The related block
                    _path: The path to remove from

                Returns:
                    The path starting from the first element not connected to the block
                """
                blockID = block.getID()
                return dropWhile(
                    _path, lambda portID: self.ports[portID].blockID == blockID
                )

            potential_block = self.behaviour_id_map[self.ports[path[0]].blockID]
            if potential_block.getBlockType() == "FunctionBlock":
                # Recursive case
                _path = dropWhile(
                    path[1:],
                    lambda e: not (
                            "PathDivide" in str(e.__class__) or "Block" in str(e.__class__)
                    ),
                )
                if "PathDivide" in str(_path[0].__class__):
                    pathdivide_paths = _path[0].paths
                    # Recursive call for each path
                    args_in_ST_form = map(
                        lambda p: path_to_ST_expression(
                            consume_path_within_block(potential_block, p)
                        ),
                        pathdivide_paths,
                    )
                    arglist = ", ".join(args_in_ST_form)
                else:
                    arglist = path_to_ST_expression(_path)
                return f"{potential_block.data.type}({arglist})"
            else:
                return potential_block.getVarExpr()

        def outputs_to_ST_statements():
            out_dataflow = self.getBackwardTrace()
            if not out_dataflow:
                return ""
            result = ""
            for outVar, path in out_dataflow.items():
                result += "\t" + f"{outVar} := "
                # Remove output variable from path list
                _path = path[1:]
                result += f"{path_to_ST_expression(_path)};\n"

            return result

        varheader_transform_to_st = self.varHeader.transform_to_ST()
        outputs_to_st_statements = outputs_to_ST_statements()
        return f"""
            Function_Block {self.progName}
            {varheader_transform_to_st}{outputs_to_st_statements}
            End_Function_Block"""


def extract_from_program(target_program: Program, value: str):
    def extract_metric(metric_value):
        return target_program.getMetrics()[metric_value]

    def extract_interface(request_value):
        if "vargroupnames" == request_value:
            return [g.groupName for g in target_program.getVarGroups()]
        result = []
        vars = target_program.getVarInfo()
        if "inputvariables" in request_value:
            result.extend([v for v in vars["InputVariables"]])
        if "outputvariables" in request_value:
            result.extend([v for v in vars["OutputVariables"]])
        return result

    value_without_dunder = value.strip("__")
    metric_regex = regex.compile(r"^metric\[((.*?)\}$")
    metric_match = re.match(metric_regex, value_without_dunder)
    if metric_match is not None:
        return extract_metric(metric_match.group(1))
    else:
        return extract_interface(value_without_dunder)
