from pytest import fixture
from AST import FBD_Block, FBDObjData
from semantics import evaluate


@fixture(scope="session")
def blocks():
    dummy_ID = 42
    add_block_data = FBDObjData(dummy_ID, "ADD")
    sub_block_data = FBDObjData(dummy_ID, "SUB")
    and_block_data = FBDObjData(dummy_ID, "AND")
    return {
        "add": (FBD_Block(add_block_data, {}, [])),
        "sub": (FBD_Block(sub_block_data, {}, [])),
        "and": (FBD_Block(and_block_data, {}, [])),
    }


def test_given_add_block_returns_addition(blocks):
    assert evaluate(blocks["add"], 3, 4) == 7
    assert evaluate(blocks["add"], 7, -7) == 0
    assert evaluate(blocks["add"]) == None


def test_given_invalid_datatypes_addition_returns_none(blocks):
    assert evaluate(blocks["add"], 'a', 'b') == None


def test_given_sub_block_returns_subtraction(blocks):
    assert evaluate(blocks["sub"], 3, 4) == -1


def test_given_and_block_returns_and(blocks):
    assert evaluate(blocks["and"], False, True) == False
