import pytest

from draconis_parser import DataflowDirection, SafeClass
from draconis_parser import PathDivide
from .test_programanalysis import programs


def test_can_get_dataflow_from_var_block(programs):
    inVarBlock = programs["Calc_Even"].behaviour_id_map[3]
    assert inVarBlock.getFlowOverBlock(DataflowDirection.Backward) == []
    assert inVarBlock.getFlowOverBlock(DataflowDirection.Forward) == [(3, [(3, 6)])]

    outVarBlock = programs["Calc_Even"].behaviour_id_map[5]
    assert outVarBlock.getFlowOverBlock(DataflowDirection.Forward) == []
    assert outVarBlock.getFlowOverBlock(DataflowDirection.Backward) == [(5, [(5, 8)])]


def test_can_get_dataflow_from_FBD(programs):
    fbd_block = programs["Calc_Even"].behaviour_id_map[9]
    assert fbd_block.getFlowOverBlock(DataflowDirection.Backward) == [(8, [(6, 3), (7, 4)])]
    assert fbd_block.getFlowOverBlock(DataflowDirection.Forward) == [(6, [(8, 5)]),
                                                                     (7, [(8, 5)])]


def test_can_perform_backward_trace_from_block(programs):
    expected = [8, PathDivide([[6, 3], [7, 4]])]
    actual = programs["Calc_Even"].performBackTraceFromBlock(9)
    assert actual == expected


def test_from_output_can_perform_simple_backward_traces(programs):
    """
    Test checks standard case of dataflow - two numerical values going into binary arithmetic block
    Resulting operation is dependent on both operands
    Resulting operation goes directly into outport
    """
    expected = [5, 8, PathDivide([[6, 3], [7, 4]])]
    actual = programs["Calc_Even"].getTrace(DataflowDirection.Backward)["Result_Even"]
    assert actual == expected


def test_backward_trace_can_handle_multi_in_single_out_blocks(programs):
    """
    Test checks standard case of dataflow - two numerical values going into binary arithmetic block
    Resulting operation is dependent on both operands
    Resulting operation goes directly into outport
    """
    expected = [9, 2, PathDivide([[0, 5], [1, 7], [4, 8]])]
    actual = programs["MultiAND"].getTrace(DataflowDirection.Backward)["CanDoWork_ST"]
    assert actual == expected


def test_backward_trace_can_handle_single_in_multiple_out_blocks(programs):
    program = programs["SingleIn_MultiOut"]
    # ID(5) - Inport #1
    # ID(1) - Input Param #1
    # ID(2) - OutPut Param #1
    # ID(3) - OutPut Param #2
    # ID(4) - FBD block ID
    # ID(6) - Outport #1
    # ID(7) - Outport #2
    expected = {"OutputByte1": [6, 2, 1, 5], "OutputByte2": [7, 3, 1, 5]}
    actual = program.getBackwardTrace()
    assert actual == expected


def test_forward_trace_can_handle_single_in_multiple_out_blocks(programs):
    program = programs["SingleIn_MultiOut"]
    # ID(5) - Inport #1
    # ID(1) - Input Param #1
    # ID(2) - OutPut Param #1
    # ID(3) - OutPut Param #2
    # ID(4) - FBD block ID
    # ID(6) - Outport #1
    # ID(7) - Outport #2
    expected = {"InputWord": [[5, 1, 2, 6], [5, 1, 3, 7]]}
    actual = program.getTrace(DataflowDirection.Forward)
    assert actual == expected


def test_can_get_dataflow_from_func_block(programs):
    pytest.skip("Higher priority tests came up")
    assert programs["Calc_Even"].behaviour_id_map[9].getFlowOverBlock(
        DataflowDirection.Backward
    ) == [[8, 6, 3], [8, 7, 4]]
    assert programs["Calc_Even"].behaviour_id_map[9].getFlowOverBlock(
        DataflowDirection.Forward
    ) == [[8, 9, 5]]


def test_from_input_can_perform_simple_forward_traces(programs):
    expected = [[3, 6, 8, 5]]
    actual = programs["Calc_Even"].getTrace(DataflowDirection.Forward)["N"]
    assert actual == expected


def test_can_classify_expression_safeness_by_name(programs):
    assert (
            programs["Calc_Even"].getVarInfo()["Safeness"]["Result_Even"]
            == SafeClass.Unsafe
    )
    assert programs["Calc_Even"].getVarInfo()["Safeness"]["N"] == SafeClass.Unsafe


def test_multi_sequence_FBD_block_dataflow_trace(programs):
    program = programs["Calc_Odd"]
    backtrace = program.getBackwardTrace()
    flattened_trace = PathDivide.unpack_pathlist([backtrace["Result_Odd"]])
    assert flattened_trace == [
        [9, 12, 10, 15, 13, 7],
        [9, 12, 10, 15, 14, 8],
        [9, 12, 11, 6],
    ]
