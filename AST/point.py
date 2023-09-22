import dataclasses
import json
from dataclasses import dataclass


@dataclass(unsafe_hash=True)
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
        return json.dumps(dataclasses.asdict(self))

    @classmethod
    def fromJSON(cls, json_string):
        import json
        d = json.loads(json_string)
        return Point(d["x"], d["y"])
