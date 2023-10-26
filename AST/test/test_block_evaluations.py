from pytest import fixture
from AST import FBD_Block, FBDObjData
from semantics import evaluate

dummy_ID = 42


def test_given_add_block_returns_addition():
    add_block_data = FBDObjData(dummy_ID, "ADD")
    add_block = FBD_Block(add_block_data, {}, [])
    assert evaluate(add_block, 3, 4) == 7
    assert evaluate(add_block, 7, -7) == 0
    assert evaluate(add_block) == None
