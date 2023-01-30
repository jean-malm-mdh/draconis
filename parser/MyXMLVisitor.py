from SafeProgAST import *
from generated.XMLParserVisitor import XMLParserVisitor
from generated.XMLParser import XMLParser

import logging



class MyXMLVisitor(XMLParserVisitor):

    def ppx_parse_block(self, blockParams: dict[str,str], content: XMLParser.ContentContext):
        blockElements = [self.visitElement(e) for e in content.element()]
        inVars = []
        inOutVars = []
        outVars = []
        return FBD_Block(BlockData(int(blockParams["localId"]),
                         blockParams["typeName"]), inVars, inOutVars, outVars)

    def ppx_parse_inVarBlock(self, inVarArgs, content):
        blockElements = [self.visitElement(e) for e in content.element()]
        expr = [e for e in blockElements if isinstance(e, Expr)][0]
        connectionOut = [e for e in blockElements if isinstance(e, ConnectionOut)][0]

        blockData = BlockData(int(inVarArgs["localId"]), "inVariable")
        return VarBlock(blockData, connectionOut, expr)

    def ppx_parse_expression(self, content):
        exprStr = self.visitChardata(content.chardata(0))
        assert (exprStr is not None) and (exprStr != "")
        return Expr(exprStr)

    # Visit a parse tree produced by XMLParser#document.
    def visitDocument(self, ctx: XMLParser.DocumentContext):
        # For now, we do not care about other parts of the document than the element node
        self.elements = []
        result = self.visitElement(ctx.element())
        return result

    # Visit a parse tree produced by XMLParser#element.
    def visitElement(self, ctx: XMLParser.ElementContext):
        # Consistency check if we are visiting an entire block
        assert ((ctx.blockCloseTag is None) or
                (str(ctx.blockTag.text) == str(ctx.blockCloseTag.text)))

        name = ctx.blockTag.text
        attrs = dict()
        for attr in ctx.attribute():
            _res = self.visitAttribute(attr)
            attrs[_res[0]] = _res[1]
        result = self.handle_ppx_element(attrs, ctx, name)

        return result

    def handle_ppx_element(self, attrs, ctx, name):
        result = None
        if "block" == name:
            self.elements.append(self.ppx_parse_block(attrs, ctx.content()))
        elif "inVariable" == name:
            self.elements.append(self.ppx_parse_inVarBlock(attrs, ctx.content()))
        elif "connectionPointOut" == name:
            return self.ppx_parse_outConnection(attrs, ctx.content())
        elif "expression" == name:
            return self.ppx_parse_expression(ctx.content())
        elif "FBD" == name:
            self.visitChildren(ctx)
        elif "position" == name:
            result = Position(int(attrs.get("x", -1)), attrs.get("y", -1))
        else:
            logging.debug(str(ctx) + " is not parsed")
        return result

    # Visit a parse tree produced by XMLParser#reference.
    def visitReference(self, ctx: XMLParser.ReferenceContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by XMLParser#attribute.
    def visitAttribute(self, ctx: XMLParser.AttributeContext):
        name = str(ctx.Name())
        value = str(ctx.STRING())[1:-1]
        return name, value

    # Visit a parse tree produced by XMLParser#chardata.
    def visitChardata(self, ctx: XMLParser.ChardataContext):
        return str(ctx.TEXT())

    # Visit a parse tree produced by XMLParser#misc.
    def visitMisc(self, ctx: XMLParser.MiscContext):
        return self.visitChildren(ctx)

    def ppx_parse_outConnection(self, attrs, param):
        return ConnectionOut("Dummy")
