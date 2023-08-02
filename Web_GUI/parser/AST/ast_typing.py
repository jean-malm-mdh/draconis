from enum import IntEnum


class ParameterType(IntEnum):
    """
    Enumerable for different classes of parameters in the software.
    """
    UNSET = 0
    InternalVar = 1
    InputVar = 2
    OutputVar = 4
    InOutVar = 6

    def __str__(self):
        return self.name

    @classmethod
    def fromString(cls, aString):
        match aString:
            case "UNSET":
                return ParameterType.UNSET
            case "InternalVar":
                return ParameterType.InternalVar
            case "InputVar":
                return ParameterType.InputVar
            case "OutputVar":
                return ParameterType.OutputVar
            case "InOutVar":
                return ParameterType.InOutVar


class ValueType(IntEnum):
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

    CUSTOM_FBD = 1024

    # TODO: Figure out a way to provide/compute this properties
    #   ANY, ANY_DERIVED, ANY_ELEMENTARY, ANY_MAGNITUDE, ANY_NUM, ANY_REAL,
    #   ANY_INT, ANY_BIT, ANY_STRING, ANY_DATE;

    def __str__(self):
        return self.name

    def isSafeValueType(self):
        return "SAFE" in self.name

    @classmethod
    def fromString(cls, aString):
        match aString:
            case "BOOL":
                return ValueType.BOOL
            case "BYTE":
                return ValueType.BYTE
            case "WORD":
                return ValueType.WORD
            case "DWORD":
                return ValueType.DWORD
            case "LWORD":
                return ValueType.LWORD
            case "SINT":
                return ValueType.SINT
            case "INT":
                return ValueType.INT
            case "DINT":
                return ValueType.DINT
            case "LINT":
                return ValueType.LINT
            case "USINT":
                return ValueType.USINT
            case "UINT":
                return ValueType.UINT
            case "UDINT":
                return ValueType.UDINT
            case "ULINT":
                return ValueType.ULINT
            case "REAL":
                return ValueType.REAL
            case "LREAL":
                return ValueType.LREAL
            case "TIME":
                return ValueType.TIME
            case "DATE":
                return ValueType.DATE
            case "DT":
                return ValueType.DT
            case "TOD":
                return ValueType.TOD
            case "STRING":
                return ValueType.STRING
            case "WSTRING":
                return ValueType.WSTRING
            case "SAFEANALOG":
                return ValueType.SAFEANALOG
            case "SAFEBOOL":
                return ValueType.SAFEBOOL
            case "SAFEBYTE":
                return ValueType.SAFEBYTE
            case "SAFEDWORD":
                return ValueType.SAFEDWORD
            case "SAFEWORD":
                return ValueType.SAFEWORD
            case "SAFEINT":
                return ValueType.SAFEINT
            case "SAFESINT":
                return ValueType.SAFESINT
            case "SAFEDINT":
                return ValueType.SAFEDINT
            case "SAFEUSINT":
                return ValueType.SAFEUSINT
            case "SAFEUINT":
                return ValueType.SAFEUINT
            case "SAFEUDINT":
                return ValueType.SAFEUDINT
            case "SAFETIME":
                return ValueType.SAFETIME
            case "CUSTOM_FBD":
                return ValueType.CUSTOM_FBD


class DataflowDirection(IntEnum):
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
        "VAR": ParameterType.InternalVar,
        "VAR_INPUT": ParameterType.InputVar,
        "VAR_OUTPUT": ParameterType.OutputVar,
    }
    return lookup.get(s, None)


def strToValType(s: str):
    """
    Conversion function from string to Data Value Types
    Args:
        s: The string representation of values.

    Returns:
        The corresponding Enum. if the value is not recognized, assumes it is a custom FBD instance.
    """
    return ValueType.__dict__.get(s, ValueType.CUSTOM_FBD)
