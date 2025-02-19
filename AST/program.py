import functools
import json
import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

from langdetect import DetectorFactory, detect, detect_langs

from checks.rule_utility_functions import unique
from utility_classes.point import Point
from .ast_typing import DataflowDirection, ParameterType, SafeClass
from .blocks import FBD_Block, VarBlock, Block
from .path import PathDivide
from .comment_box import CommentBox
from .utilities import indexOrNone
from .variables import VariableWorkSheet, VariableLine
from .block_port import Port
from utility_classes.delta import ChangeType, Delta


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

    @classmethod
    def VERSION(cls):
        MAJOR = 0
        MINOR = 4
        REVISION = 0
        return (MAJOR, MINOR, REVISION)

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

        def set_up_ports() -> None:
            """
            Sets up and connects all the ports mapping
            Returns:
                No return value - Modifies the instance object
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

        def rescale_graphical_details():
            # Lines are in their own coordinate space.
            # To ease work during rendering, they are moved once into the model's space
            self.lines = [(
                Point(line[0].x * 2, line[0].y * 2),
                (Point(line[1].x * 2, line[1].y * 2)),
            ) for line in self.lines]

        set_up_ports()
        rescale_graphical_details()

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

    def hasPotentialInternalState(self):
        return len(self.varHeader.getVarsByType(ParameterType.InternalVar)) > 0

    def performBackTraceFromBlock(self, bID, trace_from_portID=None):
        def appendIfNotInListEnd(l, elem):
            if not l or l[-1] != elem:
                l.append(elem)

        b = (
                self.behaviour_id_map.get(bID, None)
                or self.behaviour_id_map[self.ports[bID].blockID]
        )
        result = []
        # flow is a list of tuples of (startPort, [(endPorts, end_connection_ports)])
        flow = b.getFlowOverBlock(DataflowDirection.Backward, trace_from_portID)
        if not flow:
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

    def getDependencyPathsByName(self):
        backward_trace = dict()
        for name, paths in self.getBackwardTrace().items():
            backward_trace[name] = [
                self.behaviour_id_map[e[-1]].expr.expr
                for e in PathDivide.unpack_pathlist([paths])
            ]
        return backward_trace

    def num_of_elements(self):
        def get_all_connection_pairs():
            res = set()
            # Visits both start and end block
            # => visits both start and end port
            # => each connection will be added twice
            for aBlock in self.behaviourElements:
                for portID, aPort in aBlock.ports.items():
                    for conn in aPort.connections:
                        res = res.add((portID, conn))

            return res

        nr_of_variables = len(self.varHeader.getAllVariables())
        nr_of_blocks = len(self.behaviourElements)

        # Division to account for duplicated data
        nr_of_connections = len(get_all_connection_pairs()) // 2

        # Todo: Scale this based on block type complexity factor
        return nr_of_variables + nr_of_blocks + nr_of_connections

    def compute_variables_complexity(self):
        def map_variable_to_complexity_number(variable: VariableLine):
            return variable.valueType.valueTypeComplexity()

        return sum([map_variable_to_complexity_number(v) for v in self.varHeader.getAllVariables()])

    def getVarByName(self, varName: str) -> Optional[VariableLine]:
        return self.varHeader.getFirstVariableByName(varName)

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
        backwards_flow = self.getDependencyPathsByName()
        res["VariableTypeComplexity"] = self.compute_variables_complexity()
        res["IsPotentiallyImpure"] = self.hasPotentialInternalState()
        return res

    @classmethod
    def getMetricsExplanations(cls):
        res = dict()
        res["NrOfVariables"] = "The total number of variables in the program's variable sheet"
        res["NrOfFuncBlocks"] = "The total number of function blocks in the program's work sheet"
        res["NrInputVariables"] = "The total number of input variables"
        res["NrOutputVariables"] = "The total number of output variables"
        res["VariableTypeComplexity"] = "\n".join(
            ["The total complexity value given the variable types used, given the following rules:\n",
             "Boolean variables: 2",
             "Numeric variables: 5",
             "Subsystems: 10",
             "Safe variables: <complexity of variable>+1"])
        res["IsPotentiallyImpure"] = ("Whether the POU is potentially representing an impure function\n"
                                      "E.g., through having internal state")
        return res

    def checkSafeDataFlow(self):

        def block_is_safe_filter(aBlock: Block):
            return "EN_IN" in aBlock.getName()

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

        def safeness_is_filtered(pathIDs: List[int]):
            # going backwards from the source, if one of the IDs maps to a unsafe->safe conversion
            blocks_on_path = [self.behaviour_id_map.get(i) for i in pathIDs]
            return any([block_is_safe_filter(b) for b in blocks_on_path])

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
                        if safeness_is_filtered(p):
                            continue
                        result.append(
                            f"Unsafe data ('{expr}') flowing to safe output ('{name}')"
                        )
        return result

    def getLoopedBackBlocks(self):
        forward_flow = self.forward_flow

    def compute_deltas2(self, other_program):
        def find_variable_changes():
            vars_1 = set(self.varHeader.getAllVariables())
            vars_2 = set(other_program.varHeader.getAllVariables())
            variable_changes_old_to_new = {v.name: v for v in vars_1.difference(vars_2)}
            variable_changes_new_to_old = {v.name: v for v in vars_2.difference(vars_1)}

            _res = [
                Delta.Create(ChangeType.MODIFICATION, v, variable_changes_new_to_old.pop(n, None))
                for n, v in variable_changes_old_to_new.items()
            ]
            _res = [r for r in _res if r is not None]

            # at this point, we have processed all common variables and those found in first set.
            # The remaining variables represent additions during the change
            _res.extend([Delta.CreateAddition(v) for v in variable_changes_new_to_old.values()])
            _res.extend([Delta.CreateDeletion(v) for v in variable_changes_old_to_new.values() if v not in _res])

            return _res

        def find_changes_in_blocks():
            def identify_block_difference(_diff_id, _result):
                # if the ID exists in both programs, it's likely a change
                pot_block1 = self.behaviour_id_map.get(_diff_id, None)
                pot_block2 = other_program.behaviour_id_map.get(_diff_id, None)
                isABlockChange = pot_block1 is not None and pot_block2 is not None
                if isABlockChange:
                    if pot_block1.data.boundary_box != pot_block2.data.boundary_box:
                        _result.append(
                            f"Block '{pot_block1.data.type}' moved. Re-run graphical checks"
                        )
                    if pot_block1.data.type != pot_block2.data.type:
                        _result.append(
                            f"Block '{pot_block1.data.type}' changed to '{pot_block2.data.type}'."
                            f"Re-run functional checks"
                        )
                if pot_block1.getBlockType() == "Port" and pot_block2.getBlockType() == "Port":
                    assert isinstance(pot_block1, VarBlock)
                    assert isinstance(pot_block2, VarBlock)
                    expr1 = pot_block1.getVarExpr()
                    expr2 = pot_block2.getVarExpr()
                    if expr1 != expr2:

                        if "#" in expr1:
                            _result.append(
                                f"Expression in constant block {expr1} has changed to {expr2} - rerun IO tests")
                        else:
                            _result.append(
                                f"Expression in constant block {expr1} has changed to {expr2} - rerun IO tests")

        res = find_variable_changes()
        return res

    def compute_delta(self, other_program) -> List[str]:
        def find_variable_changes():
            vars_1 = set(self.varHeader.getAllVariables())
            vars_2 = set(other_program.varHeader.getAllVariables())
            variable_changes_old_to_new = {v.name: v for v in vars_1.difference(vars_2)}
            variable_changes_new_to_old = {v.name: v for v in vars_2.difference(vars_1)}

            _res = [
                f"\t{str(v)} ->\n\t{str(variable_changes_new_to_old.pop(n, ''))}\n"
                for n, v in variable_changes_old_to_new.items()
            ]
            if _res != []:
                res.insert(0, "The following variables have changed some property between the versions:")

            # at this point, we have processed all common variables and those found in first set.
            # The remaining variables represent additions during the change
            new_variables_added = [str(v) for v in variable_changes_new_to_old.values()]
            if len(new_variables_added) > 0:
                _res.append("The following variables have been added between the versions")
                _res.extend(new_variables_added)

            return _res

        def find_changes_in_blocks() -> List[str]:
            def identify_block_difference(_diff_id):
                _result = []
                # if the ID exists in both programs, it's likely a change
                pot_block1 = self.behaviour_id_map.get(_diff_id, None)
                pot_block2 = other_program.behaviour_id_map.get(_diff_id, None)
                isABlockChange = pot_block1 is not None and pot_block2 is not None
                if isABlockChange:
                    if pot_block1.data.boundary_box != pot_block2.data.boundary_box:
                        _result.append(
                            f"Block '{pot_block1.data.type}' moved. Re-run graphical checks"
                        )
                    if pot_block1.data.type != pot_block2.data.type:
                        _result.append(
                            f"Block '{pot_block1.data.type}' changed to '{pot_block2.data.type}'."
                            f"\nRe-run functional checks"
                        )
                    if pot_block1.getBlockType() == "Port" and pot_block2.getBlockType() == "Port":
                        assert isinstance(pot_block1, VarBlock)
                        assert isinstance(pot_block2, VarBlock)
                        expr1 = pot_block1.getVarExpr()
                        expr2 = pot_block2.getVarExpr()
                        if expr1 != expr2:
                            if "#" in expr1:
                                _result.append(
                                    f"Expression in constant block {expr1} has changed to {expr2} - rerun IO tests")
                            else:
                                _result.append(
                                    f"Expression in constant block {expr1} has changed to {expr2} - rerun IO tests")
                return _result

            """

            Returns:

            """
            result = []
            blocks1 = set(self.behaviourElements)
            blocks2 = set(other_program.behaviourElements)
            differences = {b.getID() for b in blocks1.difference(blocks2)}
            for diff_id in differences:
                result.extend(identify_block_difference(diff_id))

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
                "Program names are different. Delta analysis will not continue",
                f"{self.progName} != {other_program.progName}"
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

        def check_language_of_strings_is(strings_to_check, lang):
            DetectorFactory.seed = 0
            all_content = " ".join(strings_to_check)
            detected_lang = detect(all_content)  # Try to detect the language of the description
            if detected_lang != lang:  # If it's not same as lang
                return [i for i in range(strings_to_check) if detect(strings_to_check[i]) != lang]
            return None

        def evaluate_language_rule_variables():
            ruleName = "FBD.DesignRule.VariableDescriptionLang"
            verdict = "Pass"
            justification = f"The descriptions of variables are written in English"
            all_vars = self.varHeader.getAllVariables()
            test = check_language_of_strings_is([v.description for v in all_vars], lang="en")
            if test:  # if test is not none, and test is not empty list
                verdict = "Fail"
                justification = (f"The following variables have descriptions that are not in english:\n" +
                                 "\n".join([all_vars[i].description for i in test]))
            return [ruleName, verdict, justification]

        def evaluate_language_rule_comments():
            ruleName = "FBD.DesignRule.CommentLang"
            verdict = "Pass"
            justification = f"The comments are written in English"
            all_comments = self.comments
            test = check_language_of_strings_is([c.content for c in all_comments], lang="en")
            if test:  # if test is not none, and test is not empty list
                verdict = "Fail"
                justification = (f"The following variables have descriptions that are not in english:\n" +
                                 "\n".join([all_comments[i].content for i in test]))
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

        def check_useless_initializations(aProgram: Program):
            def expression_is_equal_to_zeroed(expr: str):
                return "FALSE" in expr or re.fullmatch(r"^([A-Z0-9]+#)?0$", expr)

            allVars = aProgram.varHeader.getAllVariables()
            name_initializer_list = [(v.getName(), v.initVal) for v in allVars if
                                     v.initVal is not None]
            zero_initialized_variables = [name for name, init in name_initializer_list if
                                          expression_is_equal_to_zeroed(init)]
            if zero_initialized_variables == []:
                return []
            result = ["The following variables are unnecessarily initialized to zero:\n"]
            result.append("\n\t".join(zero_initialized_variables))
            return result

        def evaluate_initialization_rule():
            ruleName = "FBD.Variables.Initialization"
            verdict = "Pass"
            justification = "Given that the memory always starts zeroed out, no useless initializations are done"

            return evaluate_rule(
                ruleName, verdict, justification, functools.partial(check_useless_initializations, self)
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
            justification = "The mandatory groups (Inputs and Outputs) exists.\nAt least one input and output variable is defined"
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
                result = []
                non_unique_signals = set()
                for it, name in enumerate(stripped_variable_names):
                    found_name_index = find_in_list_from_start_index(name, stripped_variable_names, it + 1)
                    if found_name_index:
                        non_unique_signals.add(variable_names[it])
                        non_unique_signals.add(variable_names[found_name_index])
                if len(non_unique_signals) > 0:
                    result = [f"Compilers supporting symbol table entry lengths of {max_length_to_check} "
                              f"or less would be unable to tell some of these names apart"]
                    result.extend([sorted([name for name in non_unique_signals])])
                return result

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
        result.append(evaluate_initialization_rule())
        result.append(evaluate_language_rule_variables())
        result.append(evaluate_language_rule_comments())

        return result


def extract_from_program(value: str, target_program: Program):
    def extract_metric(metric_value):
        return target_program.getMetrics()[metric_value]

    def extract_interface(request_value):
        vars = target_program.getVarInfo()
        return {
            "VarGroupNames": [g.groupName for g in target_program.getVarGroups()],
            "InputVariables": [v for v in vars["InputVariables"]],
            "OuputVariables": [v for v in vars["OutputVariables"]],
            "VariableNames": [v.getName() for v in target_program.varHeader.getAllVariables()]
        }.get(request_value, [])

    value_without_dunder = value.strip("__")
    metric_match = re.match(r"^metric\[(.*?)\]$", value_without_dunder)
    if metric_match is not None:
        return extract_metric(metric_match.group(1))
    else:
        return extract_interface(value_without_dunder)
