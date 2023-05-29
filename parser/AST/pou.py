import logging
from dataclasses import dataclass
from typing import List, Tuple, Dict

from parser.AST.ast_typing import VariableParamType, DataflowDirection, SafeClass
from parser.AST.blocks import VarBlock, FBD_Block
from parser.AST.connections import flow_selector
from parser.AST.path import PathDivide
from parser.AST.variables import VariableLine, VariableWorkSheet


@dataclass()
class Program:
    progName: str
    varHeader: VariableWorkSheet
    behaviourElements: List[FBD_Block]
    behaviour_id_map: Dict[int, FBD_Block]
    backward_flow: Dict[str, List[int]]
    forward_flow: Dict[str, List[int]]

    def __init__(self, name, varWorkSheet, behaviourElementList = None, behaviourIDMap = None):
        self.progName = name
        self.varHeader = varWorkSheet
        self.behaviourElements = [] if behaviourElementList is None else behaviourElementList
        self.behaviour_id_map = {} if behaviourIDMap is None else behaviourIDMap
        self.backward_flow = {}
        self.forward_flow = {}


    def post_parse_analysis(self):
        """
        Performs some necessary pre-steps for other analyses.
        Returns:
            No return value - will mutate the instance object
        """

        # Fill up the memoised elements
        self.getTrace(direction=DataflowDirection.Forward)

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
            res_dict = dict()
            for v in allVars:
                res_dict[v.name] = v
            return res_dict

        res = dict()
        res["OutputVariables"] = list_to_name_dict(
            self.varHeader.getVarsByType(VariableParamType.OutputVar)
        )
        res["InputVariables"] = list_to_name_dict(
            self.varHeader.getVarsByType(VariableParamType.InputVar)
        )
        res["InternalVariables"] = list_to_name_dict(
            self.varHeader.getVarsByType(VariableParamType.InternalVar)
        )
        res["Safeness"] = dict([(name_type[0], SafeClass.Safe if "SAFE" in name_type[1] else SafeClass.Unsafe)
                                for name_type in self.getVarDataColumns("name", "valueType")])
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

    def getBackwardTrace(self):
        """

        Returns: A backwards trace starting from all outputs.

        """
        def split_paths(paths: list[Tuple[int, List[Tuple[int, int]]]]):
            result = []
            for p in paths:
                flat_path = [p[0]]
                start, end = p[1][0]
                flat_path.append(start)
                if end is not None:
                    flat_path.append(end)
                result.append(flat_path)
            return PathDivide(result)

        def performTrace(start_blocks):
            result = dict()
            for b in start_blocks:
                b_Result = [b.data.localID]
                worklist = [
                    flow_selector(c, DataflowDirection.Backward) for c in
                    b.getFlow(DataflowDirection.Backward)
                ]
                while worklist:
                    start, end = worklist[0]
                    worklist = worklist[1:]
                    b_Result.append(start)
                    if end is None:
                        break
                    b_Result.append(end)
                    current_entity = self.behaviour_id_map.get(
                        end, self.behaviour_id_map[start]
                    )

                    def IsBlock(entity):
                        return isinstance(entity, FBD_Block)

                    if IsBlock(current_entity):
                        interface_vars_startIDs = [
                            fp.get_connections(DataflowDirection.Backward)
                            for fp in current_entity.getInputVars()
                        ]
                        if len(interface_vars_startIDs) > 1:
                            b_Result.append(split_paths(interface_vars_startIDs))
                        else:
                            b_Result.append(interface_vars_startIDs[0][0])
                            worklist.append(interface_vars_startIDs[0][1][0])
                result[b.getVarExpr()] = b_Result
            return result

        if {} != self.backward_flow:
            return self.backward_flow
        outport_blocks = [
            e for e in self.behaviourElements if isinstance(e, VarBlock) and e.data.type == "outVariable"
        ]
        result = performTrace(outport_blocks)
        # Memoize backward trace
        self.backward_flow = result

        return result

    def getTrace(self, direction=DataflowDirection.Backward):
        def indexOrNone(aList, elem):
            """

            Args:
                aList: enumerable to search through
                elem: element to search for

            Returns: Index of element elem in list aList. If elem cannot be found, returns None

            """
            for i in range(len(aList)):
                if aList[i] == elem:
                    return i
            return None

        def ComputeForwardFlowFromBack(back_flow):
            """

            Args:
                back_flow: The computed backwards flow

            Returns: From each inport, provides the dataflow paths to the outports

            """
            if {} != self.forward_flow:
                return self.forward_flow

            flattened_flow = [
                e for e in [PathDivide.unpack_pathlist([f]) for f in back_flow.values()]
            ]
            interface_blocks = [
                e for e in self.behaviourElements if isinstance(e, VarBlock)
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
                for (
                        outport_pathlist
                ) in flattened_flow:
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
        res["NrOfFuncBlocks"] = len(
            [
                e
                for e in self.behaviourElements
                if isinstance(e, FBD_Block) and "Variable" not in e.data.type
            ]
        )
        res["NrInputVariables"] = len(
            self.varHeader.getVarsByType(VariableParamType.InputVar)
        )
        res["NrOutputVariables"] = len(
            self.varHeader.getVarsByType(VariableParamType.OutputVar)
        )

        return res

    def checkSafeDataFlow(self):
        def exprIsConsideredSafe(safenessProperties, expr):
            if "#" in expr:
                # it is a constant
                return "SAFE" in expr
            else:
                res = safenessProperties.get(expr, None)
                if res is None:
                    # log issue
                    logging.log(level=logging.WARNING,
                                msg=f"No safety information for {expr} found. Assuming it is unsafe.")
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
                if isinstance(source, VarBlock):
                    expr = source.getVarExpr()
                    if not exprIsConsideredSafe(safeness_properties, expr):
                        result.append(f"ERROR: Unsafe data ('{expr}') flowing to safe output ('{name}')")
        return result

    def __str__(self):
        return f"Program: {self.progName}\nVariables:\n{self.varHeader}"
