from antlr4 import InputStream, CommonTokenStream

import MyPOUVisitor
import MyXMLVisitor
from generated import POULexer, POUParser
from generated import XMLLexer, XMLParser

from pathlib import Path


def test_xml_parsing():
    inputText = \
        """<?xml version="1.0" encoding="utf-16" standalone="yes"?>
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
        </FBD>"""
    elements = parse_code_worksheet(inputText)
    for e in elements:
        print(e)
        print("---")


def main():
    inputProgram = Path("test/smallprog.pou").read_text()
    before_XML_Part = inputProgram.index(
        '<?xml version="1.0" encoding="utf-16" standalone="yes"?>'
    )
    input_varWorkSheet = inputProgram[0:before_XML_Part]
    input_codeSheet = inputProgram[before_XML_Part:].strip("END_PROGRAM")

    SafeProg_VarSheet = parse_variable_worksheet(input_varWorkSheet)
    # SafeProg_CodeSheet = parse_code_worksheet(input_codeSheet)
    print(SafeProg_VarSheet)
    # print(SafeProg_CodeSheet)

    test_xml_parsing()


def parse_variable_worksheet(input_varWorkSheet):
    inputDataVarHeader = InputStream(input_varWorkSheet)
    lexer = POULexer.POULexer(inputDataVarHeader)
    tokens = CommonTokenStream(lexer)
    parser = POUParser.POUParser(tokens)
    tree = parser.safe_program_POU()  # Begin parsing at this rule
    result = MyPOUVisitor.MyPOUVisitor().visitSafe_program_POU(tree)
    return result


def parse_code_worksheet(input_codeWorkSheet):
    inputDataVarHeader = InputStream(input_codeWorkSheet)
    lexer = XMLLexer.XMLLexer(inputDataVarHeader)
    tokens = CommonTokenStream(lexer)
    parser = XMLParser.XMLParser(tokens)
    tree = parser.document()  # Begin parsing at this rule
    visitor = MyXMLVisitor.MyXMLVisitor()
    visitor.visitDocument(tree)
    return visitor.elements


if __name__ == "__main__":
    main()
