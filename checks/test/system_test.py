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
        "Empty": os.path.join(program_constraint_dir, "empty.rules"),
        "Length": os.path.join(program_constraint_dir, "length.rules"),
        "Formatting": os.path.join(program_constraint_dir, "formatting.rules"),
        "NameConv": os.path.join(program_constraint_dir, "naming_conventions.rules"),
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


def test_length_checks(programs, rule_files):
    ruleset = SignalRules.parse_rule_file(rule_files["Length"])
    assert ruleset.checkProgram(programs["MultiAND"]) == []
    assert ruleset.checkProgram(programs["MultiANDLong"]) == [
        "SignalNameIsIsTooLong: TheActualSystemIsCurrentlyOn_ST",
        "SignalNameIsIsTooLong: TheActualSystemIsCurrentlyRunning_ST",
        "SignalNameIsIsTooLong: TheActualSystemIsCurrentlyNotBusy_ST"
    ]
