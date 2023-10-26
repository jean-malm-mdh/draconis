import json
from dataclasses import dataclass
from .ast_typing import ParameterType, DataflowDirection
from .fbdobject_base import FBDObjData
from .point import Point
from .rectangle import Rectangle
from .connections import (
    ConnectionPoint,
    trace_connection_in_dataflow_direction,
    trace_connection_in_dataflow_direction_list_version,
    ConnectionDirection,
)
from typing import List, Dict
from .formalparam import ParamList
from .block_port import Port


@dataclass
class Expr:
    expr: str


@dataclass
class Block:
    data: FBDObjData
    ports: Dict[int, Port]

    def getBlockType(self):
        raise NotImplementedError("Implement in Child classes")

    def getBlockFamily(self):
        return self.data.type

    def getInPorts(self):
        return [
            p
            for p in self.ports.values()
            if p.rel_connection_direction == ConnectionDirection.Input
        ]

    def getOutPorts(self):
        return [
            p
            for p in self.ports.values()
            if p.rel_connection_direction == ConnectionDirection.Output
        ]

    def getID(self):
        return self.data.localID

    def __hash__(self):
        return hash(self.data)

    def __eq__(self, other):
        if not isinstance(other, Block):
            raise ValueError(
                "Checking equality between block and " + str(other.__class__)
            )
        return self.data == other.data

    def getFlow(self, data_flow_dir: DataflowDirection, which_port):
        raise NotImplementedError("Implement in Child classes")

    @classmethod
    def fromJSON(cls, json_string):
        raise NotImplementedError("Implement in Child classes")

    def getName(self):
        raise NotImplementedError("Implement in child classes")

    def getBoundingBox(self):
        return self.data.boundary_box


@dataclass
class VarBlock(Block):
    outConnection: ConnectionPoint
    expr: Expr

    def __hash__(self):
        return Block.__hash__(self) + hash(self.expr.expr)

    def __eq__(self, other):
        if not isinstance(other, Block):
            raise ValueError(
                "Checking equality between block and " + str(other.__class__)
            )
        return self.data == other.data

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

    def getVarExpr(self):
        return self.expr.expr

    def getFlow(self, data_flow_dir: DataflowDirection, _unused_=None):
        ID = self.getID()
        toPorts = (
            self.getInPorts() if self.data.type == "outVariable" else self.getOutPorts()
        )
        if (
                DataflowDirection.Forward == data_flow_dir
                and self.data.type == "outVariable"
        ):
            # By definition, outVariables do not have a forward flow inside the POU block
            return []
        if (
                DataflowDirection.Backward == data_flow_dir
                and self.data.type == "inVariable"
        ):
            # By definition, outVariables do not have a forward flow inside the POU block
            return []
        result = []
        for p in toPorts:
            for conn in p.connections:
                result.append((p.portID, conn))
        return [(ID, result)]

    def getBlockType(self):
        return "Port"

    @classmethod
    def fromJSON(cls, json_string):
        d = json.loads(json_string)
        vb = VarBlock(
            FBDObjData.fromJSON(d["data"]),
            outConnection=ConnectionPoint.fromJSON(d["outConnection"]),
            expr=d["expr"],
        )
        return vb

    def getName(self):
        block_direction = (
            "Input"
            if self.outConnection.connectionDir == ConnectionDirection.Output
            else "Output"
        )
        return f"{block_direction}_{self.getVarExpr()}"


def test_varBlockFromJSON_AndBack():
    vb = VarBlock(
        FBDObjData(14, "test", Rectangle(Point(42, 42), Point(57, 57))),
        expr=Expr("TEST_EXPR"),
        outConnection=ConnectionPoint(
            connectionDir=ConnectionDirection.Input, connections=[ConnectionPoint]
        ),
    )


@dataclass
class FBD_Block(Block):
    varLists: list[ParamList]

    def __hash__(self):
        return Block.__hash__(self) + sum(map(lambda vl: hash(vl), self.varLists))

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

    @classmethod
    def fromJSON(cls, json_string):
        d = json.loads(json_string)
        return FBD_Block(
            data=FBDObjData.fromJSON(d["data"]),
            varLists=[ParamList.FromJSON(p_json) for p_json in d["varLists"]],
        )

    def getVariablesOfGivenType(self, queriedType):
        result = []
        _vars = [v for v in self.varLists if v.varType == queriedType]
        for vL in _vars:
            result.extend([] if vL.list is None else vL.list)
        return result

    def getFlow(self, data_flow_dir: DataflowDirection, restrictToPortID=None):
        """

        Args:
            data_flow_dir: The direction the data shall be tracked over the block

        Returns: [(startportID, endportID, outsideConnID) | startID in portDir(inportDirection) and endID in portDir(outportDirection)]

        """

        def intra_block_tracing(fromPorts, toPorts):
            result = []
            _fromPorts = (
                [p for p in fromPorts if p.portID == restrictToPortID]
                if restrictToPortID
                else fromPorts
            )
            for fP in _fromPorts:
                tmpRes = []
                for tP in toPorts:
                    for conn in tP.connections:
                        tmpRes.append((tP.portID, conn))
                result.append((fP.portID, tmpRes))
            return result

        in_ports = self.getInPorts()
        out_ports = self.getOutPorts()
        result = []
        # Basic fully-connected calculation
        # Todo: Connect to outside
        if DataflowDirection.Forward == data_flow_dir:
            return intra_block_tracing(in_ports, out_ports)
        else:
            return intra_block_tracing(out_ports, in_ports)

    def getInputVars(self):
        return self.getVariablesOfGivenType(ParameterType.InputVar)

    def getOutputVars(self):
        return self.getVariablesOfGivenType(ParameterType.OutputVar)

    def getInOutVars(self):
        return self.getVariablesOfGivenType(ParameterType.InOutVar)

    def __str__(self):
        def stringify(lst):
            return ",".join(map(lambda e: str(e), lst))

        return (
            f"{self.data}\n"
            f"Inputs:\n{stringify(self.getInputVars())}\n"
            f"Outputs:\n{stringify(self.getOutputVars())}\n"
            f"In-Outs:\n{stringify(self.getInOutVars())}"
        )

    def getBlockType(self):
        return "FunctionBlock"

    def getName(self):
        return self.data.type
