from SafeProgAST import *
from generated.POUVisitor import POUVisitor
from generated.POUParser import POUParser


class MyPOUVisitor(POUVisitor):
    def visitSafe_program_POU(self, ctx: POUParser.Safe_program_POUContext):
        variableWorkSheet = self.visitVariableWorkSheet(ctx.varWS)
        codeWorkSheet = self.visitCodeWorkSheet(ctx.codeWorkSheet())

        return Program(str(ctx.ID()), variableWorkSheet)

    # Visit a parse tree produced by POUParser#variableHeader.
    def visitVariableWorkSheet(self, ctx: POUParser.VariableWorkSheetContext):
        variableGroups = self.visitVarGroups(ctx.varGroups())
        return VariableWorkSheet(variableGroups)

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
        return VariableGroup(str(ctx.groupName.text), int(str(ctx.groupID.text)), [])

    # Visit a parse tree produced by POUParser#vars.
    def visitVarDefGroup(self, ctx: POUParser.VarDefGroupContext):
        varList = []
        for varLine in ctx.varLine():
            _var = self.visitVarLine(varLine)
            _var.varType = strToVariableType(ctx.varType)
            varList.append(_var)
        return int(str(ctx.groupNr.text)), varList

    # Visit a parse tree produced by POUParser#varLine.
    def visitVarLine(self, ctx: POUParser.VarLineContext):
        dummy = VariableType.InternalVar
        result = VariableLine(
            ctx.varName.text,
            dummy,
            strToValType(ctx.valueType),
            str(ctx.initVal),
            str(ctx.varDesc),
            int(str(ctx.lineNr.text)),
        )
        return result

    # Visit a parse tree produced by POUParser#codeWorkSheet.
    def visitCodeWorkSheet(self, ctx: POUParser.CodeWorkSheetContext):
        return self.visitChildren(ctx)

    def printSafe_program_POU(self, ctx: POUParser.Safe_program_POUContext):
        return f"{ctx.ID()}"
