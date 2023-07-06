import json
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

from Web_GUI.parser.AST.ast_typing import DataflowDirection
from Web_GUI.parser.AST.position import GUIPosition, make_absolute_position


class ConnectionDirection(IntEnum):
    Input = 1
    Output = 2

    def __str__(self):
        return self.name

    @classmethod
    def FromString(cls, param):
        match param:
            case "Input":
                return ConnectionDirection.Input
            case "Output":
                return ConnectionDirection.Output
        raise ValueError(f"String {param} not matched for ConnectionDirection Conversion")


@dataclass
class ConnectionData:
    position = GUIPosition
    connectionIndex = Optional[int]

    def __init__(self, pos=None, connIndex=None):
        self.position = pos or make_absolute_position(-1, -1)
        if not isinstance(self.position, GUIPosition):
            raise ValueError(f"Not a valid position: {pos}")
        self.connectionIndex = connIndex

    def __str__(self):
        return f"Conn - {self.position} - {self.connectionIndex}"

    def toJSON(self):
        return f"""{{ "position": {self.position.toJSON()}, "connectionIndex": "{self.connectionIndex}" }}"""


@dataclass
class Connection:
    startPoint: ConnectionData
    endPoint: ConnectionData
    formalName: str

    def toJSON(self):
        return f'{{ "startPoint": {self.startPoint.toJSON()}, "endPoint": {self.endPoint.toJSON()}, "formalName": "{self.formalName}" }}'


def trace_connection_in_dataflow_direction(
    conn: Connection, direction: DataflowDirection
):
    result = (
        (conn.endPoint.connectionIndex, conn.startPoint.connectionIndex)
        if direction == DataflowDirection.Backward
        else (conn.startPoint.connectionIndex, conn.endPoint.connectionIndex)
    )
    return result


def trace_connection_in_dataflow_direction_list_version(
    conn: Connection, direction: DataflowDirection
):
    result = (
        [conn.endPoint.connectionIndex, conn.startPoint.connectionIndex]
        if direction == DataflowDirection.Backward
        else [conn.startPoint.connectionIndex, conn.endPoint.connectionIndex]
    )
    return result


@dataclass
class ConnectionPoint:
    connectionDir: ConnectionDirection
    connections: list[Connection]
    data: ConnectionData

    def __str__(self):
        return f"{self.connectionDir} -> {self.data}"

    def toJSON(self):
        connections_json = ", ".join([c.toJSON() for c in self.connections])
        return f'{{ "data": {self.data.toJSON()}, "connectionDir": "{self.connectionDir.name}", "connections": [{connections_json}] }}'

    @classmethod
    def fromJSON(cls, json_string):
        d = json.loads(json_string)
        return ConnectionPoint(connectionDir=ConnectionDirection.FromString(d["connectionDir"]))
