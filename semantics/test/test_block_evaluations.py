import functools
import operator

from pytest import fixture
from AST import FBD_Block, FBDObjData
from semantics import evaluate
from random import Random


@fixture(scope="session")
def blocks():
    dummy_ID = 42
    add_block_data = FBDObjData(dummy_ID, "ADD")
    sub_block_data = FBDObjData(dummy_ID, "SUB")
    and_block_data = FBDObjData(dummy_ID, "AND")
    or_block_data = FBDObjData(dummy_ID, "OR")
    return {
        "add": (FBD_Block(add_block_data, {}, [])),
        "sub": (FBD_Block(sub_block_data, {}, [])),
        "and": (FBD_Block(and_block_data, {}, [])),
        "or": (FBD_Block(or_block_data, {}, [])),
    }


def test_given_add_block_returns_addition(blocks):
    add_b = blocks["add"]
    assert evaluate(add_b, 3, 4) == 7
    assert evaluate(add_b, 7, -7) == 0
    assert evaluate(add_b) == None


def test_given_invalid_datatypes_addition_returns_none(blocks):
    assert evaluate(blocks["add"], 'a', 'b') == None
    assert evaluate(blocks["add"], True, True) == None


def test_given_SUB_block_evaluate_as_sub(blocks):
    assert evaluate(blocks["sub"], 3, 4) == -1


def test_given_AND_block_evaluate_as_AND(blocks):
    assert evaluate(blocks["and"], False, False) == False
    assert evaluate(blocks["and"], False, True) == False
    assert evaluate(blocks["and"], True, False) == False
    assert evaluate(blocks["and"], True, True) == True


def test_given_OR_block_evaluate_as_OR(blocks):
    assert evaluate(blocks["or"], False, False) == False
    assert evaluate(blocks["or"], False, True) == True
    assert evaluate(blocks["or"], True, False) == True
    assert evaluate(blocks["or"], True, True) == True


def get_random_list(rnd: Random, req_type, min_max_amount=(1, 10), seed=None):
    if seed is not None:
        rnd.seed(seed)
    amount = rnd.randint(min_max_amount[0], min_max_amount[1])
    producer = lambda _: rnd.randint(-1000, 1000) if req_type is int else rnd.choice([True, False])
    return [producer(_) for _ in range(amount)]


def test_given_blocks_with_more_than_two_arguments_evaluation_shall_still_work(blocks):
    rnd_obj = Random()
    for i in range(100):
        arg_int_list = get_random_list(rnd_obj, int, (3, 20), seed=42)
        assert evaluate(blocks["add"], *arg_int_list) == sum(arg_int_list)
        assert evaluate(blocks["sub"], *arg_int_list) == functools.reduce(operator.sub, arg_int_list)
    for i in range(100):
        arg_int_list = get_random_list(rnd_obj, bool, (3, 20), seed=42)
        assert evaluate(blocks["and"], *arg_int_list) == functools.reduce(operator.and_, arg_int_list)
        assert evaluate(blocks["or"], *arg_int_list) == functools.reduce(operator.or_, arg_int_list)

