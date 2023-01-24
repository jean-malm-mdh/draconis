from antlr4 import InputStream, CommonTokenStream

import MyPOUVisitor
from generated import POULexer, POUParser


def main():
    inputData = InputStream(
        """PROGRAM Main
        { VariableWorksheet := 'Variables' }
        {GroupDefinition(0, 'Inputs')}
        {GroupDefinition(2, 'Outputs')}
        
        VAR_INPUT
        {Group(0)}
        END_VAR

        VAR_OUTPUT
        {Group(0)}
        END_VAR

        VAR
        {Group(0)}
        {LINE(1)}
        Input1: UINT := 0;
        (*FirstUIntDesc *)
        END_VAR
        
        
        VAR_INPUT
        {Group(2)}
        END_VAR

        VAR_OUTPUT
        {Group(2)}
        END_VAR

        VAR
        {Group(2)}
        {LINE(3)}
        Input2: UINT := 42;
        (*Second UINT *)
        END_VAR
        END_PROGRAM"""
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
