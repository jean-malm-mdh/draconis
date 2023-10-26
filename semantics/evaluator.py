from functools import reduce


def evaluate(Block, *args):
    def get_combinator(block_family_type: str):
        combinators = {"ADD": lambda acc, _v: acc + _v,
                       "SUB": lambda acc, _v: acc - _v,
                       "AND": lambda acc, _v: acc and _v}
        return combinators.get(block_family_type, lambda x, y: None)

    if len(args) == 0:
        return None
    for v in args:
        v_type = type(v)
        if v_type is not int and v_type is not bool:
            return None
    combinator = get_combinator(block_family_type=Block.getBlockFamily())
    res = args[0]
    for v in args[1:]:
        res = combinator(res, v)
    return res
