import logging
import sys
import os

this_dirname = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if this_dirname not in sys.path:
    sys.path.insert(0, this_dirname)
from draconis_parser import Program, ParameterType, VariableWorkSheet, VariableLine, VariableGroup
from AST import strToValType, strToVariableType
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
        groups_no_IDs = list(variableGroups)
        return VariableWorkSheet(groups_no_IDs)

    # Visit a parse tree produced by POUParser#varGroups.
    def visitVarGroups(self, ctx: POUParser.VarGroupsContext):
        res = dict()
        for groupDef in ctx.groupDefs().children:
            groupID, _def = self.visitGroupDef(groupDef)
            res[groupID] = _def
        for varDefGroup in ctx.varDefGroups().children:
            grpID, listOfVars = self.visitVarDefGroup(varDefGroup)
            res[grpID].varLines.extend(listOfVars)
        return res.values()

    # Visit a parse tree produced by POUParser#groupDef.
    def visitGroupDef(self, ctx: POUParser.GroupDefContext):
        return int(str(ctx.groupID.text)), VariableGroup(
            str(ctx.groupName.text), []
        )

    # Visit a parse tree produced by POUParser#vars.
    def visitVarDefGroup(self, ctx: POUParser.VarDefGroupContext):
        varList = []
        for varLine in ctx.varLine():
            _var = self.visitVarLine(varLine)
            _var.paramType = self.visitVar_type(ctx.varType)
            varList.append(_var)
        return int(str(ctx.groupNr.text)), varList

    def visitValTypeRule(self, ctx: POUParser.ValTypeRuleContext):
        as_int = ctx.INT()
        if as_int is None:
            return ctx.getText()
        return str(as_int)

    def visitFeedbackRule(self, ctx: POUParser.FeedbackRuleContext):
        return ctx is not None

    # Visit a parse tree produced by POUParser#varLine.
    def visitVarLine(self, ctx: POUParser.VarLineContext):
        dummy = ParameterType.UNSET  # property is set for the whole group
        initVal = None if ctx.initVal is None else self.visitValTypeRule(ctx.initVal)
        desc = (
            None
            if ctx.varDesc is None
            else str(ctx.varDesc.text).lstrip("(*").rstrip("*)").strip()
        )
        isFeedback = self.visitFeedbackRule(ctx.isFeedback)
        return VariableLine(
            ctx.varName.text,
            dummy,
            self.visitVal_Type(ctx.valueType),
            initVal,
            desc,
            isFeedback,
        )

    # Visit a parse tree produced by POUParser#val_Type.
    def visitVal_Type(self, ctx: POUParser.Val_TypeContext):
        result = strToValType(str(ctx.start.text))
        if result is None:
            logging.warning(f"Type{str(ctx.children[0])} could not be found in lookup")
        return result

    # Visit a parse tree produced by POUParser#var_type.
    def visitVar_type(self, ctx: POUParser.Var_typeContext):
        return strToVariableType(str(ctx.children[0]))

    # Visit a parse tree produced by POUParser#codeWorkSheet.
    def visitCodeWorkSheet(self, ctx: POUParser.CodeWorkSheetContext):
        # For now, we do not care about parsing the header,
        # instead jump over and continue to parse the actual code
        return None

    def printSafe_program_POU(self, ctx: POUParser.Safe_program_POUContext):
        return f"{ctx.ID()}"
