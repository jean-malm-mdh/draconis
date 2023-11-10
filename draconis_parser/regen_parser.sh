#!/usr/bin/env bash
ANTLR_GEN_DIR="antlr_generated"
rm -fr "$ANTLR_GEN_DIR"

# ANTLR seems to behave oddly when using relative pathing to access them
# To get around this, we generate the files local to the grammar, then move the folder at the end
pushd grammar_definition > /dev/null || exit
ANTLR_PY_GEN_DIR="$ANTLR_GEN_DIR/python"
antlr4 -visitor -Dlanguage=Python3 -o "$ANTLR_PY_GEN_DIR" XMLLexer.g4
antlr4 -visitor -Dlanguage=Python3 -o "$ANTLR_PY_GEN_DIR" XMLParser.g4
antlr4 -visitor -Dlanguage=Python3 -o "$ANTLR_PY_GEN_DIR" POU.g4
#################################
# Build the __init__.py file here
#################################
echo "" > "./$ANTLR_PY_GEN_DIR/__init__.py"

# Move all the generated files to their actual location
mv "$ANTLR_GEN_DIR" "../"
git add -f "../$ANTLR_GEN_DIR"
popd > /dev/null || exit