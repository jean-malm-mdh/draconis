from functools import reduce


def evaluate(Block, *args):
    def get_valid_py_types(block_family_type: str):
        valid_types = {"ADD": [int, float],
                       "SUB": [int, float],
                       "AND": [bool],
                       "OR": [bool]}
        return valid_types.get(block_family_type, None)

    def get_combinator(block_family_type: str):
        combinators = {"ADD": lambda acc, _v: acc + _v,
                       "SUB": lambda acc, _v: acc - _v,
                       "AND": lambda acc, _v: acc and _v,
                       "OR": lambda acc, _v: acc or _v}
        return combinators.get(block_family_type, lambda x, y: None)

    if len(args) == 0:
        return None
    valid_types = get_valid_py_types(block_family_type=Block.getBlockFamily())
    for v in args:
        v_type = type(v)
        if v_type not in valid_types:
            return None
    combinator = get_combinator(block_family_type=Block.getBlockFamily())
    return reduce(combinator, args)
