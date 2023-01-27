from antlr4 import InputStream, CommonTokenStream

import MyPOUVisitor
import MyXMLVisitor
from generated import POULexer, POUParser
from generated import XMLLexer, XMLParser

from pathlib import Path


def main():
    inputProgram = Path('test/empty_prog.pou').read_text()
    before_XML_Part = inputProgram.index('<?xml version="1.0" encoding="utf-16" standalone="yes"?>')
    input_varWorkSheet = inputProgram[0:before_XML_Part]
    input_codeSheet = inputProgram[before_XML_Part:].strip("END_PROGRAM")

    SafeProg_VarSheet = parse_variable_worksheet(input_varWorkSheet)
    SafeProg_CodeSheet = parse_code_worksheet(input_codeSheet)
    print(SafeProg_VarSheet)
    print(SafeProg_CodeSheet)

def parse_variable_worksheet(input_varWorkSheet):
    inputDataVarHeader = InputStream(
        input_varWorkSheet
    )
    lexer = POULexer.POULexer(inputDataVarHeader)
    tokens = CommonTokenStream(lexer)
    parser = POUParser.POUParser(tokens)
    tree = parser.safe_program_POU()  # Begin parsing at this rule
    result = MyPOUVisitor.MyPOUVisitor().visitSafe_program_POU(
        tree
    )
    return result
def parse_code_worksheet(input_codeWorkSheet):
    inputDataVarHeader = InputStream(
        input_codeWorkSheet
    )
    lexer = XMLLexer.XMLLexer(inputDataVarHeader)
    tokens = CommonTokenStream(lexer)
    parser = XMLParser.XMLParser(tokens)
    tree = parser.document()  # Begin parsing at this rule
    result = MyXMLVisitor.XMLParserVisitor().visitDocument(
        tree
    )
    return result

if __name__ == "__main__":
    main()
