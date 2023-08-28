from Web_GUI import Point

import pytest

from Web_GUI.parser.AST.ast_typing import SafeClass, DataflowDirection
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from test_programanalysis import programs

from helper_functions import parse_pou_file

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


def test_given_programs_with_only_graphical_changes_delta_shall_list_those(programs):
    progBefore = programs["Calc_Even"]
    testDir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "")
    progAfter = parse_pou_file(f"{testDir}/Collatz_Calculator_Even/Collatz_Calculator_Even.pou")

    assert progBefore == progAfter, "This is a pre-requisite for the remaining part of the test"

    progAfter.behaviour_id_map[9].data.boundary_box.move_by_delta(Point(10, 10))
    assert "Block 'DIV' moved. Re-run graphical checks" in progBefore.compute_delta(progAfter), \
        "After moving block in one of the programs, diff should report change in position"

    # Here we check if moving the block back to its original position removes the message
    progAfter.behaviour_id_map[9].data.boundary_box.move_by_delta(Point(-10, -10))
    assert "Block 'DIV' moved. Re-run graphical checks" not in progBefore.compute_delta(progAfter), \
        "After moving block back, should no longer be reported as a change"

    # If it is not a FBD block, reports only in/outvariable has moved
    progAfter.behaviour_id_map[5].data.boundary_box.move_by_delta(Point(10, 10))
    assert "Block 'outVariable' moved. Re-run graphical checks" in progBefore.compute_delta(progAfter)

    progAfter.behaviour_id_map[3].data.boundary_box.move_by_delta(Point(-10, -10))
    assert "Block 'inVariable' moved. Re-run graphical checks" in progBefore.compute_delta(progAfter)


def test_given_program_with_changed_FBD_type_delta_shall_list_that(programs):
    progBefore = programs["Calc_Even"]
    testDir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "")
    progAfter = parse_pou_file(f"{testDir}/Collatz_Calculator_Even/Collatz_Calculator_Even.pou")

    assert "DIV" == progAfter.behaviour_id_map[9].data.type
    progAfter.behaviour_id_map[9].data.type = "ADD"
    assert "Block 'DIV' changed to 'ADD'. Re-run functional checks" in progBefore.compute_delta(progAfter)

def test_given_program_with_added_blocks_delta_shall_list_those(programs):
    pytest.fail("To be done")


