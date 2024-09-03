import json
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

from .ast_typing import DataflowDirection
from utility_classes.position import GUIPosition, make_absolute_position

from .utilities import swap_in_string


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
        raise ValueError(
            f"String {param} not matched for ConnectionDirection Conversion"
        )


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
        import json

        return f"""{{ "position": {self.position.toJSON()}, "connectionIndex": "{json.dumps(self.connectionIndex)}" }}"""

    @classmethod
    def fromJSON(cls, json_string):
        import json

        json_bool_fixed = json_string.replace("True", "true").replace("False", "false")
        d = json.loads(json_bool_fixed)
        s = (
            swap_in_string(str(d["position"]), '"', "'")
            .replace("True", "true")
            .replace("False", "false")
        )
        pos = GUIPosition.fromJSON(s)
        connIndex = (
            int(d["connectionIndex"]) if d["connectionIndex"] != "null" else None
        )

        return ConnectionData(pos, connIndex)


def test_fromConnectionData_to_json_and_back():
    from random import Random

    r = Random()
    for i in range(1000):
        gui_p = GUIPosition(
            bool(r.randint(0, 1)), r.randint(-10000, 10000), r.randint(-10000, 10000)
        )
        ind = r.randint(-10, 100)
        connIndex = None if ind < 0 else ind
        cd = ConnectionData(gui_p, connIndex)
        assert ConnectionData.fromJSON(cd.toJSON()) == cd


@dataclass
class Connection:
    startPoint: ConnectionData
    endPoint: ConnectionData
    formalName: str

    def toJSON(self):
        return f'{{ "startPoint": {self.startPoint.toJSON()}, "endPoint": {self.endPoint.toJSON()}, "formalName": "{self.formalName}" }}'

    @classmethod
    def fromJSON(cls, con_json):
        import json

        d = json.loads(con_json)
        return Connection(
            startPoint=ConnectionData.fromJSON(
                swap_in_string(d["startPoint"], "'", '"')
            ),
            endPoint=ConnectionData.fromJSON(swap_in_string(d["endPoint"], "'", '"')),
            formalName=d["formalName"],
        )


def test_from_Connection_to_JSON_and_back():
    from random import Random

    r = Random()
    for i in range(1000):
        gui_p1 = GUIPosition(
            bool(r.randint(0, 1)), r.randint(-10000, 10000), r.randint(-10000, 10000)
        )
        gui_p2 = GUIPosition(
            bool(r.randint(0, 1)), r.randint(-10000, 10000), r.randint(-10000, 10000)
        )

        ind1 = r.randint(-10, 100)
        ind2 = r.randint(-10, 100)
        connIndex1 = None if ind1 < 0 else ind1
        connIndex2 = None if ind2 < 0 else ind2
        cd1 = ConnectionData(gui_p1, connIndex1)
        cd2 = ConnectionData(gui_p2, connIndex2)
        conn = Connection(cd1, cd2, "test")
        assert Connection.fromJSON(conn.toJSON()) == conn


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
        conns = [Connection.fromJSON(con_json) for con_json in d["connections"]]
        return ConnectionPoint(
            connectionDir=ConnectionDirection.FromString(d["connectionDir"]),
            connections=conns,
            data=ConnectionData.fromJSON(d["data"]),
        )
