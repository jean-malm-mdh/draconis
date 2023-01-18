from SafeProgAST import *
from generated.POUVisitor import POUVisitor
from generated.POUParser import POUParser


class MyPOUVisitor(POUVisitor):
    def visitSafe_program_POU(self, ctx: POUParser.Safe_program_POUContext):
        variableHeader = ctx.variableHeader().accept()
        variableGroups = []
        return Program(ctx.ID(), variableGroups)

    # Visit a parse tree produced by POUParser#variableHeader.
    def visitVariableHeader(self, ctx: POUParser.VariableHeaderContext):
        variableGroups = ctx.groupDefs().accept()
        return VariableHeader(variableGroups)

    # Visit a parse tree produced by POUParser#groupDefs.
    def visitGroupDefs(self, ctx: POUParser.GroupDefsContext):
        res = dict()
        for groupDef in ctx.children:
            # groupDef : '{' 'GroupDefinition' '(' groupID=INT ',' '\'' groupName=ID '\'' ')' '}' ;
            _def = groupDef.accept()
            group = VariableGroup
            group.groupName = _def.groupName
            res[_def.groupID] = group
        return res

    # Visit a parse tree produced by POUParser#vars.
    def visitVars(self, ctx: POUParser.VarsContext):
        # vars : VAR_TYPE '{' 'Group' '(' groupNr=INT  ')' '}' varLine* 'END_VAR' ;
        varList = []
        for lines in ctx.children:
            varList.append(lines.accept())
        return int(str(ctx.groupNr())), varList

    # Visit a parse tree produced by POUParser#varLine.
    def visitVarLine(self, ctx: POUParser.VarLineContext):
        return self.visitChildren(ctx)

    def printSafe_program_POU(self, ctx: POUParser.Safe_program_POUContext):
        return f"{ctx.ID()}"
