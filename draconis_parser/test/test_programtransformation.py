import os.path
import sys

import pytest

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import re

def compare_strings_ignore_ws(expected: str, actual: str):
    assert (actual == expected) or (
    re.sub(r"[ \t\n\r]", "", actual) == re.sub(r"[ \t\n\r]", "", expected)
    )

@pytest.fixture(scope="session", autouse=True)
def programs():
    from helper_functions import parse_pou_file
    testDir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "")
    programs = dict(
        [
            (n, parse_pou_file(p))
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
                ("empty", f"{testDir}/empty_prog.pou"),
                ("empty_no_proper_groups", f"{testDir}/empty_prog_no_groups.pou"),
                ("no_statement_prog", f"{testDir}/no_statement_prog.pou"),
            ]
        ]
    )
    return programs

def test_given_empty_program_ST_transformation_only_outputs_boilerplate(programs):
    expected = \
"""
Function_Block Main

End_Function_Block
"""
    compare_strings_ignore_ws(expected, programs["empty"].transform_to_ST())

def test_given_program_with_only_inouts_ST_transformation_only_outputs_variable_list(programs):
    expected = \
"""
Function_Block Main
\tVar_Input N : UINT := 1; (*Collatz Input*) End_Var
\tVar_Output Result_Even : UINT := 0; (*Result if the input is an even number*) End_Var

End_Function_Block
"""
    compare_strings_ignore_ws(expected, programs["no_statement_prog"].transform_to_ST())

def test_given_small_program_ST_transformation_outputs_everything(programs):
    expected = \
"""
Function_Block Collatz_Calculator_Even
Var_Input N : UINT := 1; (*Collatz Input*) End_Var
Var_Output Result_Even : UINT := 0; (*Result if the input is an even number*) End_Var

Result_Even := DIV(N, UINT#2);
End_Function_Block
"""
    compare_strings_ignore_ws(expected, programs["Calc_Even"].transform_to_ST())

    expected = \
"""
Function_Block Collatz_Calculator_Odd
Var_Input N : UINT := 1; (* Collatz Input*) End_Var
Var_Output Result_Odd : UINT := 0; (*Result if the input is an odd number*) End_Var

Result_Odd := ADD(MUL(N, UINT#3), UINT#1);
End_Function_Block
"""
    compare_strings_ignore_ws(expected, programs["Calc_Odd"].transform_to_ST())



