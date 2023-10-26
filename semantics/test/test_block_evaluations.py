from pytest import fixture
from AST import FBD_Block, FBDObjData
from semantics import evaluate


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
    assert evaluate(blocks["add"], 3, 4) == 7
    assert evaluate(blocks["add"], 7, -7) == 0
    assert evaluate(blocks["add"]) == None


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
