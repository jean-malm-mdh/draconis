from antlr4 import InputStream, CommonTokenStream

import MyPOUVisitor
from generated import POULexer, POUParser

from pathlib import Path

def main():
    input = Path('test/smallprog.pou').read_text()
    inputData = InputStream(
        input
    )
    lexer = POULexer.POULexer(inputData)
    tokens = CommonTokenStream(lexer)
    parser = POUParser.POUParser(tokens)
    tree = parser.safe_program_POU()  # Begin parsing at this rule
    result = MyPOUVisitor.MyPOUVisitor().visitSafe_program_POU(
        tree
    )  # Pretty-print the result to a string
    print(result)


if __name__ == "__main__":
    main()
