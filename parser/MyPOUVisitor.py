from POUVisitor import *
import SafeProgAST


class MyPOUVisitor(POUVisitor):
    def visitSafe_program_POU(self, ctx:POUParser.Safe_program_POUContext):
        return SafeProgAST.Program(ctx.ID(), [])

    def printSafe_program_POU(self, ctx:POUParser.Safe_program_POUContext):
        return f"{ctx.ID()}"