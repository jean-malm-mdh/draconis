from enum import IntEnum


class VariableType(IntEnum):
    UNSET = (0,)
    InternalVar = 1
    InputVar = 2
    OutputVar = 3
    InOutVar = 4

    def __str__(self):
        return self.name


class ValType(IntEnum):
    BOOL = 1
    BYTE = 2
    WORD = 3
    DWORD = 4
    LWORD = 5
    SINT = 6
    INT = 7
    DINT = 8
    LINT = 9
    USINT = 10
    UINT = 11
    UDINT = 12
    ULINT = 13
    REAL = 14
    LREAL = 15
    TIME = 16
    DATE = 17
    DT = 18
    TOD = 19
    STRING = 20
    WSTRING = 21
    SAFEUINT = 22

    def __str__(self):
        return self.name

class DataflowDir(IntEnum):
    Forward = 1
    Backward = 2


class SafeClass(IntEnum):
    Unsafe = 0
    Safe = 1
