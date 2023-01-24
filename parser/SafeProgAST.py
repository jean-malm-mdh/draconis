from dataclasses import dataclass
from enum import IntEnum


class VariableType(IntEnum):
    InternalVar = (1,)
    InputVar = (2,)
    OutputVar = 3


class ValType(IntEnum):
    INT = (1,)
    UINT = (2,)
    SAFEUINT = 3


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


@dataclass
class VariableGroup:
    groupName: str
    groupID: int
    varLines: list[VariableLine]


@dataclass
class VariableWorkSheet:
    varGroups: dict[int, VariableGroup]


@dataclass(frozen=True)
class Program:
    progName: str
    varHeader: VariableWorkSheet
