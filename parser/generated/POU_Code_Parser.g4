// Adapted from example provided by "The Definitive ANTLR 4 Reference: 2nd Edition
parser grammar POU_Code_Parser;
options {
tokenVocab=POU_Code_Lexer;
language=Python3; }

codeSheet : prolog misc* element misc* ;

prolog : XMLDeclOpen attribute* SPECIAL_CLOSE ;

content : chardata? ((element | reference | CDATA | PI | COMMENT) chardata?)* ;

element : '<' Name attribute* '>' content '<' '/' Name '>'
        | '<' Name attribute* '>'
        ;
reference : EntityRef | CharRef ;

attribute : Name '=' STRING ;

chardata : TEXT | SEA_WS ;

misc    : COMMENT | PI | SEA_WS ;
