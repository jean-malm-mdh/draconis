import json
from dataclasses import dataclass

from ast_typing import VariableParamType, ValType


@dataclass
class VariableLine:
    name: str
    paramType: VariableParamType
    valueType: ValType
    initVal: str
    description: str
    lineNr: int
    isFeedback: bool

    def toJSON(self):
        return f"""{{ "name": "{self.name}", "paramType": "{self.paramType}", "valueType": "{self.valueType}", "initVal": "{self.initVal}", "description": "{self.description}", "isFeedback": "{'true' if self.isFeedback else 'false'}" }}"""

    @classmethod
    def fromJSON(cls, json_str):
        import json
        data = json.loads(json_str)
        
        variable_line = cls(name=data["name"], value_type=data["valueType"], var_type=data["paramType"])
        variable_line.initVal = data["initVal"]
        variable_line.description = data["description"]
        variable_line.lineNr = data["lineNr"]
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
        line_nr=None,
        isFeedback=False,
    ):
        self.name = name
        self.paramType = var_type
        self.valueType = value_type
        self.initVal = "UNINIT" if init_val is None else init_val
        self.description = description
        self.lineNr = line_nr
        self.isFeedback = isFeedback

    def __eq__(self, other):
        if not isinstance(other, VariableLine):
            return False
        same_name = self.name == other.name
        same_feedback = self.isFeedback == other.isFeedback
        same_description = self.description == other.description
        same_varType = self.paramType == other.paramType
        same_initVal = self.initVal == other.initVal
        same_value_type = self.valueType == other.valueType
        return (
            same_name
            and same_feedback
            and same_description
            and same_varType
            and same_value_type
            and same_initVal
        )

    def __hash__(self):
        return hash(self.name)

    def getName(self):
        return self.name


def test_can_create_variable_line_and_get_properties():
    v = VariableLine(
        "aVar", VariableParamType.InputVar, ValType.INT, 5, "This is a variable", 3
    )
    assert v.name == "aVar"
    assert v.paramType == VariableParamType.InputVar
    assert v.valueType == ValType.INT
    assert v.initVal == 5
    assert v.description == "This is a variable"
    assert v.lineNr == 3


def test_some_variable_line_properties_are_optional():
    v = VariableLine("optVar", VariableParamType.InputVar, ValType.UINT)
    assert v.name == "optVar"
    assert v.paramType == VariableParamType.InputVar
    assert v.valueType == ValType.UINT
    assert v.initVal == 0
    assert v.description is None
    assert v.lineNr is None


@dataclass
class VariableGroup:
    groupName: str
    groupID: int
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

    def getName(self):
        return self.groupName

    def getID(self):
        return self.groupID

    def isOutputGroup(self):
        return "output" in self.getName().lower()

    def isInputGroup(self):
        return "input" in self.getName().lower()

    def checkForCohesionIssues(self):
        result = []
        if self.isOutputGroup():
            for var in self.varLines:
                if var.paramType != VariableParamType.OutputVar:
                    result.append(
                        f"Non-output detected in Output group: {var.getName()}"
                    )
        elif self.isInputGroup():
            for var in self.varLines:
                if var.paramType != VariableParamType.InputVar:
                    result.append(f"Non-input detected in Input group: {var.getName()}")
        return result

    def __str__(self):
        variables = "\n".join(map(lambda l: str(l), self.varLines))
        return f"Group Name: '{self.groupName}'\n{variables}"


@dataclass
class VariableWorkSheet:
    varGroups: list[VariableGroup]

    def toJSON(self, indent=4):
        groups_json_str = ",".join([g.toJSON() for g in self.varGroups])
        json_result = f"""[{groups_json_str}]"""
        return json_result
    def getAllVariables(self):
        result = []
        for group in self.varGroups:
            result.extend(group.varLines)
        return result

    def getVariableByName(self, name):
        allVars = self.getAllVariables()
        for v in allVars:
            if name == v.name:
                return v
        return None

    def getVarsByType(self, vType: VariableParamType):
        return list((filter(lambda e: e.paramType == vType, self.getAllVariables())))

    def __str__(self):
        return "\n".join(
            [
                f"{groupContent}"
                for groupContent in self.varGroups
            ]
        )

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
        if not self.getVarsByType(VariableParamType.InputVar):
            result.append("No input variables defined.")
        if not inputFound:
            result.append("The Input group has not been defined.")
        if not self.getVarsByType(VariableParamType.OutputVar):
            result.append("No output variables defined.")
        if not outputFound:
            result.append("The Output group has not been defined.")
        return result
