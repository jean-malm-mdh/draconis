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
