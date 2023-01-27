from SafeProgAST import *
from generated.XMLParserVisitor import XMLParserVisitor
from generated.XMLParser import XMLParser


class MyXMLVisitor(XMLParserVisitor):
    # Visit a parse tree produced by XMLParser#document.
    def visitDocument(self, ctx: XMLParser.DocumentContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by XMLParser#prolog.
    def visitProlog(self, ctx: XMLParser.PrologContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by XMLParser#content.
    def visitContent(self, ctx: XMLParser.ContentContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by XMLParser#element.
    def visitElement(self, ctx: XMLParser.ElementContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by XMLParser#reference.
    def visitReference(self, ctx: XMLParser.ReferenceContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by XMLParser#attribute.
    def visitAttribute(self, ctx: XMLParser.AttributeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by XMLParser#chardata.
    def visitChardata(self, ctx: XMLParser.ChardataContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by XMLParser#misc.
    def visitMisc(self, ctx: XMLParser.MiscContext):
        return self.visitChildren(ctx)
