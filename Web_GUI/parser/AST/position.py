import dataclasses
import json
from dataclasses import dataclass


@dataclass
class GUIPosition:
    isRelativePosition: bool
    x: int
    y: int

    def __str__(self):
        return f"{'relativePos' if self.isRelativePosition else 'absolutePos'}({self.x}, {self.y})"

    def toJSON(self):
        return json.dumps(dataclasses.asdict(self))

    @classmethod
    def fromJSON(cls, json_string):
        json_string_booleanfixed = json_string.replace("True,", "true,").replace("False,", "false,")
        d = json.loads(json_string_booleanfixed)
        return GUIPosition(d["isRelativePosition"], d["x"], d["y"])


def make_absolute_position(x, y):
    return GUIPosition(False, x, y)


def make_relative_position(x, y):
    return GUIPosition(True, x, y)

def test_from_position_to_JSON_and_back():
    from random import Random
    r = Random()
    for i in range(1000):
        gui_p = GUIPosition(bool(r.randint(0, 1)), r.randint(-10000, 10000), r.randint(-10000, 10000))
        assert GUIPosition.fromJSON(gui_p.toJSON()) == gui_p
