import antlr4.tree.Tree

from SafeProgAST import *
from antlr_generated.python.XMLParserVisitor import XMLParserVisitor
from antlr_generated.python.XMLParser import XMLParser

import logging


class MyXMLVisitor(XMLParserVisitor):
    def __init__(self):
        self.connections = []
        self.elements = []
        self.local_id_map = {}

    def ppx_parse_block(
        self, blockParams: dict[str, str], content: XMLParser.ContentContext
    ):
        elements = content.element()
        blockElements = [self.visitElement(e)[0] for e in elements]
        varBlocks = [e for e in blockElements if isinstance(e, VarList)]
        inVars = [e for e in varBlocks if e.varType == VariableType.InputVar]
        inOutVars = [e for e in varBlocks if e.varType == VariableType.InOutVar]
        outVars = [e for e in varBlocks if e.varType == VariableType.OutputVar]
        result = FBD_Block(
            BlockData(int(blockParams["localId"]), blockParams["typeName"]),
            [inVars[0], inOutVars[0], outVars[0]])
        self.local_id_map[int(blockParams["localId"])] = result
        return result

    def ppx_parse_inVarBlock(self, inVarArgs, content):
        blockElements = [self.visitElement(e)[0] for e in content.element()]
        expr = [e for e in blockElements if isinstance(e, Expr)][0]
        connectionOut = [e for e in blockElements if isinstance(e, Connection)][0]

        blockData = BlockData(int(inVarArgs["localId"]), "inVariable")
        self.local_id_map[int(inVarArgs["localId"])] = VarBlock(blockData, connectionOut, expr)
        return self.local_id_map[int(inVarArgs["localId"])]

    def ppx_parse_expression(self, content):
        exprStr = self.visitChardata(content.chardata(0))
        assert (exprStr is not None) and (exprStr != "")
        return Expr(exprStr)

    # Visit a parse tree produced by XMLParser#document.
    def visitDocument(self, ctx: XMLParser.DocumentContext):
        # For now, we do not care about other parts of the document than the element node
        self.elements = []
        parsed_element, tagName, attributes = self.visitElement(ctx.element())
        return parsed_element

    # Visit a parse tree produced by XMLParser#element.
    def visitElement(self, ctx: XMLParser.ElementContext):
        def handle_ppx_element(attrs, ctx, name):
            """Parse ppx: elements based on their tag names"""
            result = None
            if "block" == name:
                self.elements.append(self.ppx_parse_block(attrs, ctx.content()))
            elif "inVariable" == name:
                self.elements.append(self.ppx_parse_inVarBlock(attrs, ctx.content()))
            elif "connectionPointIn" == name:
                return self.ppx_parse_Connection(ctx.content(), ConnectionType.Input)
            elif "connectionPointOut" == name:
                return self.ppx_parse_Connection(
                    ctx.content(), ConnectionType.Output
                )
            elif "expression" == name:
                return self.ppx_parse_expression(ctx.content())
            elif "FBD" == name:
                self.visitChildren(ctx)
            elif "relPosition" == name:
                return make_relative_position(int(attrs.get("x", -1)), int(attrs.get("y", -1)))
            elif "position" == name:
                return make_absolute_position(int(attrs.get("x", -1)), int(attrs.get("y", -1)))
            elif "connection" == name:
                return int(attrs.get("refLocalId")) if attrs.get("refLocalId", None) else None
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
        # Consistency check if we are visiting an entire block
        assert (ctx.blockCloseTag is None) or (
            str(ctx.blockTag.text) == str(ctx.blockCloseTag.text)
        )
        if ctx.blockTag is None:
            return
        name = ctx.blockTag.text
        attrs = dict()
        for attr in ctx.attribute():
            attr_name, attr_value = self.visitAttribute(attr)
            attrs[attr_name] = attr_value
        result = handle_ppx_element(attrs, ctx, name)

        return result, name, attrs


    # Visit a parse tree produced by XMLParser#reference.
    def visitReference(self, ctx: XMLParser.ReferenceContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by XMLParser#attribute.
    def visitAttribute(self, ctx: XMLParser.AttributeContext):
        name = str(ctx.Name())
        value = str(ctx.STRING()).strip('"')
        return name, value

    # Visit a parse tree produced by XMLParser#chardata.
    def visitChardata(self, ctx: XMLParser.ChardataContext):
        return str(ctx.TEXT())

    # Visit a parse tree produced by XMLParser#misc.
    def visitMisc(self, ctx: XMLParser.MiscContext):
        return self.visitChildren(ctx)

    def ppx_parse_Connection(self, param: XMLParser.ContentContext, conn_type):
        connectionData = ConnectionData()
        for c in param.getChildren(lambda e: isinstance(e, XMLParser.ElementContext)):
            res, name, _ = self.visitElement(c)
            if "position" in name.lower():
                connectionData.position = res
            elif "connection" == name:
                connectionData.connectionIndex = res
        return Connection(conn_type, connectionData)

    def ppx_parse_variables(self, variables_content: XMLParser.ContentContext):
        """Parse a list of variables"""
        result = []
        elements = variables_content.element()
        parsed_elements = [self.visitElement(e)[0] for e in elements]
        result.extend(parsed_elements)
        return result

    def ppx_parse_variable(self, attrs, variable_content: XMLParser.ContentContext):
        elements = variable_content.element()
        parsed_elements = [self.visitElement(e)[0] for e in elements]
        connectionIn = parsed_elements[0]
        additional_data = parsed_elements[1]
        return f"{attrs} - {parsed_elements}"
