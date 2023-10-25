from .point import Point
from .connections import ConnectionDirection
from typing import Set
from dataclasses import dataclass


@dataclass
class Port:
    portID: int
    rel_connection_direction: ConnectionDirection
    rel_position: Point
    blockID: int
    connections: Set[int]
