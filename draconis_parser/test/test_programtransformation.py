import os.path
import sys

import pytest

from AST import Program
from utility_classes.utility_functions import dropWhile

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import re

def compare_strings_ignore_ws(expected: str, actual: str):
    assert (actual == expected) or (
    re.sub(r"[ \t\n\r]", "", actual) == re.sub(r"[ \t\n\r]", "", expected)
    )


def transform_to_ST(prog: Program):
    def path_to_ST_expression(path):
        """

        Args:
            path: The path to generate expression for

        Returns:
            ST representation of the path
        """

        def consume_path_within_block(block, _path):
            """

            Args:
                block: The related block
                _path: The path to remove from

            Returns:
                The path starting from the first element not connected to the block
            """
            blockID = block.getID()
            return dropWhile(
                _path, lambda portID: prog.ports[portID].blockID == blockID
            )

        potential_block = prog.behaviour_id_map[prog.ports[path[0]].blockID]
        if potential_block.getBlockType() == "FunctionBlock":
            # Recursive case
            _path = dropWhile(
                path[1:],
                lambda e: not (
                        "PathDivide" in str(e.__class__) or "Block" in str(e.__class__)
                ),
            )
            if "PathDivide" in str(_path[0].__class__):
                pathdivide_paths = _path[0].paths
                # Recursive call for each path
                args_in_ST_form = map(
                    lambda p: path_to_ST_expression(
                        consume_path_within_block(potential_block, p)
                    ),
                    pathdivide_paths,
                )
                arglist = ", ".join(args_in_ST_form)
            else:
                arglist = path_to_ST_expression(_path)
            return f"{potential_block.data.type}({arglist})"
        else:
            return potential_block.getVarExpr()

    def outputs_to_ST_statements():
        out_dataflow = prog.getBackwardTrace()
        if not out_dataflow:
            return ""
        result = ""
        for outVar, path in out_dataflow.items():
            result += "\t" + f"{outVar} := "
            # Remove output variable from path list
            _path = path[1:]
            result += f"{path_to_ST_expression(_path)};\n"

        return result

    varheader_transform_to_st = prog.varHeader.transform_to_ST()
    outputs_to_st_statements = outputs_to_ST_statements()
    return f"""
            Function_Block {prog.progName}
            {varheader_transform_to_st}
            {outputs_to_st_statements}
            End_Function_Block"""

@pytest.fixture(scope="session", autouse=True)
def programs():
    from draconis_parser.helper_functions import parse_pou_file
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
    compare_strings_ignore_ws(expected, transform_to_ST(programs["empty"]))

def test_given_program_with_only_inouts_ST_transformation_only_outputs_variable_list(programs):
    expected = \
"""
Function_Block Main
\tVar_Input N : UINT := 1; (*Collatz Input*) End_Var
\tVar_Output Result_Even : UINT := 0; (*Result if the input is an even number*) End_Var

End_Function_Block
"""
    compare_strings_ignore_ws(expected, transform_to_ST(programs["no_statement_prog"]))

def test_given_small_program_ST_transformation_outputs_everything(programs):
    expected = \
"""
Function_Block Collatz_Calculator_Even
Var_Input N : UINT := 1; (*Collatz Input*) End_Var
Var_Output Result_Even : UINT := 0; (*Result if the input is an even number*) End_Var

Result_Even := DIV(N, UINT#2);
End_Function_Block
"""
    compare_strings_ignore_ws(expected, transform_to_ST(programs["Calc_Even"]))

    expected = \
"""
Function_Block Collatz_Calculator_Odd
Var_Input N : UINT := 1; (* Collatz Input*) End_Var
Var_Output Result_Odd : UINT := 0; (*Result if the input is an odd number*) End_Var

Result_Odd := ADD(MUL(N, UINT#3), UINT#1);
End_Function_Block
"""
    compare_strings_ignore_ws(expected, transform_to_ST(programs["Calc_Odd"]))



