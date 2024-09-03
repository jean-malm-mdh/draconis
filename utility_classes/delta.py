from enum import IntEnum


class ChangeType(IntEnum):
    DELETION = -1
    MODIFICATION = 0
    ADDITION = 1


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
        return Delta(changeType, fromObject, toObject)

    @classmethod
    def CreateAddition(cls, to_object):
        return cls.Create(ChangeType.ADDITION, None, to_object)

    @classmethod
    def CreateDeletion(cls, from_object):
        return cls.Create(ChangeType.DELETION, from_object, None)
