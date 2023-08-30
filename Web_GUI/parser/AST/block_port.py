from Web_GUI import Point
from connections import (
    ConnectionPoint, ConnectionDirection
)
from typing import Set
from dataclasses import dataclass
from formalparam import FormalParam


@dataclass
class Port:
    portID: int
    rel_connection_direction: ConnectionDirection
    rel_position: Point
    blockID: int
    connections: Set[int]

