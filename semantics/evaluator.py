from functools import reduce


def evaluate(Block, *args):
    if len(args) == 0:
        return None
    for v in args:
        if type(v) is not int:
            return None
    combinator = (lambda acc, _v: acc + _v) if Block.getBlockFamily() == "ADD" else (lambda acc, _v: acc - _v)
    res = args[0]
    for v in args[1:]:
        res = combinator(res, v)
    return res
