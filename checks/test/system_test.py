import os
import sys

source_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
draconis_path = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
if source_path not in sys.path:
    sys.path.append(source_path)
if draconis_path not in sys.path:
    sys.path.append(draconis_path)
from constraint_rules import SignalRules
from AST.program import Program, extract_from_program
from draconis_parser.helper_functions import parse_pou_file
import pytest


def load_rule_files():
    program_constraint_dir = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "program_constraint_rules"
    )
    return {
        "Formatting": os.path.join(program_constraint_dir, "formatting.rules"),
        "Length": os.path.join(program_constraint_dir, "length.rules"),
        "LengthDefs": os.path.join(program_constraint_dir, "length_define_version.rules"),
        "NamingConvention": os.path.join(program_constraint_dir, "naming_conventions.rules")
    }


@pytest.fixture(scope="session", autouse=True)
def programs():
    testDir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "test_programs")
    programs = dict(
        [
            (n, parse_pou_file(p))
            for n, p in [
            ("MultiAND", f"{testDir}/MultiANDer.pou"),
            ("MultiANDLong", f"{testDir}/MultiANDerLongNames.pou")
        ]
        ]
    )
    return programs


@pytest.fixture
def rule_files():
    return load_rule_files()

def equal_no_ordering(l1,l2):
    assert set(l1) == set(l2)

def test_length_checks(programs, rule_files):
    ruleset = SignalRules.parse_rule_file(rule_files["Length"])
    equal_no_ordering(ruleset.check_program(programs["MultiAND"]), [])
    equal_no_ordering(ruleset.check_program(programs["MultiANDLong"]), {"SignalNameIsTooShort: On_ST",
                                                                   "SignalNameIsIsTooLong: TheActualSystemIsCurrentlyRunning_ST",
                                                                   "SignalNameIsIsTooLong: TheActualSystemIsCurrentlyNotBusy_ST"})


def test_given_templated_regex_can_transform_to_python_version():
    names = ["Apa", "apa", ""]
    ruleset = SignalRules.from_json_string(
        """{ "Defines": {"DEFTEMPLATE": "Apa"}, "Rules": {"isATemplateRule": "not(fullmatch(^##DEFTEMPLATE##$, __input__))"} }"""
    )
    assert [[], ["isATemplateRule"], ["isATemplateRule"]] == [
        ruleset.check(n) for n in names
    ]



def test_given_normal_and_defined_rule_version_results_are_equal(programs, rule_files):
    ruleset_normal = SignalRules.parse_rule_file(rule_files["Length"])
    ruleset_defs = SignalRules.parse_rule_file(rule_files["LengthDefs"])
    equal_no_ordering(ruleset_normal.get_rule_names(), ruleset_defs.get_rule_names())
    for prog in programs.values():
        assert set(ruleset_normal.check_program(prog)) == set(ruleset_defs.check_program(prog))