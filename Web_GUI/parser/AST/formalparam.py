from dataclasses import dataclass

from Web_GUI.parser.AST.ast_typing import DataflowDirection, VariableParamType
from Web_GUI.parser.AST.connections import (
    ConnectionPoint,
    trace_connection_in_dataflow_direction,
)


@dataclass
class FormalParam:
    name: str
    connectionPoint: ConnectionPoint
    ID: int
    data: dict[str, str]

    def get_connections(self, direction=DataflowDirection.Backward):
        result = []
        for c in self.connectionPoint.connections:
            result.append(trace_connection_in_dataflow_direction(c, direction))
        return self.ID, result

    def getID(self):
        return self.ID


@dataclass
class ParamList:
    varType: VariableParamType
    list: list[FormalParam]
