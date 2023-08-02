from dataclasses import dataclass

from fbdobject_base import Rectangle

@dataclass()
class CommentBox:
    bounding_box: Rectangle
    content: str

    def toJSON(self):
        return f'{{ "bounding_box": {self.bounding_box.toJSON()}, "comment_content": "{self.content}" }}'

    @classmethod
    def fromJSON(cls, json_string):
        import json

        d = json.loads(json_string)
        cont = d["comment_content"]
        rect = Rectangle.fromJSON(d["bounding_box"])
        return CommentBox(rect, cont)


