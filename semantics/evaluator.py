from functools import reduce


def evaluate(Block, *args):
    if len(args) == 0:
        return None
    for v in args:
        v_type = type(v)
        if v_type is not int and v_type is not bool:
            return None
    combinator = (lambda acc, _v: acc + _v) if Block.getBlockFamily() == "ADD" else (
        lambda acc, _v: acc - _v) if Block.getBlockFamily() == "SUB" else (lambda acc, _v: acc and _v)
    res = args[0]
    for v in args[1:]:
        res = combinator(res, v)
    return res
