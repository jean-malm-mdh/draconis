from enum import IntEnum
from dataclasses import dataclass

class ChangeType(IntEnum):
    DELETION = -1
    MODIFICATION = 0
    ADDITION = 1


@dataclass()
class Delta:
    def __init__(self, changeType, fromObject, toObject):
        self.type = changeType
        self.fromObject = fromObject
        self.toObject = toObject

    @classmethod
    def Create(cls, changeType, fromObject, toObject):
        # Enforce invariants
        # If a new element is added, it should have no ancestor
        if changeType == ChangeType.ADDITION:
            if fromObject is not None:
                return None
        # If an element is removed, it should not have a descendant
        elif changeType == ChangeType.DELETION:
            if toObject is not None:
                return None
        else:
            # At this point, there needs to exist a link between two objects
            # and their properties shall not be equal
            if fromObject is None or toObject is None or fromObject == toObject:
                return None
            # This only works if the arguments are of the same type
            if type(fromObject) != type(toObject):
                return None
        return Delta(changeType, fromObject, toObject)

    @classmethod
    def CreateAddition(cls, to_object):
        return cls.Create(ChangeType.ADDITION, None, to_object)

    @classmethod
    def CreateDeletion(cls, from_object):
        return cls.Create(ChangeType.DELETION, from_object, None)

    def summarize(self):
        if self.type == ChangeType.MODIFICATION:
            res = [
                f"The following properties have been modified for variable '{self.fromObject.getName()}'",
            ]
            from_field_value_pairs = dict((f, getattr(self.fromObject, f)) for f in vars(self.fromObject) if f[0] != '_' )
            to_field_value_pairs = dict((f, getattr(self.toObject, f)) for f in vars(self.toObject) if f[0] != '_' )
            for f, v1 in from_field_value_pairs.items():
                v2 = to_field_value_pairs.get(f, "FIELD_DOES_NOT_EXIST")
                if v2 == "FIELD_DOES_NOT_EXIST" or v1 != v2:
                    res.append(f"{f}: {v1} => {v2}")
            return res
        else:
            # Addition/Deletion handled similarly enough to parametrise
            src = self.toObject or self.fromObject
            return [
                f"{type(src).__name__} {str(src.getName())} was "
                f"{'added' if self.type == ChangeType.ADDITION else 'removed'}"
            ]