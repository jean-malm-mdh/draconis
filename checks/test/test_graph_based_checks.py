from checks.graph_based_checks import program_to_graph
import os
import pytest
from parser.helper_functions import parse_pou_file
@pytest.fixture(scope="session", autouse=True)
def programs():
    testDir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../../parser/test")
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
                ("empty_no_proper_groups", f"{testDir}/empty_prog_no_groups.pou"),
            ]
        ]
    )
    return programs
