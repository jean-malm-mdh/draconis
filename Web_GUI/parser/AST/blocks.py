from dataclasses import dataclass
import sys

sys.path.append("/Users/jmm01/Documents/SmartDelta/safeprogparser")
from Web_GUI.parser.AST.ast_typing import VariableParamType, DataflowDirection
from Web_GUI.parser.AST.fbdobject_base import FBDObjData
from Web_GUI.parser.AST.connections import (
    ConnectionPoint,
    trace_connection_in_dataflow_direction,
    trace_connection_in_dataflow_direction_list_version,
)
from Web_GUI.parser.AST.formalparam import ParamList


@dataclass
class Expr:
    expr: str


@dataclass
class VarBlock:
    data: FBDObjData
    outConnection: ConnectionPoint
    expr: Expr
    def toJSON(self):
        data_json = self.data.toJSON()
        conn_json = self.outConnection.toJSON()
        json_res = f"""
        {{
            "Type": "{self.getBlockType()}",
            "data": {data_json},
            "expr": "{self.getVarExpr()}",
            "outConnection": {conn_json}
        }}
        """
        return json_res

    def getID(self):
        return self.data.localID

    def getVarExpr(self):
        return self.expr.expr

    def getFlow(self, data_flow_dir: DataflowDirection):
        if DataflowDirection.Forward == data_flow_dir:
            return (
                []
                if self.data.type == "outVariable"
                else [
                    trace_connection_in_dataflow_direction_list_version(
                        c, data_flow_dir
                    )
                    for c in self.outConnection.connections
                ]
            )
        if DataflowDirection.Backward == data_flow_dir:
            return (
                []
                if self.data.type == "inVariable"
                else [
                    trace_connection_in_dataflow_direction_list_version(
                        c, data_flow_dir
                    )
                    for c in self.outConnection.connections
                ]
            )

    def getBlockType(self):
        return "Port"


@dataclass
class FBD_Block:
    data: FBDObjData
    varLists: list[ParamList]
    def toJSON(self):
        data_json = self.data.toJSON()
        param_list_json = ", ".join([plist.toJSON() for plist in self.varLists])
        json_res = f"""
        {{
            "Type": "{self.getBlockType()}",
            "data": {data_json},
            "varLists": [{param_list_json}]
        }}
        """
        return json_res

    def getVariablesOfGivenType(self, queriedType):
        result = []
        _vars = [v for v in self.varLists if v.varType == queriedType]
        for vL in _vars:
            result.extend([] if vL.list is None else vL.list)
        return result

    def getFlow(self, data_flow_dir: DataflowDirection):
        """

        Args:
            data_flow_dir: The direction the data shall be tracked over the block

        Returns: [(startportID, endportID, outsideConnID) | startID in portDir(inportDirection) and endID in portDir(outportDirection)]

        """
        in_params = self.getInputVars()
        out_params = self.getOutputVars()
        result = []
        # Basic fully-connected calculation
        # Todo: Connect to outside
        if DataflowDirection.Forward == data_flow_dir:
            for inP in in_params:
                _res = [
                    (oP.connectionPoint.connections[0], oP.getID()) for oP in out_params
                ]
                result.extend(
                    [
                        [
                            inP.getID(),
                            oPort,
                            trace_connection_in_dataflow_direction(conn, data_flow_dir)[
                                0
                            ],
                        ]
                        for conn, oPort in _res
                    ]
                )
        else:
            for inP in out_params:
                _res = [
                    (oP.connectionPoint.connections[0], oP.getID()) for oP in in_params
                ]
                result.extend(
                    [
                        [
                            inP.getID(),
                            oPort,
                            trace_connection_in_dataflow_direction(conn, data_flow_dir)[
                                0
                            ],
                        ]
                        for conn, oPort in _res
                    ]
                )
        return result

    def getInputVars(self):
        return self.getVariablesOfGivenType(VariableParamType.InputVar)

    def getOutputVars(self):
        return self.getVariablesOfGivenType(VariableParamType.OutputVar)

    def getInOutVars(self):
        return self.getVariablesOfGivenType(VariableParamType.InOutVar)

    def __str__(self):
        def stringify(lst):
            return ",".join(map(lambda e: str(e), lst))

        return (
            f"{self.data}\n"
            f"Inputs:\n{stringify(self.getInputVars())}\n"
            f"Outputs:\n{stringify(self.getOutputVars())}\n"
            f"In-Outs:\n{stringify(self.getInOutVars())}"
        )

    def getID(self):
        return self.data.localID

    def getBlockType(self):
        return "FunctionBlock"

