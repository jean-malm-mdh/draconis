import os
import sys

source_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")
if source_path not in sys.path:
    sys.path.append(source_path)
from constraint_rules import SignalRules
import pytest


def load_rule_files():
    constraint_data_dir = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "signal_constraint_rules"
    )
    return {
        "Empty": os.path.join(constraint_data_dir, "empty.rules"),
        "Length": os.path.join(constraint_data_dir, "length.rules"),
        "Formatting": os.path.join(constraint_data_dir, "formatting.rules"),
        "NameConv": os.path.join(constraint_data_dir, "naming_conventions.rules"),
    }


@pytest.fixture
def rule_files():
    return load_rule_files()


def test_given_no_rules_any_signal_is_ok(rule_files):
    ruleset = SignalRules.parse_rule_file(rule_files["Empty"])
    sigName = "TBFKAL80ETC"

    assert [] == ruleset.check(sigName)


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
        ruleset = SignalRules.from_json_string(
            '{ "Rules": {"MaliciousConstraint": "not(os.rmdir(__input__))"} }'
        )
    assert "Invalid constraint property" in str(excinfo)


def test_given_length_rule_names_shall_comply():
    ruleset = SignalRules.from_json_string(
        '{ "Rules": {"TooShort": "len(__input__)<10", "TooLong": "len(__input__)>20"} }'
    )
    assert [] == ruleset.check("TBFKAL80ETC"), "Positive test"
    assert ["TooShort"] == ruleset.check(
        "TBFKAL80"
    ), "Not detecting that input should be too short for first constraint"
    assert ["TooLong"] == ruleset.check(
        "TBFKAL80ETCTBFKAL80ETC"
    ), "The input should trigger the too long check to fail"


def test_given_templated_regex_can_transform_to_python_version():
    names = ["Apa", "apa", ""]
    ruleset = SignalRules.from_json_string(
        """{ "Defines": {"DEFTEMPLATE": "Apa"}, "Rules": {"isATemplateRule": "not(fullmatch(^##DEFTEMPLATE##$, __input__))"} }"""
    )
    assert [[], ["isATemplateRule"], ["isATemplateRule"]] == [
        ruleset.check(n) for n in names
    ]


def test_can_parse_constraint_rule_file(rule_files):
    ruleset = SignalRules.parse_rule_file(rule_files["Length"])
    assert ["IsTooShort", "IsTooLong"] == ruleset.getRuleNames()


if __name__ == "__main__":
    files = load_rule_files()
