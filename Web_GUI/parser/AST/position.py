from dataclasses import dataclass


@dataclass
class GUIPosition:
    isRelativePosition: bool
    x: int
    y: int

    def __str__(self):
        return f"{'relativePos' if self.isRelativePosition else 'absolutePos'}({self.x}, {self.y})"


def make_absolute_position(x, y):
    return GUIPosition(False, x, y)


def make_relative_position(x, y):
    return GUIPosition(True, x, y)
