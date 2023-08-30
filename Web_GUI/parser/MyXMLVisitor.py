from typing import List

import antlr4.Parser

from Web_GUI.parser.AST.comment_box import CommentBox
from antlr_generated.python.XMLParserVisitor import XMLParserVisitor
from antlr_generated.python.XMLParser import XMLParser

import logging

from Web_GUI.parser.AST.ast_typing import ParameterType
from Web_GUI.parser.AST.fbdobject_base import FBDObjData
from Web_GUI import Point, Rectangle
from Web_GUI.parser.AST.blocks import Expr, VarBlock, FBD_Block
from Web_GUI.parser.AST.connections import (
    ConnectionDirection,
    ConnectionData,
    Connection,
    ConnectionPoint,
)
from Web_GUI.parser.AST.formalparam import FormalParam, ParamList
from Web_GUI.parser.AST.position import make_absolute_position, make_relative_position


class MyXMLVisitor(XMLParserVisitor):
    def __init__(self):
        self.connections = []
        self.elements = []
        self.local_id_map = {}
        self.lines = []
        self.comments = []

    def ppx_parse_block(
        self, blockParams: dict[str, str], content: XMLParser.ContentContext
    ):
        elements = content.element()
        blockElements = [self.visitElement(e)[0] for e in elements]
        varBlocks = [e for e in blockElements if isinstance(e, ParamList)]
        inVars = [e for e in varBlocks if e.varType == ParameterType.InputVar]
        inOutVars = [e for e in varBlocks if e.varType == ParameterType.InOutVar]
        outVars = [e for e in varBlocks if e.varType == ParameterType.OutputVar]
        GUI_position_top_left = [
            e for e in blockElements if "GUIPosition" in str(e.__class__)
        ][0]
        position_top_left = Point(GUI_position_top_left.x, GUI_position_top_left.y)
        size = Point(int(blockParams["width"]), int(blockParams["height"]))
        bounding_box = Rectangle(position_top_left, position_top_left + size)
        ports = {}
        result = FBD_Block(
            FBDObjData(
                int(blockParams["localId"]), blockParams["typeName"], bounding_box
            ),
            ports,
            [inVars[0], inOutVars[0], outVars[0]],
        )
        self.local_id_map[int(blockParams["localId"])] = result
        return result

    def ppx_parse_VarBlock(self, outVarArgs, content, direction="in"):
        blockElements = [self.visitElement(e)[0] for e in content.element()]
        GUI_position_top_left = [
            e for e in blockElements if "GUIPosition" in str(e.__class__)
        ][0]
        expr = [e for e in blockElements if isinstance(e, Expr)][0]
        connection_points = [
            e for e in blockElements if isinstance(e, ConnectionPoint)
        ][0]
        localId = int(outVarArgs["localId"])
        height, width = int(outVarArgs["height"]), int(outVarArgs["width"])
        upper_left_point = Point(GUI_position_top_left.x, GUI_position_top_left.y)
        lower_right_point = upper_left_point + Point(width, height)
        boundingBox = Rectangle(upper_left_point, lower_right_point)
        blockData = FBDObjData(localId, direction + "Variable", boundingBox)
        ports = {}
        self.local_id_map[localId] = VarBlock(blockData, ports, connection_points, expr)
        return self.local_id_map[localId]

    def ppx_parse_expression(self, content):
        exprStr = self.visitChardata(content.chardata(0))
        assert (exprStr is not None) and (exprStr != "")
        return Expr(exprStr)

    def ppx_parse_comment_content(self, ctx):
        html_tag = ctx.content().element()[0]
        head_node = html_tag.content().element()[0]
        body_node = head_node.content().element()[1]
        p_node = body_node.content().element()[0]
        comment_content = p_node.content().getText()
        return comment_content

    # Visit a parse tree produced by XMLParser#document.
    def visitDocument(self, ctx: XMLParser.DocumentContext):
        # For now, we do not care about other parts of the document than the element node
        self.elements = []
        parsed_element, tagName, attributes = self.visitElement(ctx.element())
        return parsed_element

    # Visit a parse tree produced by XMLParser#element.
    def visitElement(self, ctx: XMLParser.ElementContext):
        def get_value_or_none(d: dict, v, f):
            return f(d.get(v)) if d.get(v, None) else None

        def handle_ppx_element(attrs, ctx, name):
            """Parse ppx: elements based on their tag names"""
            result = None
            if "block" == name:
                self.elements.append(self.ppx_parse_block(attrs, ctx.content()))
            elif "inVariable" == name:
                self.elements.append(
                    self.ppx_parse_VarBlock(attrs, ctx.content(), "in")
                )
            elif "outVariable" == name:
                self.elements.append(
                    self.ppx_parse_VarBlock(attrs, ctx.content(), "out")
                )
            elif "connectionPointIn" == name:
                return self.ppx_parse_ConnectionPoint(
                    ctx.content(), ConnectionDirection.Input
                )
            elif "connectionPointOut" == name:
                return self.ppx_parse_ConnectionPoint(
                    ctx.content(), ConnectionDirection.Output
                )
            elif "expression" == name:
                return self.ppx_parse_expression(ctx.content())
            elif "FBD" == name:
                content = ctx.content()
                elements = [e for e in content.element()]
                for e in elements:
                    self.visitElement(e)
            elif "line" == name:
                start_x, start_y, end_x, end_y = map(
                    int,
                    (attrs["beginX"], attrs["beginY"], attrs["endX"], attrs["endY"]),
                )
                self.lines.append((Point(start_x, start_y), Point(end_x, end_y)))
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
                _data = [
                    c
                    for c in ctx.getChildren(
                        lambda e: isinstance(e, XMLParser.ContentContext)
                    )
                ]
                if _data:
                    return self.ppx_parse_Connection(_data[0], attrs)
                else:
                    return self.ppx_parse_Connection(None, attrs)
            elif "inputVariables" == name:
                return ParamList(
                    ParameterType.InputVar, self.ppx_parse_variables(ctx.content())
                )
            elif "outputVariables" == name:
                return ParamList(
                    ParameterType.OutputVar, self.ppx_parse_variables(ctx.content())
                )
            elif "inOutVariables" == name:
                content = ctx.content()
                vars = None if content is None else self.ppx_parse_variables(content)
                return ParamList(ParameterType.InOutVar, vars)
            elif "variable" == name:
                return self.ppx_parse_formal_variable(attrs, ctx.content())
            elif "comment" == name:
                cont = ctx.content()
                elements_attrib_pairs = [self.visitElement(e) for e in cont.element()]
                position = elements_attrib_pairs[0][0]
                _comment_content = elements_attrib_pairs[1][0]
                bounding_box = Rectangle(
                    Point(position.x, position.y),
                    Point(
                        position.x + int(attrs["width"]),
                        position.y + int(attrs["height"]),
                    ),
                )
                comment = CommentBox(bounding_box, _comment_content)
                self.comments.append(comment)
            elif "content" == name:
                return self.ppx_parse_comment_content(ctx)

            else:
                logging.warning(str(ctx) + " is not parsed - tag name:" + name)
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
        content = dataNodes[0].elementContent
        # Some data-nodes do not have children
        if content is None:
            return []
        dataElements = content.element()
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
            return Connection(
                ConnectionData(),
                ConnectionData(pos=None, connIndex=int(attrs["refLocalId"])),
                formalName=attrs.get("formalParameter", None),
            )

        elements = list(connData.element())

        def hasOnlyPositionData(elements: List[XMLParser.ElementContext]):
            foundPositionData = False
            foundAdditionalData = False
            for e in elements:
                if "position" in e.blockTag.text:
                    foundPositionData = True
                if "addData" == e.blockTag.text:
                    foundAdditionalData = True
            return foundPositionData and not (foundAdditionalData)

        def hasOnlyAdditionalData(elements: List[XMLParser.ElementContext]):
            foundPositionData = False
            foundAdditionalData = False
            for e in elements:
                if "position" in e.blockTag.text:
                    foundPositionData = True
                if "addData" == e.blockTag.text:
                    foundAdditionalData = True
            return not (foundPositionData) and foundAdditionalData

        startID = None
        if hasOnlyPositionData(elements):
            toPosition = self.visitElement(elements[0])[0]
            fromPosition = self.visitElement(elements[1])[0]
        elif hasOnlyAdditionalData(elements):
            toPosition = make_absolute_position(-1, -1)
            fromPosition = make_absolute_position(-1, -1)
            addDataNode = elements[0]
            parsedDataElements = self.parse_addData_node(addDataNode)
            startID, _, _ = parsedDataElements[0]
        else:
            toPosition = self.visitElement(elements[1])[0]
            fromPosition = self.visitElement(elements[2])[0]
            addDataNode = elements[0]
            parsedDataElements = self.parse_addData_node(addDataNode)
            startID, _, _ = parsedDataElements[0]
        startConnPoint = ConnectionData(fromPosition, startID)
        endConnPoint = ConnectionData(toPosition, int(attrs["refLocalId"]))
        return Connection(
            startPoint=startConnPoint,
            endPoint=endConnPoint,
            formalName=attrs.get("formalParameter", None),
        )

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
        return [self.visitElement(e)[0] for e in variables_content.element()]

    def ppx_parse_formal_variable(
        self, attrs, variable_content: XMLParser.ContentContext
    ):
        elements = variable_content.element()
        assert len(elements) == 2
        parsed_element_results = [self.visitElement(e)[0] for e in elements]
        connPoint = parsed_element_results[0]
        fpData = parsed_element_results[1][0]
        assert "fp" == fpData[1]

        return FormalParam(
            name=attrs["formalParameter"],
            connectionPoint=connPoint,
            ID=fpData[0],
            data=fpData[2],
        )
