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


@dataclass
class ConnectionData:
    position = GUIPosition
    connectionIndex = Optional[int]

    def __init__(self, pos=None, connIndex=None):
        self.position = make_absolute_position(-1, -1) if not pos else pos
        self.connectionIndex = connIndex

    def __str__(self):
        return f"Conn - {self.position} - {self.connectionIndex}"


@dataclass
class Connection:
    startPoint: ConnectionData
    endPoint: ConnectionData
    formalName: str


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
