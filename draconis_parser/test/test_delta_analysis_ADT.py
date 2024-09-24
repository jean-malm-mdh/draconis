from Web_GUI import Point

import pytest

import sys
import os
import re

from draconis_parser.helper_functions import parse_pou_file
from utility_classes.delta import Delta, ChangeType
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
def test_given_program_with_variable_changes_list_of_deltas_shall_return_change_class(
        programs_with_clones,
):
    prog = programs_with_clones["Calc_Even"][0]
    prog_changed = programs_with_clones["Calc_Even_SafeVer"][0]

    expected = Delta.Create(ChangeType.MODIFICATION,
                            prog.getVarByName("Result_Even"),
                            prog_changed.getVarByName("Result_Even"))
    actual = prog.compute_deltas2(prog_changed)
    assert expected in actual


def test_addition_delta_reporting(
        programs_with_clones
):
    prog = programs_with_clones["MultiAND"][0]
    prog_addition = programs_with_clones["MultiANDAddedVariable"][0]
    expected = Delta.CreateAddition(prog_addition.getVarByName("IsInSafeState"))
    actual = prog.compute_deltas2(prog_addition)

    assert expected in actual


def test_given_a_change_it_shall_be_possible_to_summarize_differences(
        programs_with_clones
):
    prog = programs_with_clones["Calc_Even"][0]
    prog_changed = programs_with_clones["Calc_Even_SafeVer"][0]

    delta_info = Delta.Create(ChangeType.MODIFICATION,
                              prog.getVarByName("Result_Even"),
                              prog_changed.getVarByName("Result_Even"))
    info = delta_info.summarize()
    assert "The following properties have been modified for variable 'Result_Even'" in info
    assert "valueType: UINT => SAFEUINT" in info


def test_change_reporting_is_order_dependent(
        programs_with_clones
):
    prog = programs_with_clones["Calc_Even"][0]
    prog_changed = programs_with_clones["Calc_Even_SafeVer"][0]

    # Swapping the order of the objects
    delta_info = Delta.Create(ChangeType.MODIFICATION,
                              prog_changed.getVarByName("Result_Even"),
                              prog.getVarByName("Result_Even"))
    info = delta_info.summarize()
    assert "The following properties have been modified for variable 'Result_Even'" in info
    # Swaps the ordering of the property value printout
    assert "valueType: SAFEUINT => UINT" in info


def test_addition_reporting(
        programs_with_clones
):
    prog_addition = programs_with_clones["MultiANDAddedVariable"][0]
    actual = Delta.CreateAddition(prog_addition.getVarByName("IsInSafeState")).summarize()

    assert "VariableLine IsInSafeState was added" in actual


def test_deletion_reporting(
        programs_with_clones
):
    prog_addition = programs_with_clones["MultiANDAddedVariable"][0]
    actual = Delta.CreateDeletion(prog_addition.getVarByName("IsInSafeState")).summarize()

    assert "VariableLine IsInSafeState was removed" in actual

