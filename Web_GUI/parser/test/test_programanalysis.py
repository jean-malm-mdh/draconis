import json
import os.path
import sys

import pytest

from Web_GUI.parser.AST.ast_typing import SafeClass

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
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
                ("empty_no_proper_groups", f"{testDir}/empty_prog_no_groups.pou"),
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
        ["N", "InputVar", "UINT", "1", "Collatz Input", "False"],
        [
            "Result_Even",
            "OutputVar",
            "UINT",
            "0",
            "Result if the input is an even number",
            "False",
        ],
    ]

    varInfo_AllSpecifiedFields = program.getVarDataColumns(
        "name", "paramType", "valueType", "initVal", "description", "isFeedback"
    )
    assert varInfo_AllSpecifiedFields == [
        ["N", "InputVar", "UINT", "1", "Collatz Input", "False"],
        [
            "Result_Even",
            "OutputVar",
            "UINT",
            "0",
            "Result if the input is an even number",
            "False",
        ],
    ]


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
    program.behaviourElements, program.behaviour_id_map, *_ = parse_code_worksheet(
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


def test_given_program_can_convert_to_json(programs):
    for prog in programs.values():
        json_val = prog.toJSON()
        d = json.loads(json_val)
        assert d["progName"] == prog.progName


def main():
    pass


if __name__ == "__main__":
    main()
