import logging
from dataclasses import dataclass
from typing import List, Tuple, Dict

from parser.AST.ast_typing import VariableParamType, DataflowDir, SafeClass
from parser.AST.blocks import VarBlock, FBD_Block
from parser.AST.connections import flow_selector
from parser.AST.path import PathDivide
from parser.AST.variables import VariableLine


@dataclass
class VariableGroup:
    groupName: str
    groupID: int
    varLines: list[VariableLine]

    def __str__(self):
        variables = "\n".join(map(lambda l: str(l), self.varLines))
        return f"Group Name: '{self.groupName}'\n{variables}"


@dataclass
class VariableWorkSheet:
    varGroups: dict[int, VariableGroup]

    def getAllVariables(self):
        result = []
        for _, group in self.varGroups.items():
            result.extend(group.varLines)
        return result

    def getVarByName(self, name):
        allVars = self.getAllVariables()
        for v in allVars:
            if name == v.name:
                return v
        return None

    def getVarsByType(self, vType: VariableParamType):
        return list((filter(lambda e: e.varType == vType, self.getAllVariables())))

    def __str__(self):
        return "\n".join(
            [
                f"Group {groupNr}:\n{groupContent}"
                for groupNr, groupContent in self.varGroups.items()
            ]
        )


@dataclass()
class Program:
    progName: str
    varHeader: VariableWorkSheet
    behaviourElements: List[FBD_Block]
    behaviour_id_map: Dict[int, FBD_Block]

    def getVarInfo(self):
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
        def getFieldContent(fieldList, element):
            theVars = vars(element)
            return [str(theVars.get(k, None)) for k in fieldList]

        _fields = (
            VariableLine.__dict__["__annotations__"].keys() if len(args) == 0 else args
        )
        return [getFieldContent(_fields, e) for e in self.varHeader.getAllVariables()]

    def getBackwardTrace(self):
        interface_blocks = [
            e for e in self.behaviourElements if isinstance(e, VarBlock)
        ]
        start_blocks = [b for b in interface_blocks if b.data.type == "outVariable"]
        result = dict()

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

        for b in start_blocks:
            b_Result = [b.data.localID]
            worklist = [
                flow_selector(c, DataflowDir.Backward)
                for c in b.outConnection.connections
            ]
            while worklist:
                start, end = worklist[0]
                if end is None:
                    break
                b_Result.append(start)
                b_Result.append(end)
                current_entity = self.behaviour_id_map.get(
                    end, self.behaviour_id_map[start]
                )

                def IsBlockWithMultipleInputs(entity):
                    return (
                            isinstance(entity, FBD_Block) and len(entity.getInputVars()) > 1
                    )

                if IsBlockWithMultipleInputs(current_entity):
                    interface_vars_startIDs = [
                        fp.get_connections(DataflowDir.Backward)
                        for fp in current_entity.getInputVars()
                    ]
                    b_Result.append(split_paths(interface_vars_startIDs))
                    break
            result[b.getVarExpr()] = b_Result
        return result

    def getTrace(self, direction=DataflowDir.Backward):
        def indexOrNone(l, e):
            """Returns index of element e in list l. If e cannot be found, returns None"""
            for i in range(len(l)):
                if l[i] == e:
                    return i
            return None

        def ComputeForwardFlowFromBack(back_flow):
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
            return result

        if direction == DataflowDir.Backward:
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

    def check(self):
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
