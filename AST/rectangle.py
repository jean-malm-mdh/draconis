import dataclasses
import json
from dataclasses import dataclass

from .point import Point
from .utilities import swap_in_string


@dataclass(unsafe_hash=True)
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
        return json.dumps(dataclasses.asdict(self))
    @classmethod
    def fromJSON(cls, json_string):
        d = json.loads(json_string)
        string = swap_in_string(str(d["top_left"]), "'", '"')
        lt = Point.fromJSON(
            string)
        rb = Point.fromJSON(
            swap_in_string(str(d["bot_right"]), "'", '"')
        )
        return Rectangle(lt, rb)

    def move_by_delta(self, delta: Point):
        """
        in-memory update of a rectangle by moving its position by the delta
        Args:
            delta: A point

        Returns:
            None
        """
        self.top_left += delta
        self.bot_right += delta

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
