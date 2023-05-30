import logging

from AST.pou import Program
from Web_GUI import parser
from Web_GUI.parser.AST.ast_typing import VariableParamType
from antlr_generated.python.POUVisitor import POUVisitor
from antlr_generated.python.POUParser import POUParser


class MyPOUVisitor(POUVisitor):
    def visitSafe_program_POU(self, ctx: POUParser.Safe_program_POUContext):
        variableWorkSheet = self.visitVariableWorkSheet(ctx.varWS)

        # For now, we set the elements separately
        return Program(str(ctx.ID()), variableWorkSheet, [], {})

    # Visit a parse tree produced by POUParser#variableHeader.
    def visitVariableWorkSheet(self, ctx: POUParser.VariableWorkSheetContext):
        variableGroups = self.visitVarGroups(ctx.varGroups())
        return parser.AST.variables.VariableWorkSheet(variableGroups)

    # Visit a parse tree produced by POUParser#varGroups.
    def visitVarGroups(self, ctx: POUParser.VarGroupsContext):
        res = dict()
        for groupDef in ctx.groupDefs().children:
            _def = self.visitGroupDef(groupDef)
            res[_def.groupID] = _def
        for varDefGroup in ctx.varDefGroups().children:
            grpID, listOfVars = self.visitVarDefGroup(varDefGroup)
            res[grpID].varLines.extend(listOfVars)
        return res

    # Visit a parse tree produced by POUParser#groupDef.
    def visitGroupDef(self, ctx: POUParser.GroupDefContext):
        return parser.AST.variables.VariableGroup(str(ctx.groupName.text), int(str(ctx.groupID.text)), [])

    # Visit a parse tree produced by POUParser#vars.
    def visitVarDefGroup(self, ctx: POUParser.VarDefGroupContext):
        varList = []
        for varLine in ctx.varLine():
            _var = self.visitVarLine(varLine)
            _var.varType = self.visitVar_type(ctx.varType)
            varList.append(_var)
        return int(str(ctx.groupNr.text)), varList

    # Visit a parse tree produced by POUParser#varLine.
    def visitVarLine(self, ctx: POUParser.VarLineContext):
        dummy = VariableParamType.UNSET  # property is set for the whole group
        initVal = None if ctx.initVal is None else str(ctx.initVal.text)
        desc = (
            None
            if ctx.varDesc is None
            else str(ctx.varDesc.text).lstrip("(*").rstrip("*)").strip()
        )
        result = parser.AST.variables.VariableLine(
            ctx.varName.text,
            dummy,
            self.visitVal_Type(ctx.valueType),
            initVal,
            desc,
            int(str(ctx.lineNr.text)),
        )
        return result

    # Visit a parse tree produced by POUParser#val_Type.
    def visitVal_Type(self, ctx: POUParser.Val_TypeContext):
        result = parser.AST.ast_typing.strToValType(str(ctx.start.text))
        if result is None:
            logging.warning(f"Type{str(ctx.children[0])} could not be found in lookup")
        return result

    # Visit a parse tree produced by POUParser#var_type.
    def visitVar_type(self, ctx: POUParser.Var_typeContext):
        return parser.AST.ast_typing.strToVariableType(str(ctx.children[0]))

    # Visit a parse tree produced by POUParser#codeWorkSheet.
    def visitCodeWorkSheet(self, ctx: POUParser.CodeWorkSheetContext):
        # For now, we do not care about parsing the header,
        # instead jump over and continue to parse the actual code
        return None

    def printSafe_program_POU(self, ctx: POUParser.Safe_program_POUContext):
        return f"{ctx.ID()}"
