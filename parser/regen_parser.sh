ANTLR_GEN_DIR="antlr_generated"
rm -fr "$ANTLR_GEN_DIR"

# ANTLR seems to behave oddly when using relative pathing to access them
# To get around this, we generate the files local to the grammar, then move the folder at the end
pushd grammar_definition > /dev/null || exit
antlr4 -visitor -Dlanguage=Python3 -o "$ANTLR_GEN_DIR/python" XMLLexer.g4
antlr4 -visitor -Dlanguage=Python3 -o "$ANTLR_GEN_DIR/python" XMLParser.g4
antlr4 -visitor -Dlanguage=Python3 -o "$ANTLR_GEN_DIR/python" POU.g4
#################################
# Build the __init__.py file here
#################################
echo "" > "./$ANTLR_GEN_DIR/python/__init__.py"

# Move all the generated files to their actual location
mv "$ANTLR_GEN_DIR" "../"
popd || exit
#antlr_j XMLLexer.g4
#antlr_j XMLParser.g4
#antlr_j POU.g4
#javac *.java