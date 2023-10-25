from dataclasses import dataclass
from AST import Program


@dataclass
class Check:
    check_family: str
    name: str
    long_name: str
    check_config: dict[str, str]

    def __init__(self, check_family, name, long_name, check_config_str):
        self.check_family = check_family
        self.name = name
        self.long_name = long_name
        self.check_config = self.parse_config(check_config_str)

    @property
    def FullName(self):
        return f"{self.check_family}.{self.name}"

    @property
    def HumanReadableName(self):
        return self.long_name

    def check(self, program: Program):
        raise NotImplementedError("Override in child classes")

    def parse_config(self, config_json: str):
        raise NotImplementedError("Override in child classes")


class MetricsCheck(Check):
    def __init__(self, name, long_name, check_config_str):
        super().__init__(check_family="Metrics", name=name, long_name=long_name, check_config_str=check_config_str)

    def metric_check(self, program, metrics):
        raise NotImplementedError("Override in child classes")

    def check(self, program: Program):
        return self.metric_check(program, program.getMetrics())


class DataflowCheck(Check):
    def __init__(self, name, long_name, check_config_str):
        super().__init__(check_family="Flow", name=name, long_name=long_name, check_config_str=check_config_str)

    def flow_check(self, program, backward_flow, forward_flow):
        raise NotImplementedError("Override in child classes")

    def check(self, program: Program):
        return self.flow_check(program, program.backward_flow, program.forward_flow)
