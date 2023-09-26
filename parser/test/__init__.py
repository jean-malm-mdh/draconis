import pytest
import os
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
                ("feedback_example", f"{testDir}/Feedback_Exampple.pou"),
                ("feedback_example_misaligned_networks", f"{testDir}/Feedback_Exampple_misaligned_networks.pou")
            ]
        ]
    )
    return programs