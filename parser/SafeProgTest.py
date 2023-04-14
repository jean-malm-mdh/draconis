from antlr4 import InputStream, CommonTokenStream

import MyPOUVisitor
import MyXMLVisitor
from antlr_generated.python import POULexer, POUParser
from antlr_generated.python import XMLLexer, XMLParser

from pathlib import Path


# Helpers

def get_worksheets_from_input(input_program: str):
    index_start_of_XML = input_program.index(
        '<?xml version="1.0" encoding="utf-16" standalone="yes"?>'
    )
    index_end_of_XML = input_program.index("END_PROGRAM")
    input_varWorkSheet = input_program[0:index_start_of_XML]
    input_codeSheet = input_program[index_start_of_XML:index_end_of_XML]

    return input_varWorkSheet, input_codeSheet



def parse_variable_worksheet(input_varWorkSheet):
    inputDataVarHeader = InputStream(input_varWorkSheet)
    lexer = POULexer.POULexer(inputDataVarHeader)
    tokens = CommonTokenStream(lexer)
    parser = POUParser.POUParser(tokens)
    tree = parser.safe_program_POU()  # Begin parsing at this rule
    result = MyPOUVisitor.MyPOUVisitor().visitSafe_program_POU(tree)
    return result


def parse_code_worksheet(input_codeWorkSheet:str):
    """
    Parses the code worksheet defined by the input string
    Returns the elements and an ID map
    """
    inputDataVarHeader = InputStream(input_codeWorkSheet)
    lexer = XMLLexer.XMLLexer(inputDataVarHeader)
    tokens = CommonTokenStream(lexer)
    parser = XMLParser.XMLParser(tokens)
    tree = parser.document()  # Begin parsing at this rule
    visitor = MyXMLVisitor.MyXMLVisitor()
    visitor.visitDocument(tree)
    return visitor.elements, visitor.local_id_map



def parse_pou_file(pou_file_path:str):
    def clean_pou_string(input_pou_prog:str):
        """Removes useless parts of the program before parsing"""
        return input_pou_prog.replace("﻿", "")

    program_string = clean_pou_string(Path(pou_file_path).read_text())
    varSheet, codeSheet = get_worksheets_from_input(program_string)

    resultProgram = parse_variable_worksheet(varSheet)
    resultProgram.behaviourElements, resultProgram.behaviour_id_map = parse_code_worksheet(codeSheet)
    return resultProgram
def print_xml_parsing():
    inputText = """<?xml version="1.0" encoding="utf-16" standalone="yes"?>
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
    elements = parse_code_worksheet(inputText)
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
    input_varWorkSheet, input_codeSheet = \
        get_worksheets_from_input(inputProgram)
    program = parse_variable_worksheet(input_varWorkSheet)
    program.behaviourElements, program.behaviour_id_map = parse_code_worksheet(input_codeSheet)
    assert program.getMetrics()["NrOfVariables"] == 2
    assert program.getMetrics()["NrOfFuncBlocks"] == 1


def main():
    #inputProgram = Path("test/smallprog.pou").read_text()
    #input_varWorkSheet, _ = get_worksheets_from_input(inputProgram)
    # print(parse_variable_worksheet(input_varWorkSheet))

    print_xml_parsing()
    test_metrics_pipeline()

if __name__ == "__main__":
    main()
