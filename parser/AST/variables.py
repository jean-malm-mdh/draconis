from dataclasses import dataclass

from parser.AST.ast_typing import VariableParamType, ValType


@dataclass
class VariableLine:
    name: str
    varType: VariableParamType
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

    def getName(self):
        return self.name


def test_can_create_variable_line_and_get_properties():
    v = VariableLine(
        "aVar", VariableParamType.InputVar, ValType.INT, 5, "This is a variable", 3
    )
    assert v.name == "aVar"
    assert v.varType == VariableParamType.InputVar
    assert v.valueType == ValType.INT
    assert v.initVal == 5
    assert v.description == "This is a variable"
    assert v.lineNr == 3


def test_some_variable_line_properties_are_optional():
    v = VariableLine("optVar", VariableParamType.InputVar, ValType.UINT)
    assert v.name == "optVar"
    assert v.varType == VariableParamType.InputVar
    assert v.valueType == ValType.UINT
    assert v.initVal == 0
    assert v.description is None
    assert v.lineNr is None


@dataclass
class VariableGroup:
    groupName: str
    groupID: int
    varLines: list[VariableLine]
    def getName(self):
        return self.groupName
    def getID(self):
        return self.groupID

    def checkForCohesionIssues(self):
        def isOutputGroup():
            return "Output" in self.getName()
        def isInputGroup():
            return "Input" in self.getName()
        result = []
        if isOutputGroup():
            for var in self.varLines:
                if var.varType != VariableParamType.OutputVar:
                    result.append(f"Non-output detected in Output group: {var.getName()}")
        elif isInputGroup():
            for var in self.varLines:
                if var.varType != VariableParamType.InputVar:
                    result.append(f"Non-input detected in Input group: {var.getName()}")
        return result

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

    def getVariableByName(self, name):
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
