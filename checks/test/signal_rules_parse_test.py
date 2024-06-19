import os
import sys

source_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")
if source_path not in sys.path:
    sys.path.append(source_path)
from constraint_rules import SignalRules
import pytest


def load_rule_files():
    constraint_data_dir = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "program_constraint_rules"
    )
    return {
        "Length": os.path.join(constraint_data_dir, "length.rules"),
        "Formatting": os.path.join(constraint_data_dir, "formatting.rules"),
        "NameConv": os.path.join(constraint_data_dir, "naming_conventions.rules"),
    }


@pytest.fixture
def rule_files():
    return load_rule_files()


def test_given_empty_values_shall_not_parse():
    with pytest.raises(ValueError) as excinfo:
        ruleset = SignalRules.from_json_string('{ "Rules": {"SomeName": ""} }')
    assert "Constraint cannot be empty" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        ruleset = SignalRules.from_json_string(
            '{ "Rules": {"": "Some_constraint(__input__)"} }'
        )
    assert "Empty name for constraint" in str(excinfo.value)


def test_given_no_template_value_constraint_shall_not_parse():
    with pytest.raises(ValueError) as excinfo:
        ruleset = SignalRules.from_json_string(
            '{ "Rules": {"NoTemplate": "len(test)>1"} }'
        )
    assert "Missing template for entity injection in constraint" in str(excinfo.value)


def test_given_unknown_constraints_shall_not_parse():
    with pytest.raises(ValueError) as excinfo:
        ruleset = SignalRules.from_json_string(
            '{ "Rules": {"MaliciousConstraint": "os.rmdir(__input__)"} }'
        )
    assert "Invalid constraint property" in str(excinfo)
    with pytest.raises(ValueError) as excinfo:
        _ = SignalRules.from_json_string(
            '{ "Rules": {"MaliciousConstraint": "not(os.rmdir(__input__))"} }'
        )
    assert "Invalid constraint property" in str(excinfo)



if __name__ == "__main__":
    files = load_rule_files()
