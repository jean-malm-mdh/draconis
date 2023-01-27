pushd generated > /dev/null
mv "__init__.py" "__init__.py.g4" > /dev/null
find . -type f ! -name "*.g4" -delete
mv "__init__.py.g4" "__init__.py"
antlr4 -visitor -Dlanguage=Python3 XMLLexer.g4
antlr4 -visitor -Dlanguage=Python3 XMLParser.g4
antlr_j XMLLexer.g4
antlr_j XMLParser.g4
antlr4 -visitor -Dlanguage=Python3 POU.g4
antlr_j POU.g4
javac *.java
popd > /dev/null
