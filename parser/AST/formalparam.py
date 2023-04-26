from dataclasses import dataclass

from parser.AST.ast_typing import DataflowDir, VariableParamType
from parser.AST.connections import ConnectionPoint, flow_selector


@dataclass
class FormalParam:
    name: str
    connectionPoint: ConnectionPoint
    ID: int
    data: dict[str, str]

    def get_connections(self, direction=DataflowDir.Backward):
        result = []
        for c in self.connectionPoint.connections:
            result.append(flow_selector(c, direction))
        return self.ID, result


@dataclass
class ParamList:
    varType: VariableParamType
    list: list[FormalParam]
