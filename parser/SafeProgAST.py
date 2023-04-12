from dataclasses import dataclass
from enum import IntEnum
from typing import List, Tuple, Optional, Dict


class VariableType(IntEnum):
    UNSET = (0,)
    InternalVar = 1
    InputVar = 2
    OutputVar = 3
    InOutVar = 4


class ValType(IntEnum):
    BOOL = 1
    BYTE = 2
    WORD = 3
    DWORD = 4
    LWORD = 5
    SINT = 6
    INT = 7
    DINT = 8
    LINT = 9
    USINT = 10
    UINT = 11
    UDINT = 12
    ULINT = 13
    REAL = 14
    LREAL = 15
    TIME = 16
    DATE = 17
    DT = 18
    TOD = 19
    STRING = 20
    WSTRING = 21
    SAFEUINT = 22


@dataclass
class Expr:
    expr: str

@dataclass
class GUIPosition:
    isRelativePosition: bool
    x: int
    y: int

    def __str__(self):
        return f"{'relativePos' if self.isRelativePosition else 'absolutePos'}({self.x}, {self.y})"

def make_absolute_position(x,y):
    return GUIPosition(False, x, y)
def make_relative_position(x,y):
    return GUIPosition(True, x, y)
class ConnectionType(IntEnum):
    Input = 1
    Output = 2

    def __str__(self):
        return self.name

@dataclass
class ConnectionData:
    position = GUIPosition
    connectionIndex = Optional[int]

    def __init__(self, pos=None, connIndex=None):
        self.position = make_absolute_position(-1,-1) if not pos else pos
        self.connectionIndex = connIndex

    def __str__(self):
        return f"Conn - {self.position} - {self.connectionIndex}"

@dataclass
class Connection:
    connectionType: ConnectionType
    data: ConnectionData
    def __str__(self):
        return f"{self.connectionType} -> {self.data}"




@dataclass
class BlockData:
    localID: int
    type: str


@dataclass
class VarList:
    varType: VariableType
    list: list[str]


@dataclass
class VarBlock:
    data: BlockData
    outConnection: Connection
    expr: Expr


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
        for groupID, group in self.varGroups.items():
            result.extend(group.varLines)
        return result

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



        return res

    def __str__(self):
        return f"Program: {self.progName}\nVariables:\n{self.varHeader}"
