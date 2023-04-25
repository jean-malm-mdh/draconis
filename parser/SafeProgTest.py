import os.path
import sys

import pytest

from parser import SafeProgAST
from parser.SafeProgAST import DataflowDir, SafeClass

sys.path.append(os.path.dirname(__file__))
import helper_functions

# TODO(TDD):
#  It shall be possible to check if functions depend on internal variables/state
#  It shall be possible to trace the path of a output backwards
#  * It shall be possible to trace any value in any direction

@pytest.fixture(scope="session", autouse=True)
def programs():
    programs = dict([(n, helper_functions.parse_pou_file(p)) for n, p in
                [("Calc_Odd", "test/Collatz_Calculator_Odd.pou"),
                 ("Calc_Even", "test/Collatz_Calculator_Even.pou"),
                 ("Calc_Even_SafeVer", "test/Collatz_Calculator_Even_Safe.pou")
                 ]])
    return programs
def test_given_a_file_can_extract_numeric_metrics(programs):
    metrics = programs["Calc_Odd"].getMetrics()
    assert metrics["NrOfVariables"] == 2
    assert metrics["NrOfFuncBlocks"] == 2
    assert metrics["NrInputVariables"] == 1
    assert metrics["NrOutputVariables"] == 1

def test_given_a_name_can_get_variable_info_by_name(programs):
    info = programs["Calc_Even"].getVarInfo()
    assert str(info["OutputVariables"].get("Result_Even", None)).replace("'", "").replace('"', "") == \
           "Var(UINT Result_Even: OutputVar = 0; Description: Result if the input is an even number)"
    assert str(info["InputVariables"].get("N", None)).replace("'", "").replace('"', "") == \
           "Var(UINT N: InputVar = 1; Description: Collatz Input)"
    assert len(info["InternalVariables"]) == 0

def test_given_program_can_extract_names_and_descriptions(programs):
    program = programs["Calc_Even"]
    """Basic functionality"""
    assert program.getVarDataColumns("name") == [["N"], ["Result_Even"]]
    assert program.getVarDataColumns("name", "description") == [["N", "Collatz Input"], ["Result_Even", "Result if the input is an even number"]]
    assert program.getVarDataColumns("description", "name") == [["Collatz Input", "N"], ["Result if the input is an even number", "Result_Even"]]

    """Boundary Values"""
    varInfo_noSpecifiedFields = program.getVarDataColumns()
    assert varInfo_noSpecifiedFields == [['N', "InputVar", "UINT", "1", "Collatz Input", "1"], ["Result_Even", "OutputVar", "UINT", '0', 'Result if the input is an even number', "3"]]

    varInfo_AllSpecifiedFields = program.getVarDataColumns("name", "varType", "valueType", "initVal", "description", "lineNr")
    assert varInfo_AllSpecifiedFields == [['N', "InputVar", "UINT", "1", "Collatz Input", "1"],
                                          ["Result_Even", "OutputVar", "UINT", '0', 'Result if the input is an even number', "3"]]

def path_assert_helper(expected, actual):
    for i in range(len(expected)):
        a = actual[i]
        e = expected[i]
        if "PathDivide" in str(type(e)) and "PathDivide" in str(type(a)):
            path_assert_helper(e.paths, a.paths)
        else:
            assert (e == a)
    return True

def test_from_output_can_perform_simple_backward_traces(programs):
    expected = [5, 9, 8, SafeProgAST.PathDivide([[6, 3], [7, 4]])]
    actual = programs["Calc_Even"].getTrace(DataflowDir.Backward)["Result_Even"]
    assert actual == expected
def test_from_input_can_perform_simple_forward_traces(programs):
    expected = [[3, 6, 8, 9, 5]]
    actual = programs["Calc_Even"].getTrace(DataflowDir.Forward)["N"]
    assert actual == expected

def test_can_classify_expression_safeness_by_name(programs):
    assert SafeClass.Unsafe == programs["Calc_Even"].getVarInfo()["Safeness"]["Result_Even"]
    assert SafeClass.Unsafe == programs["Calc_Even"].getVarInfo()["Safeness"]["N"]

    assert SafeClass.Safe == programs["Calc_Even_SafeVer"].getVarInfo()["Safeness"]["N"]



def print_xml_parsing():
    inputText = """
  <?xml version="1.0" encoding="utf-16" standalone="yes"?>
  <FBD>
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
    </FBD>"""
    elements = helper_functions.parse_code_worksheet(inputText)
    for e in elements:
        print(e)


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
    input_varWorkSheet, input_codeSheet = helper_functions.get_worksheets_from_input(inputProgram)
    program = helper_functions.parse_variable_worksheet(input_varWorkSheet)
    program.behaviourElements, program.behaviour_id_map = helper_functions.parse_code_worksheet(
        input_codeSheet
    )
    assert program.getMetrics()["NrOfVariables"] == 2
    assert program.getMetrics()["NrOfFuncBlocks"] == 1

def main():
    pass


if __name__ == "__main__":
    main()
