import random
from dataclasses import dataclass

import pytest

from position import GUIPosition, make_relative_position
import json


@dataclass
class Point:
    x: int
    y: int

    def __add__(self, other):
        if not isinstance(other, Point):
            raise ValueError("Not a Point")
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        if not isinstance(other, Point):
            raise ValueError("Not a Point")
        return Point(self.x - other.x, self.y - other.y)

    def getAsTuple(self):
        return self.x, self.y

    def toJSON(self):
        return f'{{"x": {self.x}, "y": {self.y} }}'

    @classmethod
    def fromJSON(cls, json_string):
        import json

        d = json.loads(json_string)
        return Point(d["x"], d["y"])


@dataclass
class Rectangle:
    top_left: Point
    bot_right: Point

    def getPosition(self):
        return self.top_left.x, self.top_left.y

    def getSize(self):
        return Point(
            abs(self.bot_right.x - self.top_left.x),
            abs(self.bot_right.y - self.top_left.y),
        )

    def getAsTuple(self):
        return self.top_left.x, self.top_left.y, self.bot_right.x, self.bot_right.y

    def toJSON(self):
        return f'{{ "top_left": {self.top_left.toJSON()}, "bot_right": {self.bot_right.toJSON()} }}'

    @classmethod
    def fromJSON(cls, json_string):
        d = json.loads(json_string)
        lt = Point.fromJSON(
            str(d["top_left"])
            .replace("'", "€€€&&")
            .replace('"', "'")
            .replace("€€€&&", '"')
        )
        rb = Point.fromJSON(
            str(d["bot_right"])
            .replace("'", "€€€&&")
            .replace('"', "'")
            .replace("€€€&&", '"')
        )
        return Rectangle(lt, rb)

    @classmethod
    def check_overlap(cls, rect1, rect2):
        if not isinstance(rect1, Rectangle) or not isinstance(rect2, Rectangle):
            raise ValueError("Not a rectangle")

        # If one rectangle is on left side of other
        if rect1.top_left.x > rect2.bot_right.x or rect2.top_left.x > rect1.bot_right.x:
            return None

        # If one rectangle is above other
        if rect1.bot_right.y < rect2.top_left.y or rect2.bot_right.y < rect1.top_left.y:
            return None

        overlap_top_left_x = max(rect1.top_left.x, rect2.top_left.x)
        overlap_bot_right_x = min(rect1.bot_right.x, rect2.bot_right.x)

        overlap_top_left_y = max(rect1.top_left.y, rect2.top_left.y)
        overlap_bot_right_y = min(rect1.bot_right.y, rect2.bot_right.y)
        return Rectangle(
            Point(overlap_top_left_x, overlap_top_left_y),
            Point(overlap_bot_right_x, overlap_bot_right_y),
        )


@dataclass
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
        rect_json = self.boundary_box.toJSON()
        return f'{{ "localID": {self.localID}, "type": "{self.type}", "boundary_box": {rect_json} }}'

    @classmethod
    def fromJSON(cls, json_string):
        data = json.loads(json_string)
        return FBDObjData(
            data["localID"], data["type"], Rectangle.fromJSON(data["boundary_box"])
        )


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
        assert p_json["x"] == p.x
        assert p_json["y"] == p.y
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
        r_json = json.loads(rect.toJSON())
        assert r_json["top_left"] == {"x": rect.top_left.x, "y": rect.top_left.y}
        assert r_json["bot_right"] == {"x": rect.bot_right.x, "y": rect.bot_right.y}
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
        assert Rectangle.fromJSON(rect.toJSON()) == rect
