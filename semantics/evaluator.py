def evaluate(Block, *args):
    if len(args) == 0:
        return None
    res = 0
    for v in args:
        res += v
    return res
