import sys
import os

source_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")
if source_path not in sys.path:
    sys.path.append(source_path)
from constraint_rules import SignalRules
import pytest


class ConstraintFuzzer:
    alphabet = [chr(a) for a in range(ord("a"), ord("a") + 26)]
    alphabet.extend([chr(a) for a in range(ord("A"), ord("A") + 26)])
    valid_rule_grammar = {
        "<ConstraintConfig>": ['{ "Rules": {<Constraints>} }'],
        "<Constraints>": ["<Constraint>, <Constraints>", "<Constraint>"],
        "<Constraint>": ['"<Name>": "<ConstraintString>"'],
        "<ConstraintString>": ["<Property> <Operator> <ConstraintValue>"],
        "<Property>": ["len(__input__)"],
        "<Operator>": ["==", "!=", "<", ">", "<=", ">="],
        "<ConstraintValue>": ["<Number>"],
        "<Number>": ["<DigitsNonZero>", "+<DigitsNonZero>", "-<DigitsNonZero>"],
        "<DigitsNonZero>": ["<DigitNonZero><Digits>", "<DigitNonZero>"],
        "<Digits>": ["<Digit><Digits>", "<Digit>"],
        "<LongName>": [
            "<Char><Name>",
            "<Char><Name>",
            "<Char><Name>",
            "<Char><Name>",
            "<Char><Name>",
            "<Char><Name>",
            "<Char>",
        ],
        "<Name>": ["<Char><Name>", "<Char>"],
        "<Char>": alphabet,  # a-z
        "<DigitNonZero>": [str(i) for i in range(1, 9)],
        "<Digit>": [str(i) for i in range(0, 9)],
    }

    def generate(grammar, startRule):
        import re
        import random

        def get_first_tag(s):
            return re.search(r"<[a-zA-Z]+>", s)

        start_rules = grammar[startRule]
        res = start_rules[random.randint(0, len(start_rules) - 1)]
        while get_first_tag(res) is not None:
            # find first tag, replace with random choice
            first_tag = get_first_tag(res)
            replacement_options = grammar[first_tag.group(0)]
            startPos, endPos = first_tag.span()
            res = (
                    res[:startPos]
                    + replacement_options[random.randint(0, len(replacement_options) - 1)]
                    + res[endPos:]
            )
        return res


def test_can_parse_random_rules():
    names = [
        ConstraintFuzzer.generate(ConstraintFuzzer.valid_rule_grammar, "<LongName>")
        for i in range(20)
    ]
    rules = [
        ConstraintFuzzer.generate(
            ConstraintFuzzer.valid_rule_grammar, "<ConstraintConfig>"
        )
        for i in range(1000)
    ]
    for n in names:
        for r in rules:
            rule = SignalRules.from_json_string(r)
            assert rule != []
            try:
                rule.check(n)
            except Exception as e:
                pytest.fail(
                    f"Rule check raised an exception {e} on random valid rules."
                )
