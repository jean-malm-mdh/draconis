from SafeProgAST import *
from antlr_generated.python.XMLParserVisitor import XMLParserVisitor
from antlr_generated.python.XMLParser import XMLParser

import logging

from parser.AST.fbdobject_base import FBDObjData
from parser.AST.blocks import Expr, VarBlock, FBD_Block
from parser.AST.connections import ConnectionDirection, ConnectionData, Connection, ConnectionPoint
from parser.AST.formalparam import FormalParam, ParamList
from parser.AST.position import make_absolute_position, make_relative_position


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
        varBlocks = [e for e in blockElements if isinstance(e, ParamList)]
        inVars = [e for e in varBlocks if e.varType == VariableParamType.InputVar]
        inOutVars = [e for e in varBlocks if e.varType == VariableParamType.InOutVar]
        outVars = [e for e in varBlocks if e.varType == VariableParamType.OutputVar]
        result = FBD_Block(
            FBDObjData(int(blockParams["localId"]), blockParams["typeName"]),
            [inVars[0], inOutVars[0], outVars[0]],
        )
        self.local_id_map[int(blockParams["localId"])] = result
        return result

    def ppx_parse_VarBlock(self, outVarArgs, content, direction="in"):
        blockElements = [self.visitElement(e)[0] for e in content.element()]
        expr = [e for e in blockElements if isinstance(e, Expr)][0]
        connection_points = [e for e in blockElements if isinstance(e, ConnectionPoint)][0]
        localId = int(outVarArgs["localId"])
        blockData = FBDObjData(localId, direction + "Variable")
        self.local_id_map[localId] = VarBlock(
            blockData, connection_points, expr
        )
        return self.local_id_map[localId]

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
        def get_value_or_none(d: dict, v, f):
            return (f(d.get(v)) if d.get(v, None) else None)

        def handle_ppx_element(attrs, ctx, name):
            """Parse ppx: elements based on their tag names"""
            result = None
            if "block" == name:
                self.elements.append(self.ppx_parse_block(attrs, ctx.content()))
            elif "inVariable" == name:
                self.elements.append(self.ppx_parse_VarBlock(attrs, ctx.content(), "in"))
            elif "outVariable" == name:
                self.elements.append(self.ppx_parse_VarBlock(attrs, ctx.content(), "out"))
            elif "connectionPointIn" == name:
                return self.ppx_parse_ConnectionPoint(ctx.content(), ConnectionDirection.Input)
            elif "connectionPointOut" == name:
                return self.ppx_parse_ConnectionPoint(ctx.content(), ConnectionDirection.Output)
            elif "expression" == name:
                return self.ppx_parse_expression(ctx.content())
            elif "FBD" == name:
                # We ignore signal lines locations for now
                content = ctx.content()
                elements = [e for e in content.element()]
                for i in range(1, len(elements)):
                    self.visitElement(elements[i])
            elif "line" == name:
                return attrs
            elif "addData" == name:
                return self.parse_addData_node(ctx)
            elif "data" == name:
                def parse_node_content(e):
                    if isinstance(e, XMLParser.ElementContext):
                        return self.visitElement(e)
                    elif isinstance(e, XMLParser.ContentContext):
                        return [c for c in e.getChildren()]
                    else:
                        return None

                pre_filter = [parse_node_content(c) for c in ctx.getChildren()]
                result = list(filter(lambda e: e is not None, pre_filter))
            elif "connectedFormalparameter" == name:
                return get_value_or_none(attrs, "refLocalId", int)
            elif "fp" == name:
                return int(attrs["localId"])
            elif "relPosition" == name:
                return make_relative_position(
                    int(attrs.get("x", -1)), int(attrs.get("y", -1))
                )
            elif "position" == name:
                return make_absolute_position(
                    int(attrs.get("x", -1)), int(attrs.get("y", -1))
                )
            elif "connection" == name:
                _data = [c for c in ctx.getChildren(lambda e: isinstance(e, XMLParser.ContentContext))]
                if _data:
                    return self.ppx_parse_Connection(_data[0], attrs)
                else:
                    return self.ppx_parse_Connection(None, attrs)
            elif "inputVariables" == name:
                return ParamList(
                    VariableParamType.InputVar, self.ppx_parse_variables(ctx.content())
                )
            elif "outputVariables" == name:
                return ParamList(
                    VariableParamType.OutputVar, self.ppx_parse_variables(ctx.content())
                )
            elif "inOutVariables" == name:
                content = ctx.content()
                vars = (
                    None if content is None else self.ppx_parse_variables(ctx.content())
                )
                return ParamList(VariableParamType.InOutVar, vars)
            elif "variable" == name:
                return self.ppx_parse_formal_variable(attrs, ctx.content())
            else:
                logging.debug(str(ctx) + " is not parsed")
                print(str(ctx) + " is not parsed - tag name:" + name)
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

    def parse_addData_node(self, addDataNode: XMLParser.ElementContext):
        dataNodes = addDataNode.content().element()
        assert len(dataNodes) == 1
        dataElements = dataNodes[0].content().element()
        result = [self.visitElement(e) for e in dataElements]
        return result

    def ppx_parse_Connection(self, connData: XMLParser.ContentContext, attrs):
        """
        <connection refLocalId="16" formalParameter="ADD">
            <addData>
              <data name="redacted" handleUnknown="preserve">
                <connectedFormalparameter refLocalId="12" />
              </data>
            </addData>
            <position x="154" y="44" />
            <position x="144" y="44" />
      </connection>
        """
        """
          <connection refLocalId="6">
            <position x="120" y="48" />
            <position x="112" y="48" />
          </connection>
        """
        """        
        <connectionPointIn>
          <relPosition x="0" y="16" />
          <connection refLocalId="8" /> <--
        </connectionPointIn>
        """
        def hasNoExtraData():
            return connData is None or len(connData.element()) == 0

        if hasNoExtraData():
            return Connection(ConnectionData(),
                              ConnectionData(pos=None, connIndex=int(attrs["refLocalId"])),
                              formalName=attrs.get("formalParameter", None))

        elements = list(connData.element())

        def hasOnlyPositionData(elements: List[XMLParser.ElementContext]):
            for e in elements:
                if "position" not in e.blockTag.text:
                    return False
            return True

        startID = None
        if hasOnlyPositionData(elements):
            toPosition = self.visitElement(elements[0])
            fromPosition = self.visitElement(elements[1])
        else:
            addDataNode = elements[0]
            toPosition = self.visitElement(elements[1])
            fromPosition = self.visitElement(elements[2])
            parsedDataElements = self.parse_addData_node(addDataNode)
            startID, _, _ = parsedDataElements[0]
        startConnPoint = ConnectionData(fromPosition, startID)
        endConnPoint = ConnectionData(toPosition, int(attrs["refLocalId"]))
        return Connection(startPoint=startConnPoint, endPoint=endConnPoint, formalName=attrs.get("formalParameter", None))

    def ppx_parse_ConnectionPoint(self, param: XMLParser.ContentContext, conn_type):
        connectionData = ConnectionData()
        connections = []
        for c in param.getChildren(lambda e: isinstance(e, XMLParser.ElementContext)):
            res, name, _ = self.visitElement(c)
            if "position" in name.lower():
                connectionData.position = res
            if "connection" in name.lower():
                connections.append(res)

        return ConnectionPoint(conn_type, connections, connectionData)

    def ppx_parse_variables(self, variables_content: XMLParser.ContentContext):
        """Parse a list of variables"""

        ## TODO: After debugging is done, refactor to one-liner is possible
        result = []
        elements = variables_content.element()
        parsed_elements = [self.visitElement(e)[0] for e in elements]
        result.extend(parsed_elements)
        return result

    def ppx_parse_formal_variable(self, attrs, variable_content: XMLParser.ContentContext):
        elements = variable_content.element()
        assert len(elements) == 2
        parsed_element_results = [self.visitElement(e)[0] for e in elements]
        connPoint = parsed_element_results[0]
        fpData = parsed_element_results[1][0]
        assert "fp" == fpData[1]

        return FormalParam(name=attrs["formalParameter"], connectionPoint=connPoint, ID=fpData[0], data=fpData[2])
