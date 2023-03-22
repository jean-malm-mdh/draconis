from SafeProgAST import *
from generated.XMLParserVisitor import XMLParserVisitor
from generated.XMLParser import XMLParser

import logging


class MyXMLVisitor(XMLParserVisitor):
    def ppx_parse_block(
        self, blockParams: dict[str, str], content: XMLParser.ContentContext
    ):
        elements = content.element()
        blockElements = [self.visitElement(e) for e in elements]
        varBlocks = [e for e in blockElements if isinstance(e, VarList)]
        inVars = [e for e in varBlocks if e.varType == VariableType.InputVar]
        inOutVars = [e for e in varBlocks if e.varType == VariableType.InOutVar]
        outVars = [e for e in varBlocks if e.varType == VariableType.OutputVar]

        return FBD_Block(
            BlockData(int(blockParams["localId"]), blockParams["typeName"]),
            [inVars[0], inOutVars[0], outVars[0]],
        )

    def ppx_parse_inVarBlock(self, inVarArgs, content):
        blockElements = [self.visitElement(e) for e in content.element()]
        expr = [e for e in blockElements if isinstance(e, Expr)][0]
        connectionOut = [e for e in blockElements if isinstance(e, Connection)][0]

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
        assert (ctx.blockCloseTag is None) or (
            str(ctx.blockTag.text) == str(ctx.blockCloseTag.text)
        )
        if ctx.blockTag is None:
            return
        name = ctx.blockTag.text
        attrs = dict()
        for attr in ctx.attribute():
            _res = self.visitAttribute(attr)
            attrs[_res[0]] = _res[1]
        result = self.handle_ppx_element(attrs, ctx, name)

        return result

    def handle_ppx_element(self, attrs, ctx, name):
        """Parse ppx: elements based on their tag names"""
        result = None
        if "block" == name:
            self.elements.append(self.ppx_parse_block(attrs, ctx.content()))
        elif "inVariable" == name:
            self.elements.append(self.ppx_parse_inVarBlock(attrs, ctx.content()))
        elif "connectionPointOut" == name:
            return self.ppx_parse_Connection(
                attrs, ctx.content(), ConnectionType.Output
            )
        elif "connectionPointIn" == name:
            return self.ppx_parse_Connection(attrs, ctx.content(), ConnectionType.Input)
        elif "expression" == name:
            return self.ppx_parse_expression(ctx.content())
        elif "FBD" == name:
            self.visitChildren(ctx)
        elif "position" == name:
            result = Position(int(attrs.get("x", -1)), attrs.get("y", -1))
        elif "inputVariables" == name:
            return VarList(
                VariableType.InputVar, self.ppx_parse_variables(ctx.content())
            )
        elif "outputVariables" == name:
            return VarList(
                VariableType.OutputVar, self.ppx_parse_variables(ctx.content())
            )
        elif "inOutVariables" == name:
            content = ctx.content()
            vars = None if content is None else self.ppx_parse_variables(ctx.content())
            return VarList(VariableType.InOutVar, vars)
        elif "variable" == name:
            return self.ppx_parse_variable(attrs, ctx.content())
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

    def ppx_parse_Connection(self, attrs, param, conn_type):
        DUMMY = f"{str(attrs)} - {str(param)}"
        return Connection(conn_type, DUMMY)

    def ppx_parse_variables(self, variables_content: XMLParser.ContentContext):
        """Parse a list of variables"""
        result = []
        elements = variables_content.element()
        parsed_elements = [self.visitElement(e) for e in elements]
        result.extend(parsed_elements)
        return result

    def ppx_parse_variable(self, attrs, variable_content: XMLParser.ContentContext):
        elements = variable_content.element()
        parsed_elements = [self.visitElement(e) for e in elements]
        connectionIn = parsed_elements[0]
        additional_data = parsed_elements[1]
        return f"{attrs} - {parsed_elements}"
