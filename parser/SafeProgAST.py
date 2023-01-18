from dataclasses import dataclass
from enum import IntEnum


class VarType(IntEnum):
    INT = (1,)
    UINT = (2,)
    SAFEUINT = 3


@dataclass
class Variables:
    name: str
    type: VarType
    initVal: int


@dataclass
class VariableGroup:
    groupName: str
    varIDs: dict[int, list[Variables]]


@dataclass
class VariableHeader:
    varGroups: dict[int, VariableGroup]


@dataclass(frozen=True)
class Program:
    progName: str
    variables: list[Variables]
