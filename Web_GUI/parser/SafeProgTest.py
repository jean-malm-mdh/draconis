import os.path
import sys

import pytest

from Web_GUI.parser.AST.ast_typing import SafeClass, DataflowDirection
from Web_GUI.parser.AST.path import PathDivide
from copy import deepcopy

sys.path.append(os.path.dirname(__file__))
from helper_functions import (
    parse_pou_file,
    parse_code_worksheet,
    get_worksheets_from_input,
    parse_variable_worksheet,
)


# TODO(TDD):
#  It shall be possible to check if functions depend on internal variables/state
#  * It shall be possible to start tracing any value in any direction
#  ** Ports shall only trace one way (outport => backwards, inport => forwards)
#  Dataflow shall handle cases where outputs depend on several inputs
#  * Dataflow shall handle cases where some outputs depend on some inputs


@pytest.fixture(scope="session", autouse=True)
def programs():
    programs = dict(
        [
            (n, parse_pou_file(p))
            for n, p in [
                ("Calc_Odd", "test/Collatz_Calculator_Odd/Collatz_Calculator_Odd.pou"),
                (
                    "Calc_Even",
                    "test/Collatz_Calculator_Even/Collatz_Calculator_Even.pou",
                ),
                (
                    "Calc_Even_SafeVer",
                    "test/Collatz_Calculator_Even/Collatz_Calculator_Even_UnsafeIn_SafeOut.pou",
                ),
                ("MultiAND", "test/MultiANDer.pou"),
                ("MultiANDAddedVariable", "test/MultiANDAddedVariables.pou"),
                ("MultiANDRemovedVariable", "test/MultiANDRemovedVariable.pou"),
                ("SingleIn_MultiOut", "test/TestPOU_SingleInput_MultipleOutput.pou"),
                ("output_has_non_outputs", "test/output_has_non_output_vars.pou"),
                ("input_has_non_inputs", "test/input_has_non_input_vars.pou"),
                ("empty_no_proper_groups", "test/empty_prog_no_groups.pou"),
            ]
        ]
    )
    return programs


def test_given_a_file_can_extract_numeric_metrics(programs):
    metrics = programs["Calc_Odd"].getMetrics()
    assert metrics["NrOfVariables"] == 2
    assert metrics["NrOfFuncBlocks"] == 2
    assert metrics["NrInputVariables"] == 1
    assert metrics["NrOutputVariables"] == 1


def test_given_a_name_can_get_variable_info_by_name(programs):
    info = programs["Calc_Even"].getVarInfo()
    assert (
        str(info["OutputVariables"].get("Result_Even", None))
        .replace("'", "")
        .replace('"', "")
        == "Var(UINT Result_Even: OutputVar = 0; Description: Result if the input is an even number)"
    )
    assert (
        str(info["InputVariables"].get("N", None)).replace("'", "").replace('"', "")
        == "Var(UINT N: InputVar = 1; Description: Collatz Input)"
    )
    assert len(info["InternalVariables"]) == 0


def test_given_program_can_extract_names_and_descriptions(programs):
    program = programs["Calc_Even"]
    """Basic functionality"""
    assert program.getVarDataColumns("name") == [["N"], ["Result_Even"]]
    assert program.getVarDataColumns("name", "description") == [
        ["N", "Collatz Input"],
        ["Result_Even", "Result if the input is an even number"],
    ]
    assert program.getVarDataColumns("description", "name") == [
        ["Collatz Input", "N"],
        ["Result if the input is an even number", "Result_Even"],
    ]

    """Boundary Values"""
    varInfo_noSpecifiedFields = program.getVarDataColumns()
    assert varInfo_noSpecifiedFields == [
        ["N", "InputVar", "UINT", "1", "Collatz Input", "1", "False"],
        [
            "Result_Even",
            "OutputVar",
            "UINT",
            "0",
            "Result if the input is an even number",
            "3",
            "False",
        ],
    ]

    varInfo_AllSpecifiedFields = program.getVarDataColumns(
        "name", "varType", "valueType", "initVal", "description", "lineNr", "isFeedback"
    )
    assert varInfo_AllSpecifiedFields == [
        ["N", "InputVar", "UINT", "1", "Collatz Input", "1", "False"],
        [
            "Result_Even",
            "OutputVar",
            "UINT",
            "0",
            "Result if the input is an even number",
            "3",
            "False",
        ],
    ]


def test_from_output_can_perform_simple_backward_traces(programs):
    """
    Test checks standard case of dataflow - two numerical values going into binary arithmetic block
    Resulting operation is dependent on both operands
    Resulting operation goes directly into outport
    """
    expected = [5, 9, 8, PathDivide([[6, 3], [7, 4]])]
    actual = programs["Calc_Even"].getTrace(DataflowDirection.Backward)["Result_Even"]
    assert actual == expected


def test_backward_trace_can_handle_multi_in_single_out_blocks(programs):
    """
    Test checks standard case of dataflow - two numerical values going into binary arithmetic block
    Resulting operation is dependent on both operands
    Resulting operation goes directly into outport
    """
    expected = [9, 3, 2, PathDivide([[0, 5], [1, 7], [4, 8]])]
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
    expected = {"OutputByte1": [6, 4, 2, 1, 5], "OutputByte2": [7, 4, 3, 1, 5]}
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
    expected = {"InputWord": [[5, 1, 2, 4, 6], [5, 1, 3, 4, 7]]}
    actual = program.getTrace(DataflowDirection.Forward)
    assert actual == expected


def test_can_get_dataflow_from_func_block(programs):
    pytest.skip("Higher priority tests came up")
    assert programs["Calc_Even"].behaviour_id_map[9].getFlow(
        DataflowDirection.Backward
    ) == [(8, 6), (8, 7)]
    assert programs["Calc_Even"].behaviour_id_map[9].getFlow(
        DataflowDirection.Forward
    ) == [(6, 8), (6, 7)]


def test_can_get_dataflow_from_var_block(programs):
    pytest.skip("Higher priority tests came up")
    inVarBlock = programs["Calc_Even"].behaviour_id_map[3]
    assert inVarBlock.getFlow(DataflowDirection.Backward) == []
    assert inVarBlock.getFlow(DataflowDirection.Forward) == [(3, 6)]


def test_from_input_can_perform_simple_forward_traces(programs):
    expected = [[3, 6, 8, 9, 5]]
    actual = programs["Calc_Even"].getTrace(DataflowDirection.Forward)["N"]
    assert actual == expected


def test_can_classify_expression_safeness_by_name(programs):
    assert (
        programs["Calc_Even"].getVarInfo()["Safeness"]["Result_Even"]
        == SafeClass.Unsafe
    )
    assert programs["Calc_Even"].getVarInfo()["Safeness"]["N"] == SafeClass.Unsafe


def test_can_detect_unsafe_usage_of_data_at_safe_output(programs):
    safeness_info = programs["Calc_Even_SafeVer"].getVarInfo()["Safeness"]
    assert (
        SafeClass.Unsafe == safeness_info["N"]
        and SafeClass.Safe == safeness_info["Result_Even"]
    ), "Prerequisite for remainder of test to be reasonable does not hold"
    assert programs["Calc_Even_SafeVer"].checkSafeDataFlow() == [
        "ERROR: Unsafe data ('N') flowing to safe output ('Result_Even')"
    ]


def test_can_check_cohesiveness_and_structure_of_variable_header(programs):
    assert (
        programs["empty_no_proper_groups"].varHeader.evaluate_cohesion_of_sheet() == []
    )
    assert programs[
        "empty_no_proper_groups"
    ].varHeader.evaluate_structure_of_var_sheet() == [
        "No input variables defined.",
        "The Input group has not been defined.",
        "No output variables defined.",
        "The Output group has not been defined.",
    ]


def test_multi_sequence_FBD_block_dataflow_trace(programs):
    program = programs["Calc_Odd"]
    # ID 0-5: line segments
    # ID 6: Input Port (constant UINT#1)
    # ID 7: Input Port (N)
    # ID 8: Input Port (constant UINT#3)
    # ID 9: Output Port (Result_Odd)
    # ID 10: Param Input 1 ADD
    # ID 11: Param Input 2 ADD
    # ID 12: Param Output ADD
    # ID 13: Param Input 1 MULT
    # ID 14: Param Input 2 MULT
    # ID 15: Param Output MULT
    # ID 16: ADD Block
    # ID 17: MULT Block
    # TODO: Problem seems to be when connecting from one block to another
    backtrace = program.getBackwardTrace()
    flattened_trace = PathDivide.unpack_pathlist([backtrace["Result_Odd"]])
    assert flattened_trace == [
        [9, 16, 12, 10, 17, 15, 13, 7],
        [9, 16, 12, 10, 17, 15, 14, 8],
        [9, 16, 12, 11, 6],
    ]


def test_given_unsafe_output_safeness_is_irrelevant(programs):
    # For sanity checking of test data
    safeness_info = programs["Calc_Even"].getVarInfo()["Safeness"]
    assert (
        SafeClass.Unsafe == safeness_info["N"]
        and SafeClass.Unsafe == safeness_info["Result_Even"]
    ), "Prerequisite for remainder of test to be reasonable does not hold"
    assert programs["Calc_Even"].checkSafeDataFlow() == []


def test_metrics_pipeline():
    inputProgram = """PROGRAM Main
    { VariableWorksheet := 'Variables' }
    {GroupDefinition(0,'Inputs')}
    {GroupDefinition(2,'Outputs')}
    {GroupDefinition(4,'Internals')}
    
    VAR_INPUT {Group(0)}
    END_VAR
    
    VAR_OUTPUT {Group(0)}
    END_VAR
    
    VAR {Group(0)}
            {LINE(1)}
            Input1 : UINT := 0; (*FirstUIntDesc*)
    END_VAR
    
    VAR_INPUT {Group(2)}
    END_VAR
    
    VAR_OUTPUT {Group(2)}
    END_VAR
    
    VAR {Group(2)}
            {LINE(3)}
            Input3 : UINT := 0; (*Desc*)
    END_VAR
    
    VAR_INPUT {Group(4)}
    END_VAR
    
    VAR_OUTPUT {Group(4)}
    END_VAR
    
    VAR {Group(4)}
    END_VAR
    
    { CodeWorksheet := 'Main', Type := '.fbd' }
    <?xml version="1.0" encoding="utf-16" standalone="yes"?>
    <FBD>
    <addData>
      <data name="blabla.com" handleUnknown="preserve">
        <line localId="11" beginX="64" beginY="9" endX="67" endY="9" />
      </data>
    </addData>
    <inVariable localId="1" height="4" width="18">
      <position x="86" y="14" />
      <expression>Input1</expression>
      <connectionPointOut>
        <relPosition x="18" y="2" />
      </connectionPointOut>
    </inVariable>
    <block localId="4" height="24" width="16" typeName="ADD">
      <position x="152" y="34" />
      <addData>
        <data name="blabla.com" handleUnknown="preserve">
          <fbData fbFuType="1" />
        </data>
      </addData>
      <inputVariables>
        <variable formalParameter="IN1" hidden="true">
          <connectionPointIn>
            <relPosition x="0" y="8" />
            <connection refLocalId="0" />
          </connectionPointIn>
          <addData>
            <data name="blabla.com" handleUnknown="preserve">
              <fp localId="1" inState="640" outState="0" width="2" height="2" flagType="" dataType="ANY_NUM" />
            </data>
          </addData>
        </variable>
        <variable formalParameter="IN2" hidden="true">
          <connectionPointIn>
            <relPosition x="0" y="16" />
            <connection refLocalId="5" />
          </connectionPointIn>
          <addData>
            <data name="blabla.com" handleUnknown="preserve">
              <fp localId="2" inState="640" outState="0" width="2" height="2" flagType="" dataType="ANY_NUM" />
            </data>
          </addData>
        </variable>
      </inputVariables>
      <inOutVariables />
      <outputVariables>
        <variable formalParameter="ADD" hidden="true">
            <connectionPointIn>
              <relPosition x="16" y="10" />
              <connection refLocalId="5" />
            </connectionPointIn>
            <addData>
              <data name="blabla.com" handleUnknown="preserve">
                <fp localId="3" inState="0" outState="640" width="2" height="2" flagType="" dataType="ANY_NUM" />
              </data>
            </addData>
          </variable>
      </outputVariables>
    </block>
    <inVariable localId="5" height="4" width="18">
      <position x="86" y="22" />
      <expression>Input1</expression>
      <connectionPointOut>
        <relPosition x="18" y="2" />
      </connectionPointOut>
    </inVariable>
  </FBD>
    END_PROGRAM
    """
    input_varWorkSheet, input_codeSheet = get_worksheets_from_input(inputProgram)
    program = parse_variable_worksheet(input_varWorkSheet)
    program.behaviourElements, program.behaviour_id_map, _ = parse_code_worksheet(
        input_codeSheet
    )
    assert program.getMetrics()["NrOfVariables"] == 2
    assert program.getMetrics()["NrOfFuncBlocks"] == 1


def test_given_a_variable_sheet_inputs_shall_only_be_in_input_group(programs):
    program = programs["output_has_non_outputs"]
    groups = list(program.getVarGroups())
    assert [group.getName() for group in groups] == ["Inputs", "Outputs"]
    inputGroup, outputGroup = groups[0], groups[1]
    assert [issue.lower() for issue in inputGroup.checkForCohesionIssues()] == []
    assert [issue.lower() for issue in outputGroup.checkForCohesionIssues()] == [
        "non-output detected in output group: candowork_st"
    ]


def test_given_a_variable_sheet_outputs_shall_only_be_in_output_group(programs):
    program = programs["input_has_non_inputs"]
    groups = list(program.getVarGroups())
    assert [group.getName() for group in groups] == ["Inputs", "Outputs"]
    inputGroup, outputGroup = groups[0], groups[1]
    assert [issue.lower() for issue in inputGroup.checkForCohesionIssues()] == [
        "non-input detected in input group: candowork_st"
    ]
    assert [issue.lower() for issue in outputGroup.checkForCohesionIssues()] == []


def test_given_two_identical_programs_list_of_deltas_shall_be_empty(programs):
    for prog in programs.values():
        prog_copy = deepcopy(prog)
        assert prog.compute_delta(prog_copy) == []


def test_given_program_with_variable_changes_list_of_deltas_shall_contain_change_info(
    programs,
):
    prog = programs["Calc_Even"]
    prog_changed = programs["Calc_Even_SafeVer"]

    assert (
        "Var(UINT Result_Even: OutputVar = 0; Description: 'Result if the input is an even number')",
        "Var(SAFEUINT Result_Even: OutputVar = 0; Description: 'Result if the input is an even number')",
    ) in prog.compute_delta(prog_changed)


def test_given_two_different_programs_not_intended_to_run_delta_computation(programs):
    prog = programs["Calc_Odd"]
    prog_different = programs["Calc_Even"]

    assert prog.compute_delta(prog_different) == [
        (
            "Program names are different. Delta analysis will not continue",
            "Collatz_Calculator_Odd != Collatz_Calculator_Even",
        )
    ]


def test_given_programs_with_changed_variable_number_delta_shall_contain_additions(
    programs,
):
    prog = programs["MultiAND"]
    prog_addition = programs["MultiANDAddedVariable"]
    actual = prog.compute_delta(prog_addition)
    expected = (
        "",
        "Var(SAFEBOOL IsInSafeState: InputVar = UNINIT; Description: 'If System is in safe state')",
    )
    assert expected in actual

    prog_removal = programs["MultiANDRemovedVariable"]
    expected = (
        "Var(SAFEBOOL IsNotBusy_ST: InputVar = UNINIT; Description: 'If system is busy')",
        "",
    )
    assert expected in prog.compute_delta(prog_removal)


def main():
    pass


if __name__ == "__main__":
    main()
