from dataclasses import dataclass

from parser.AST.ast_typing import VariableParamType
from parser.AST.fbdobject_base import FBDObjData
from parser.AST.connections import ConnectionPoint
from parser.AST.formalparam import ParamList


@dataclass
class Expr:
    expr: str


@dataclass
class VarBlock:
    data: FBDObjData
    outConnection: ConnectionPoint
    expr: Expr

    def getID(self):
        return self.data.localID

    def getVarExpr(self):
        return self.expr.expr


@dataclass
class FBD_Block:
    data: FBDObjData
    varLists: list[ParamList]

    def getVariablesOfGivenType(self, queriedType):
        result = []
        _vars = [v for v in self.varLists if v.varType == queriedType]
        for vL in _vars:
            result.extend([] if vL.list is None else vL.list)
        return result

    def getInputVars(self):
        return self.getVariablesOfGivenType(VariableParamType.InputVar)

    def getOutputVars(self):
        return self.getVariablesOfGivenType(VariableParamType.OutputVar)

    def getInOutVars(self):
        return self.getVariablesOfGivenType(VariableParamType.InOutVar)

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
