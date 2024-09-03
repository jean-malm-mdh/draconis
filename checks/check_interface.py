from functools import partial

from checks.rule_utility_functions import unique, any_match, full_match, conforms_to, is_magic_named_constant, in_list

INPUT_PLACEHOLDER = "__input__"
INPUT_PLACEHOLDER_LIST = "__inputlist__"
METRIC_PLACEHOLDER = "metric"
PLACEHOLDERS = [INPUT_PLACEHOLDER, INPUT_PLACEHOLDER_LIST, METRIC_PLACEHOLDER]


def allowed_actions_map(abbreviations_map):
    """
    Mapping of the list of properties to their functional implementation.
    """
    return {
        "unique": unique,
        "any_match": any_match,
        "full_match": full_match,
        "conforms_to": partial(conforms_to, abbreviations_map),
        "partial": partial,
        "len": len,
        "AND": bool.__and__,
        "OR": bool.__or__,
        "is_magic_named_constant": is_magic_named_constant,
        "in_list": in_list,
    }


# Expose the allowed actions to other classes
ALLOWED_ACTIONS_NAMES = [k for k in allowed_actions_map({}).keys()]


def reserved_value_input_mapper(data_source, data_source_element):
    return {
        INPUT_PLACEHOLDER_LIST: data_source,
        INPUT_PLACEHOLDER: data_source_element
    }
