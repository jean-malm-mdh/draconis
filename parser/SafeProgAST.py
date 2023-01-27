from dataclasses import dataclass
from enum import IntEnum


class VariableType(IntEnum):
    UNSET = (-1,)
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
        return "\n".join([f"Group {groupNr}:\n{groupContent}" for groupNr, groupContent in self.varGroups.items()])


@dataclass(frozen=True)
class Program:
    progName: str
    varHeader: VariableWorkSheet

    def getMetrics(self):
        res = dict()
        res["NrOfVariables"] = len(self.varHeader.getAllVariables())

        return res

    def __str__(self):
        return f"Program: {self.progName}\nVariables:\n{self.varHeader}"
