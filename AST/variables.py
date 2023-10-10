import json
from dataclasses import dataclass
from random import Random

import pytest

from .ast_typing import ParameterType, ValueType


@dataclass
class VariableLine:
    name: str
    paramType: ParameterType
    valueType: ValueType
    initVal: str
    description: str
    isFeedback: bool

    def toJSON(self):
        return f"""{{ "name": "{self.name}", "paramType": "{self.paramType}", "valueType": "{self.valueType}", "initVal": "{self.initVal}", "description": "{self.description}", "isFeedback": "{'true' if self.isFeedback else 'false'}" }}"""

    @classmethod
    def fromJSON(cls, json_str):
        import json

        data = json.loads(json_str)

        variable_line = cls(
            name=data["name"],
            value_type=ValueType.fromString(data["valueType"]),
            var_type=ParameterType.fromString(data["paramType"]),
        )
        variable_line.initVal = data["initVal"]
        variable_line.description = data["description"]
        variable_line.isFeedback = data["isFeedback"] == "True"
        return variable_line

    def __str__(self):
        _init = "" if self.initVal is None else f" = {self.initVal}"
        _desc = "" if self.description is None else f"Description: '{self.description}'"
        return f"Var({self.valueType.name} {self.name}: {str(self.paramType.name)}{_init}; {_desc})"

    def __init__(
        self,
        name,
        var_type,
        value_type,
        init_val=None,
        description=None,
        isFeedback=False,
    ):
        self.name = name
        self.paramType = var_type
        self.valueType = value_type
        self.initVal = init_val or "UNINIT"
        self.description = description
        self.isFeedback = isFeedback

    def __hash__(self):
        return hash(self.name)

    def getName(self):
        return self.name


def test_can_create_variable_line_and_get_properties():
    v = VariableLine(
        "aVar", ParameterType.InputVar, ValueType.INT, "5", "This is a variable", isFeedback=True
    )
    assert v.name == "aVar"
    assert v.paramType == ParameterType.InputVar
    assert v.valueType == ValueType.INT
    assert v.initVal == "5"
    assert v.description == "This is a variable"
    assert v.isFeedback == True


def test_some_variable_line_properties_are_optional():
    v = VariableLine("optVar", ParameterType.InputVar, ValueType.UINT)
    assert v.name == "optVar"
    assert v.paramType == ParameterType.InputVar
    assert v.valueType == ValueType.UINT
    assert v.initVal == "UNINIT"
    assert v.description is None


@pytest.fixture(scope="session", autouse=True)
def rand_tc():
    rand = Random()
    rand.seed(1337)
    return rand


def test_from_variable_to_JSON_and_back():
    aVar = VariableLine(
        "aVar", ParameterType.InputVar, ValueType.INT, "5", "This is a variable"
    )
    actual = VariableLine.fromJSON(aVar.toJSON())
    assert actual == aVar


@dataclass
class VariableGroup:
    groupName: str
    varLines: list[VariableLine]

    def toJSON(self):
        varLines = ", ".join([v.toJSON() for v in self.varLines])
        json_result = f"""
        {{
            "groupName": "{self.groupName}",
            "variables": [{varLines}]
        }}
        """
        return json_result

    @classmethod
    def fromJSON(cls, vg):
        import json

        d = json.loads(vg)
        lines = [VariableLine.fromJSON(line_json) for line_json in d["variables"]]
        return VariableGroup(d["groupName"], lines)

    def getName(self):
        return self.groupName

    def isOutputGroup(self):
        return "output" in self.getName().lower()

    def isInputGroup(self):
        return "input" in self.getName().lower()

    def checkForCohesionIssues(self):
        result = []
        if self.isOutputGroup():
            for var in self.varLines:
                if var.paramType != ParameterType.OutputVar:
                    result.append(
                        f"Non-output detected in Output group: {var.getName()}"
                    )
        elif self.isInputGroup():
            for var in self.varLines:
                if var.paramType != ParameterType.InputVar:
                    result.append(f"Non-input detected in Input group: {var.getName()}")
        return result

    def __str__(self):
        variables = "\n".join(map(lambda l: str(l), self.varLines))
        return f"Group Name: '{self.groupName}'\n{variables}"


@dataclass
class VariableWorkSheet:
    varGroups: list[VariableGroup]

    def toJSON(self):
        groups_json_str = ",".join([g.toJSON() for g in self.varGroups])
        json_result = f"""[{groups_json_str}]"""
        return json_result

    @classmethod
    def fromJSON(cls, json_string):
        vgs = json.loads(json_string)
        return [VariableGroup.fromJSON(vg) for vg in vgs]

    def getAllVariables(self):
        result = []
        for group in self.varGroups:
            result.extend(group.varLines)
        return result

    def getFirstVariableByName(self, name):
        allVars = self.getAllVariables()
        for v in allVars:
            if name == v.name:
                return v
        return None

    def getVarsByType(self, vType: ParameterType):
        return [e for e in self.getAllVariables() if e.paramType == vType]

    def __str__(self):
        return "\n".join([str(vg) for vg in self.varGroups])

    def evaluate_cohesion_of_sheet(self):
        result = []
        for groupContent in self.varGroups:
            groupCheck = groupContent.checkForCohesionIssues()
            if groupCheck:
                result.extend(groupCheck)
        return result

    def evaluate_structure_of_var_sheet(self):
        result = []
        # Check if inputs and output groups actually exist
        inputFound, outputFound = False, False
        for group in self.varGroups:
            inputFound = inputFound or group.isInputGroup()
            outputFound = outputFound or group.isOutputGroup()
        if not self.getVarsByType(ParameterType.InputVar):
            result.append("No input variables defined.")
        if not inputFound:
            result.append("The Input group has not been defined.")
        if not self.getVarsByType(ParameterType.OutputVar):
            result.append("No output variables defined.")
        if not outputFound:
            result.append("The Output group has not been defined.")
        return result

    def transform_to_ST(self):
        def var_to_ST_declaration(variable: VariableLine):
            param_ST_string = "Var_Input" if variable.paramType == ParameterType.InputVar else "Var_Output"
            initstr = "" if not variable.initVal else f" := {variable.initVal}"
            return f"\t{param_ST_string} {variable.name} : {variable.valueType}{initstr}; (*{variable.description}*) End_Var"
        return "\n".join(map(var_to_ST_declaration, self.getAllVariables()))
