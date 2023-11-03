import pytest
import os
import sys

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                             ".."))
from rule_utility_functions import conforms_to


def test_given_degenerate_cases_then_finishes_early():
    assert True == conforms_to(pattern="", input="",
                               name_groups={}), "empty pattern and input => conformant by construction"

    assert False == conforms_to(pattern="", input="a",
                                name_groups={}), "if pattern is empty, no non-empty input is conformant"
    assert False == conforms_to(pattern="a", input="",
                                name_groups={}), "If input is empty, no non-empty pattern is acceptable"


def test_given_only_constant_string_then_works_as_string_comparison():
    assert True == conforms_to(
        pattern="constant string conform only to itself",
        input="constant string conform only to itself",
        name_groups={},
    )
    assert False == conforms_to(
        pattern="constant string conform only to itself",
        input="but this is different",
        name_groups={},
    )


def test_given_nonexistant_tag_then_fails_with_exception():
    with pytest.raises(ValueError) as excinfo:
        conforms_to(pattern="<A>", input="apa", name_groups={})
    assert "Tag <A>" in str(excinfo), "Should receive info of which tag failed"
    assert "does not exist" in str(excinfo), "Should clarify what has gone wrong"


def test_given_pattern_with_tags_then_should_match_tags():
    assert True == conforms_to(pattern="<A>", input="apa", name_groups={"<A>": ["apa"]})
    assert False == conforms_to(
        pattern="<A>", input="apabar", name_groups={"<A>": ["apa"]}
    )

    assert True == conforms_to(
        pattern="<A> <B>_<C>",
        input="apa bar_car",
        name_groups={"<A>": ["apa"], "<B>": ["bar"], "<C>": ["car"]},
    )


def test_given_tags_with_optional_repetition_then_should_match_zero_or_more_times():
    assert True == conforms_to(pattern="<A>*", input="", name_groups={"<A>": ["apa"]})
    assert True == conforms_to(
        pattern="<A>*", input="apaapaapa", name_groups={"<A>": ["apa"]}
    )

    assert False == conforms_to(
        pattern="<A>", input="apaapa", name_groups={"<A>": ["apa"]}
    )


def test_given_tags_with_mandatory_repetition_then_must_match_at_least_once():
    assert False == conforms_to(pattern="<A>+", input="", name_groups={"<A>": ["apa"]})
    assert False == conforms_to(pattern="<A>+", input="ap", name_groups={"<A>": ["apa"]})

    assert True == conforms_to(
        pattern="<A>+", input="apa", name_groups={"<A>": ["apa"]}
    )

    assert True == conforms_to(
        pattern="<A>+ <B>_<C>+",
        input="apa bar_car",
        name_groups={"<A>": ["apa"], "<B>": ["bar"], "<C>": ["car"]},
    )


def _tags():
    return {"<A>": ["a"], "<B>": ["b"]}


@pytest.fixture
def tags():
    return _tags()


def test_conforms_to_rules_can_be_grouped(tags):
    assert False == conforms_to(name_groups=tags, pattern="(<A><B>)", input="")
    assert False == conforms_to(name_groups=tags, pattern="(<A><B>)", input="a")
    assert False == conforms_to(name_groups=tags, pattern="(<A><B>)", input="b")
    assert True == conforms_to(name_groups=tags, pattern="(<A><B>)", input="ab")


def test_given_group_in_rule_when_group_is_optional_then_group_can_be_optional(tags):
    assert True == conforms_to(name_groups=tags, pattern="(<A><B>)?", input="")

    assert False == conforms_to(name_groups=tags, pattern="(<A><B>)?", input="a")
    assert False == conforms_to(name_groups=tags, pattern="(<A><B>)?", input="b")

    assert True == conforms_to(name_groups=tags, pattern="(<A><B>)?", input="ab")


def test_given_repeating_group_then_group_can_repeat_zero_or_more_times(tags):
    assert True == conforms_to(name_groups=tags, pattern="(<A><B>)*", input="")

    assert False == conforms_to(name_groups=tags, pattern="(<A><B>)*", input="a")
    assert False == conforms_to(name_groups=tags, pattern="(<A><B>)*", input="b")

    assert True == conforms_to(name_groups=tags, pattern="(<A><B>)*", input="ab")
    assert True == conforms_to(name_groups=tags, pattern="(<A><B>)*", input="abab")
    assert True == conforms_to(name_groups=tags, pattern="(<A><B>)*", input="ababab")


def test_given_mandatory_groups_then_group_must_match_at_least_once(tags):
    assert False == conforms_to(name_groups=tags, pattern="(<A><B>)+", input="")
    assert True == conforms_to(name_groups=tags, pattern="(<A><B>)+", input="ab")

    assert False == conforms_to(name_groups=tags, pattern="(<A><B>)+", input="aba")
    assert True == conforms_to(name_groups=tags, pattern="(<A><B>)+", input="abab")


def test_given_groups_when_inner_tags_have_quantifiers_then_quantifiers_should_be_respected(tags):
    assert True == conforms_to(name_groups=tags, pattern="(<A><B>?)", input="a")
    assert False == conforms_to(name_groups=tags, pattern="(<A><B>?)", input="aa")
    assert True == conforms_to(name_groups=tags, pattern="(<A>?<B>)", input="b")
    assert False == conforms_to(name_groups=tags, pattern="(<A>?<B>)", input="bb")

    assert True == conforms_to(name_groups=tags, pattern="(<A>?<B>?)", input="")
    assert True == conforms_to(name_groups=tags, pattern="(<A>?<B>?)", input="ab")


def main():
    fixture_tags = _tags()
    test_given_groups_when_inner_tags_have_quantifiers_then_quantifiers_should_be_respected(fixture_tags)


if __name__ == "__main__":
    main()
