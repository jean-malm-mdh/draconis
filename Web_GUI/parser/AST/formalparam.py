from dataclasses import dataclass

from Web_GUI.parser.AST.ast_typing import DataflowDirection, VariableParamType
from Web_GUI.parser.AST.connections import (
    ConnectionPoint,
    trace_connection_in_dataflow_direction,
)


@dataclass
class FormalParam:
    name: str
    connectionPoint: ConnectionPoint
    ID: int
    data: dict[str, str]

    def toJSON(self):
        import json

        data_json = json.dumps(self.data)
        return f'{{"name": "{self.name}", "connectionPoint": {self.connectionPoint.toJSON()}, "ID": {self.getID()}, "data": {data_json} }}'

    def get_connections(self, direction=DataflowDirection.Backward):
        result = []
        for c in self.connectionPoint.connections:
            result.append(trace_connection_in_dataflow_direction(c, direction))
        return self.ID, result

    def getID(self):
        return self.ID

    @classmethod
    def fromJSON(cls, pm_json):
        import json
        d = json.loads(pm_json)
        return FormalParam(d["name"], ConnectionPoint.fromJSON(d["connectionPoint"]), d["ID"], d["data"])


@dataclass
class ParamList:
    varType: VariableParamType
    list: list[FormalParam]

    def __init__(self, varType, list=None):
        self.varType = varType
        self.list = list or []

    def toJSON(self):
        paramlist_json = ", ".join(p.toJSON() for p in self.list)
        return f"""
        {{
            "varType": "{self.varType}",
            "list": [{paramlist_json}]
        }}
        """

    @classmethod
    def FromJSON(cls, p_json):
        import json
        d = json.loads(p_json)
        parList = [FormalParam.fromJSON(pm_json) for pm_json in d["list"]]
        return ParamList(varType=VariableParamType.fromString(d["varType"]), list=parList)
        pass
