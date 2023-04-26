import logging
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Tuple, Optional, Dict

from parser.AST.ast_typing import VariableType, ValType
@dataclass
class Expr:
    expr: str

class IssueLevel(IntEnum):
    Note = 0
    Warning = 1
    Error = 2
@dataclass
class Report:
    issueLevel: IssueLevel
    message: str

class SafeClass(IntEnum):
    Unsafe = 0
    Safe = 1


@dataclass
class GUIPosition:
    isRelativePosition: bool
    x: int
    y: int

    def __str__(self):
        return f"{'relativePos' if self.isRelativePosition else 'absolutePos'}({self.x}, {self.y})"


def make_absolute_position(x, y):
    return GUIPosition(False, x, y)


def make_relative_position(x, y):
    return GUIPosition(True, x, y)


class ConnectionDirection(IntEnum):
    Input = 1
    Output = 2

    def __str__(self):
        return self.name


class DataflowDir(IntEnum):
    Forward = 1
    Backward = 2


@dataclass
class ConnectionData:
    position = GUIPosition
    connectionIndex = Optional[int]

    def __init__(self, pos=None, connIndex=None):
        self.position = make_absolute_position(-1, -1) if not pos else pos
        self.connectionIndex = connIndex

    def __str__(self):
        return f"Conn - {self.position} - {self.connectionIndex}"


@dataclass
class Connection:
    startPoint: ConnectionData
    endPoint: ConnectionData
    formalName: str


def flow_selector(conn: Connection, direction: DataflowDir):
    return (
        (conn.endPoint.connectionIndex, conn.startPoint.connectionIndex)
        if direction == DataflowDir.Backward
        else (conn.startPoint.connectionIndex, conn.endPoint.connectionIndex)
    )


@dataclass
class ConnectionPoint:
    connectionDir: ConnectionDirection
    connections: list[Connection]
    data: ConnectionData

    def __str__(self):
        return f"{self.connectionDir} -> {self.data}"


@dataclass
class BlockData:
    localID: int
    type: str


@dataclass
class FormalParam:
    name: str
    connectionPoint: ConnectionPoint
    ID: int
    data: dict[str, str]

    def get_connections(self, direction=DataflowDir.Backward):
        result = []
        for c in self.connectionPoint.connections:
            result.append(flow_selector(c, direction))
        return self.ID, result


@dataclass
class VarList:
    varType: VariableType
    list: list[FormalParam]


@dataclass
class VarBlock:
    data: BlockData
    outConnection: ConnectionPoint
    expr: Expr

    def getID(self):
        return self.data.localID

    def getVarExpr(self):
        return self.expr.expr


@dataclass
class FBD_Block:
    data: BlockData
    varLists: list[VarList]

    def getVarsGivenType(self, type):
        result = []
        _vars = [v for v in self.varLists if v.varType == type]
        for vL in _vars:
            result.extend([] if vL.list is None else vL.list)
        return result

    def getInputVars(self):
        return self.getVarsGivenType(VariableType.InputVar)

    def getOutputVars(self):
        return self.getVarsGivenType(VariableType.OutputVar)

    def getInOutVars(self):
        return self.getVarsGivenType(VariableType.InOutVar)

    def __str__(self):
        def stringify(lst):
            return ",".join(map(lambda e: str(e), lst))

        return (
            f"{self.data}\n"
            f"Inputs:\n{stringify(self.getInputVars())}\n"
            f"Outputs:\n{stringify(self.getOutputVars())}\n"
            f"In-Outs:\n{stringify(self.getInOutVars())}"
        )
    def getID(self):
        return self.data.localID


def strToVariableType(s):
    lookup = {
        "VAR": VariableType.InternalVar,
        "VAR_INPUT": VariableType.InputVar,
        "VAR_OUTPUT": VariableType.OutputVar,
    }
    return lookup.get(s, None)


def strToValType(s):
    lookup = {"INT": ValType.INT, "UINT": ValType.UINT, "SAFEUINT": ValType.SAFEUINT}
    return lookup.get(s, None)


@dataclass
class VariableLine:
    name: str
    varType: VariableType
    valueType: ValType
    initVal: str
    description: str
    lineNr: int

    def __str__(self):
        _init = "" if self.initVal is None else f" = {self.initVal}"
        _desc = "" if self.description is None else f"Description: '{self.description}'"
        return f"Var({self.valueType.name} {self.name}: {str(self.varType.name)}{_init}; {_desc})"

    def __init__(
        self, name, var_type, value_type, init_val=None, description=None, line_nr=None
    ):
        self.name = name
        self.varType = var_type
        self.valueType = value_type
        self.initVal = 0 if init_val is None else init_val
        self.description = description
        self.lineNr = line_nr


def test_can_create_variable_line_and_get_properties():
    v = VariableLine(
        "aVar", VariableType.InputVar, ValType.INT, 5, "This is a variable", 3
    )
    assert v.name == "aVar"
    assert v.varType == VariableType.InputVar
    assert v.valueType == ValType.INT
    assert v.initVal == 5
    assert v.description == "This is a variable"
    assert v.lineNr == 3


def test_some_variable_line_properties_are_optional():
    v = VariableLine("optVar", VariableType.InputVar, ValType.UINT)
    assert v.name == "optVar"
    assert v.varType == VariableType.InputVar
    assert v.valueType == ValType.UINT
    assert v.initVal == 0
    assert v.description is None
    assert v.lineNr is None


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

    def makeVarDict(self):
        allVars = self.getAllVariables()

    def getVarsByType(self, vType: VariableType):
        return list((filter(lambda e: e.varType == vType, self.getAllVariables())))

    def __str__(self):
        return "\n".join(
            [
                f"Group {groupNr}:\n{groupContent}"
                for groupNr, groupContent in self.varGroups.items()
            ]
        )


@dataclass()
class PathDivide:
    def __init__(self, paths: List[list[int]]):
        self.paths = paths

    def __eq__(self, other):
        signature__ = str(type(other))
        if "PathDivide" in str(signature__):
            return self.paths == other.paths
        return False

    def __ne__(self, other):
        return not (self.__eq__(other))

    def __str__(self):
        f'D({";".join([str(e) for e in self.paths])})'

    def __len__(self):
        return max(map(self.__len__, self.paths))

    @classmethod
    def unpack_pathlist(cls, pathList):
        """Take a list of paths and unpack all PathDivide objects into separate lists"""
        result = []
        for p in pathList:
            accList = []
            NoDividingPath = True
            for p_e in p:
                if isinstance(p_e, PathDivide):
                    NoDividingPath = False
                    _divPaths = PathDivide.unpack_pathlist(p_e.paths)
                    for _p in _divPaths:
                        _fin = [e for e in accList]  # Copy accumulated path until here
                        _fin.extend(_p)  # Extend with the flattened path
                        result.append(_fin)
                else:
                    accList.append(p_e)
            if len(accList) and NoDividingPath:
                result.append(accList)
        return result

    def flatten(self):
        return PathDivide.unpack_pathlist(self.paths)

def test_can_flatten_pathdivide_to_path_sequences():
    assert PathDivide.unpack_pathlist([[1, 2], [3, 4]]) == [[1, 2], [3, 4]]


def test_flatten_shall_handle_empty_paths_through_removal():
    assert PathDivide.unpack_pathlist([[1, 2], []]) == [[1, 2]]
    assert PathDivide.unpack_pathlist([[], [1, 2]]) == [[1, 2]]


def test_can_flatten_multiple_levels_of_pathdivides():
    div_prime = PathDivide([[3, 4], [5, 6]])
    actual_input = PathDivide([[1, 2, div_prime], [7, 8]])
    assert actual_input.flatten() == [[1, 2, 3, 4], [1, 2, 5, 6], [7, 8]]

    div_prime_prime = PathDivide([[10, 11, 12], [13, 14, 15]])
    div_prime_2 = PathDivide([[3, 4, div_prime], [5, div_prime_prime]])
    actual_input = PathDivide([[1, 2, div_prime_2], [7, 8], [99, 100]])
    assert actual_input.flatten() == [
        [1, 2, 3, 4, 3, 4],
        [1, 2, 3, 4, 5, 6],
        [1, 2, 5, 10, 11, 12],
        [1, 2, 5, 13, 14, 15],
        [7, 8],
        [99, 100],
    ]


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
            self.varHeader.getVarsByType(VariableType.OutputVar)
        )
        res["InputVariables"] = list_to_name_dict(
            self.varHeader.getVarsByType(VariableType.InputVar)
        )
        res["InternalVariables"] = list_to_name_dict(
            self.varHeader.getVarsByType(VariableType.InternalVar)
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
            self.varHeader.getVarsByType(VariableType.InputVar)
        )
        res["NrOutputVariables"] = len(
            self.varHeader.getVarsByType(VariableType.OutputVar)
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
