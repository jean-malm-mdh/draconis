from dataclasses import dataclass
from position import GUIPosition, make_relative_position
@dataclass
class GraphicalData:
    position: GUIPosition
    size_x: int
    size_y: int


@dataclass
class FBDObjData:
    localID: int
    type: str
    graph_data: GraphicalData

    def __init__(self, _id, _type, graphData=None):
        self.localID = _id
        self.type = _type
        self.graph_data = GraphicalData(make_relative_position(-1, -1), 1, 1) if graphData is None else graphData

