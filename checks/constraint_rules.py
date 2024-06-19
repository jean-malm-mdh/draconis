import functools
from pathlib import Path
import os
import sys
import json
import re
import logging

from functools import partial

logging.basicConfig(level=logging.DEBUG)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from checks.check_interface import PLACEHOLDERS, allowed_actions_map, \
    reserved_value_input_mapper

from AST.program import extract_from_program


class Rule:
    """
    A Rule is defined as a name and a constraint string.
    The string '__input__' is used as a placeholder for the entity string value that should be checked in the constraint
    """

    def __init__(self, name, constraint):
        self.name = name
        self.constraint = constraint
        self.aCheck = lambda cons, prog: None
        self.data_source = lambda prog: []

    def check_against_program(self, prog):
        datas = self.data_source(prog)
        to_check = partial(self.aCheck, datas)
        rule_failed_on_data = []
        for d in datas:
            if to_check(d):
                rule_failed_on_data.append(str(d))
        return rule_failed_on_data

    @classmethod
    def parse_data_source(cls, data_source: str):
        return partial(extract_from_program, data_source)

    def __str__(self) -> str:
        return f"Rule: {self.name} - {self.constraint}"

    @classmethod
    def parse(
            cls, rule_name, rule_constraint, data_source_str, _defines_map=None, abbreviations_map=None
    ):
        def handle_custom_syntax(constraint: str):
            result = constraint
            for reg_f in ["fullmatch", "any_match", "conforms_to"]:
                if reg_f in constraint:
                    result = re.sub(
                        rf"{reg_f}\s*\(([^,]*)\s*((?:,\s*[^,]*)*)\)",
                        rf'{reg_f}("\1"\2)', constraint
                    )
            result = result.replace(";", ",")
            return result.strip()

        def handle_defines(constraint, defines_map):
            theDefines = list(re.finditer(r"##(.*?)##", constraint))
            if theDefines and defines_map is None:
                raise ValueError("Defines have been used but no defines are declared.")
            for d in theDefines:
                define_name = d.group(1)
                constraint = re.sub(
                    f"##{define_name}##", defines_map[define_name], constraint
                )
            return constraint

        def is_func_style(constraint):
            return "|>" in constraint

        def parse_func_style(constraint: str):
            split_on_pipe = constraint.split("|>")
            result = split_on_pipe[0]
            split_on_pipe = map(handle_custom_syntax, split_on_pipe[1:])
            FUNC_NAME_PATTERN = r"([a-zA-Z_][a-zA-Z_0-9]*)"
            for f in split_on_pipe:
                m = re.match(rf"^\s*{FUNC_NAME_PATTERN}\((.*)\)\s*$", f)
                if m is not None:
                    f = f"partial({m.group(1)}, {m.group(2)})"
                result = f"{f}({result})"
            return result

        _defines_map = _defines_map or {}
        rule_constraint = handle_defines(rule_constraint, _defines_map)
        if is_func_style(rule_constraint):
            rule_constraint = parse_func_style(rule_constraint)
        else:
            rule_constraint = handle_custom_syntax(rule_constraint)
        res = Rule(rule_name, rule_constraint)
        _data_source = cls.parse_data_source(data_source_str)
        res.aCheck = lambda datas, e: eval(
            rule_constraint,
            allowed_actions_map(abbreviations_map),
            reserved_value_input_mapper(datas, e)
        )
        res.data_source = _data_source
        return res


class SignalRules:
    def __init__(self) -> None:
        self.rules = []

    @classmethod
    def parse_rule_file(cls, aRuleFile: os.PathLike):
        return SignalRules.from_json_string(Path.read_text(Path(aRuleFile)))

    @classmethod
    def from_json_string(cls, json_string: str):
        def check_valid_properties(rule_constraint):
            allowed_properties = [
                "len",
                "not",
                "any_match",
                "fullmatch",
                "unique",
                "map",
                "list",
                "conforms_to",
                "lower",
                "AND",
                "OR",
                "in_list",
            ]
            found_properties = re.finditer(r"([a-zA-Z_]+)\(", rule_constraint)
            for m in found_properties:
                prop = m.group(1)
                if prop not in allowed_properties:
                    return f"Invalid constraint property {prop} detected in constraint: {rule_constraint}"

        def error_check_constraint(a_rule_name, a_rule_constraint):
            if "" == a_rule_constraint:
                return "Constraint cannot be empty: " + a_rule_name
            if "" == a_rule_name:
                return "Empty name for constraint: " + a_rule_constraint
            placeholder_found = functools.reduce(lambda s, e: s or e in a_rule_constraint, PLACEHOLDERS, False)
            if not placeholder_found:
                return (
                        "Missing template for entity injection in constraint: "
                        + a_rule_constraint
                )
            return None

        data = json.loads(json_string)
        ruleset = SignalRules()
        rules = data.get("Rules", None)
        defines_map = data.get("Defines", None)
        abbreviations_map = data.get("Abbreviations", None)
        data_source_map = data.get("DataSource", None)
        assert rules is not None

        for rule_name, rule_constraint in rules.items():
            err = error_check_constraint(rule_name, rule_constraint)
            if err:
                raise ValueError(err)
            err = check_valid_properties(rule_constraint)
            if err:
                raise ValueError(err)
            ruleset.rules.append(
                Rule.parse(rule_name, rule_constraint, data_source_map, defines_map, abbreviations_map)
            )
        return ruleset

    def check(self, entity):
        return [r.name for r in self.rules if bool(r.check_rule_violation(entity))]

    def check_program(self, prog):
        res = []
        for r in self.rules:
            res.extend([f"{r.name}: {v}" for v in r.check_against_program(prog)])
        return res

    def check_all(self, entity_list):
        return [self.check(e) for e in entity_list]

    def get_rule_names(self):
        return [r.name for r in self.rules]

    def getRules(self):
        return self.rules
