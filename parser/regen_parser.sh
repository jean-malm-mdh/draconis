pushd generated > /dev/null
antlr4 -visitor POU_Code_Lexer.g4
antlr4 -visitor POU.g4
popd > /dev/null
