# Generated from POU.g4 by ANTLR 4.11.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .POUParser import POUParser
else:
    from POUParser import POUParser

# This class defines a complete generic visitor for a parse tree produced by POUParser.

class POUVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by POUParser#safe_program_POU.
    def visitSafe_program_POU(self, ctx:POUParser.Safe_program_POUContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#pou_type.
    def visitPou_type(self, ctx:POUParser.Pou_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#codeWorkSheet.
    def visitCodeWorkSheet(self, ctx:POUParser.CodeWorkSheetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#variableWorkSheet.
    def visitVariableWorkSheet(self, ctx:POUParser.VariableWorkSheetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#varGroups.
    def visitVarGroups(self, ctx:POUParser.VarGroupsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#groupDefs.
    def visitGroupDefs(self, ctx:POUParser.GroupDefsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#groupDef.
    def visitGroupDef(self, ctx:POUParser.GroupDefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#varDefGroups.
    def visitVarDefGroups(self, ctx:POUParser.VarDefGroupsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#varDefGroup.
    def visitVarDefGroup(self, ctx:POUParser.VarDefGroupContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#valTypeRule.
    def visitValTypeRule(self, ctx:POUParser.ValTypeRuleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#feedbackRule.
    def visitFeedbackRule(self, ctx:POUParser.FeedbackRuleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#varLine.
    def visitVarLine(self, ctx:POUParser.VarLineContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#val_Type.
    def visitVal_Type(self, ctx:POUParser.Val_TypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#elementary_type.
    def visitElementary_type(self, ctx:POUParser.Elementary_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#safe_type.
    def visitSafe_type(self, ctx:POUParser.Safe_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#derived_type.
    def visitDerived_type(self, ctx:POUParser.Derived_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#generic_type.
    def visitGeneric_type(self, ctx:POUParser.Generic_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by POUParser#var_type.
    def visitVar_type(self, ctx:POUParser.Var_typeContext):
        return self.visitChildren(ctx)



del POUParser