import dataclasses
import random
from dataclasses import dataclass

import pytest

from .point import Point
from .rectangle import Rectangle
import json


@dataclass(unsafe_hash=True)
class FBDObjData:
    localID: int
    type: str
    boundary_box: Rectangle

    def __init__(self, _id, _type, graphData=None):
        self.localID = _id
        self.type = _type
        self.boundary_box = (
            Rectangle(Point(-1, -1), Point(-1, -1)) if graphData is None else graphData
        )

    def toJSON(self):
        return json.dumps(dataclasses.asdict(self))

    @classmethod
    def fromJSON(cls, json_string):
        data = json.loads(json_string)
        rectData = (
            str(data["boundary_box"])
            .replace("'", "€€€&&")
            .replace('"', "'")
            .replace("€€€&&", '"')
        )
        return FBDObjData(data["localID"], data["type"], Rectangle.fromJSON(rectData))


@pytest.fixture(scope="session", autouse=True)
def rand_tc():
    rand = random.Random()
    rand.seed(1337)
    return rand


TC_INT_BOUND = 10000


def test_PointToJSONAndBack(rand_tc):
    for i in range(1000):
        p = Point(
            rand_tc.randint(-TC_INT_BOUND, TC_INT_BOUND),
            rand_tc.randint(-TC_INT_BOUND, TC_INT_BOUND),
        )
        p_json = json.loads(p.toJSON())
        assert Point.fromJSON(p.toJSON()) == p


def test_RectToJSONAndBack(rand_tc):
    for i in range(1000):
        p_lefttop = Point(
            rand_tc.randint(-TC_INT_BOUND, TC_INT_BOUND),
            rand_tc.randint(-TC_INT_BOUND, TC_INT_BOUND),
        )
        p_rightbot = Point(
            rand_tc.randint(-TC_INT_BOUND, TC_INT_BOUND),
            rand_tc.randint(-TC_INT_BOUND, TC_INT_BOUND),
        )
        rect = Rectangle(p_lefttop, p_rightbot)
        assert Rectangle.fromJSON(rect.toJSON()) == rect


def test_objDataToJSONAndBack(rand_tc):
    for i in range(1000):
        rect = Rectangle(
            Point(
                rand_tc.randint(-TC_INT_BOUND, TC_INT_BOUND),
                rand_tc.randint(-TC_INT_BOUND, TC_INT_BOUND),
            ),
            Point(
                rand_tc.randint(-TC_INT_BOUND, TC_INT_BOUND),
                rand_tc.randint(-TC_INT_BOUND, TC_INT_BOUND),
            ),
        )
        obj = FBDObjData(rand_tc.randint(-TC_INT_BOUND, TC_INT_BOUND), "test", rect)
        res = json.loads(obj.toJSON())
        assert res["localID"] == obj.localID
        assert res["type"] == obj.type
        assert res["boundary_box"] == json.loads(obj.boundary_box.toJSON())
        assert FBDObjData.fromJSON(obj.toJSON()) == obj
