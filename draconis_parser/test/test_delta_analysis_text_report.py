from Web_GUI import Point

import pytest

import sys
import os
import re


def compare_strings_no_spacing(str1, str2):
    return str1 == str2 or (
            re.sub("\s", "", str1) == re.sub("\s", "", str2)
    )


def string_no_spacing_in_iterable(s, iterable):
    for candidate in iterable:
        if compare_strings_no_spacing(s, candidate):
            return True

    return False


from draconis_parser.helper_functions import parse_pou_file
import pickle


@pytest.fixture(scope="session", autouse=True)
def load_programs():
    testDir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "")
    programs = dict(
        [
            (n, pickle.dumps(parse_pou_file(p)))
            for n, p in [
            ("Calc_Odd", f"{testDir}/Collatz_Calculator_Odd/Collatz_Calculator_Odd.pou"),
            (
                "Calc_Even",
                f"{testDir}/Collatz_Calculator_Even/Collatz_Calculator_Even.pou",
            ),
            (
                "Calc_Even_SafeVer",
                f"{testDir}/Collatz_Calculator_Even/Collatz_Calculator_Even_UnsafeIn_SafeOut.pou",
            ),
            ("MultiAND", f"{testDir}/MultiANDer.pou"),
            ("MultiANDAddedVariable", f"{testDir}/MultiANDAddedVariables.pou"),
            ("MultiANDRemovedVariable", f"{testDir}/MultiANDRemovedVariable.pou"),
            ("SingleIn_MultiOut", f"{testDir}/TestPOU_SingleInput_MultipleOutput.pou"),
            ("output_has_non_outputs", f"{testDir}/output_has_non_output_vars.pou"),
            ("input_has_non_inputs", f"{testDir}/input_has_non_input_vars.pou"),
            ("empty_no_proper_groups", f"{testDir}/empty_prog_no_groups.pou"),
        ]
        ]
    )
    return programs


@pytest.fixture(autouse=True)
def programs_with_clones(load_programs):
    return {n: (pickle.loads(p), pickle.loads(p)) for n, p in load_programs.items()}


# These tests are brittle, expect them to flake
def test_given_program_with_variable_changes_list_of_deltas_shall_contain_change_info(
        programs_with_clones,
):
    prog = programs_with_clones["Calc_Even"][0]
    prog_changed = programs_with_clones["Calc_Even_SafeVer"][0]

    assert (
        string_no_spacing_in_iterable(
            "Var(UINT Result_Even: OutputVar = 0; Description: 'Result if the input is an even number') -> "
            "Var(SAFEUINT Result_Even: OutputVar = 0; Description: 'Result if the input is an even number')",
            prog.compute_delta(prog_changed))
    )


def test_given_two_different_programs_not_intended_to_run_delta_computation(programs_with_clones):
    prog = programs_with_clones["Calc_Odd"][0]
    prog_different = programs_with_clones["Calc_Even"][0]
    actual = prog.compute_delta(prog_different)
    print(actual)
    assert "Program names are different. Delta analysis will not continue" in actual
    assert "Collatz_Calculator_Odd != Collatz_Calculator_Even" in actual


def test_given_programs_with_added_variable_delta_shall_contain_additions(
        programs_with_clones,
):
    prog = programs_with_clones["MultiAND"][0]
    prog_addition = programs_with_clones["MultiANDAddedVariable"][0]
    actual = prog.compute_delta(prog_addition)
    # TL;DR: info that variable has been added should exist and come before the variable list
    assert 'The following variables have been added between the versions' in actual
    assert "Var(SAFEBOOL IsInSafeState: InputVar = UNINIT; Description: 'If System is in safe state')" in actual
    assert actual.index('The following variables have been added between the versions') < \
           actual.index("Var(SAFEBOOL IsInSafeState: InputVar = UNINIT; Description: 'If System is in safe state')")


def test_given_program_with_removed_variable_delta_shall_contain_this_information(
        programs_with_clones
):
    prog = programs_with_clones["MultiAND"][0]
    prog_removal = programs_with_clones["MultiANDRemovedVariable"][0]

    assert string_no_spacing_in_iterable(
        "Var(SAFEBOOL IsNotBusy_ST: InputVar = UNINIT; Description: 'If system is busy') -> ",
        prog.compute_delta(prog_removal))


def test_given_programs_with_only_graphical_changes_delta_shall_list_those(programs_with_clones):
    # Given two programs
    progBefore, progAfter = programs_with_clones["Calc_Even"]

    # When programs are initially identical
    assert progBefore == progAfter, "This is a pre-requisite for the remaining part of the test"

    # And one program has changed by moving an FBD block
    element_to_move = progAfter.behaviour_id_map[9]
    element_to_move.data.boundary_box.move_by_delta(Point(10, 10))

    # Then delta check shall detect and report the move
    assert "Block 'DIV' moved. Re-run graphical checks" in progBefore.compute_delta(progAfter), \
        "After moving block in one of the programs, diff should report change in position"

    # And when the same element is moved back
    element_to_move.data.boundary_box.move_by_delta(Point(-10, -10))

    # Then the delta check shall no longer detect a delta
    assert "Block 'DIV' moved. Re-run graphical checks" not in progBefore.compute_delta(progAfter), \
        "After moving block back, should no longer be reported as a change"

    # And if a variable block is moved
    outVarBlock = progAfter.behaviour_id_map[5]
    inVarBlock = progAfter.behaviour_id_map[3]
    outVarBlock.data.boundary_box.move_by_delta(Point(10, 10))
    inVarBlock.data.boundary_box.move_by_delta(Point(-10, -10))

    # Then the delta analysis shall note the move
    delta_analysis = progBefore.compute_delta(progAfter)
    assert "Block 'outVariable' moved. Re-run graphical checks" in delta_analysis
    assert "Block 'inVariable' moved. Re-run graphical checks" in delta_analysis


def test_given_program_with_changed_FBD_type_delta_shall_list_that(programs_with_clones):
    progBefore, progAfter = programs_with_clones["Calc_Even"]

    assert "DIV" == progAfter.behaviour_id_map[9].data.type
    progAfter.behaviour_id_map[9].data.type = "ADD"
    assert "Block 'DIV' changed to 'ADD'.\nRe-run functional checks" in progBefore.compute_delta(progAfter)


def test_programs_with_added_blocks_in_delta(programs_with_clones):
    progBefore, progAfter = programs_with_clones["Calc_Even"]
