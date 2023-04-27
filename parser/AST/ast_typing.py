from enum import IntEnum


class VariableParamType(IntEnum):
    UNSET = 0
    InternalVar = 1
    InputVar = 2
    OutputVar = 4
    InOutVar = 6

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

    # 1 << 7 = 128
    SAFEANALOG = 128
    SAFEBOOL = 129
    SAFEBYTE = 130
    SAFEDWORD = 131
    SAFEWORD = 132
    SAFEINT = 135
    SAFESINT = 134
    SAFEDINT = 136
    SAFEUSINT = 138
    SAFEUINT = 139
    SAFEUDINT = 140
    SAFETIME = 144

    #TODO: Figure out a way to provide/compute this properties
    #   ANY, ANY_DERIVED, ANY_ELEMENTARY, ANY_MAGNITUDE, ANY_NUM, ANY_REAL,
    #   ANY_INT, ANY_BIT, ANY_STRING, ANY_DATE;


    def __str__(self):
        return self.name

    def isSafeValueType(self):
        return self.value() >= 128


class DataflowDir(IntEnum):
    Forward = 1
    Backward = 2


class SafeClass(IntEnum):
    Unsafe = 0
    Safe = 1


def strToVariableType(s: str):
    """
    Conversion function from string to VariableParamType
    Args:
        s: The string version of the value as defined in
        The value should match the regex VAR(_INPUT|_OUTPUT)?

    Returns:
        The Enumerable type, or None if the parameter is not found.
    """
    lookup = {
        "VAR": VariableParamType.InternalVar,
        "VAR_INPUT": VariableParamType.InputVar,
        "VAR_OUTPUT": VariableParamType.OutputVar,
    }
    return lookup.get(s, None)


def strToValType(s: str):
    """
    Conversion function from string to Data Value Types
    Args:
        s: The string representation of values.

    Returns:
        The corresponding Enum, or None if the value is not found
    """
    return ValType.__dict__.get(s, None)
