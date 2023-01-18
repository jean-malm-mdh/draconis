grammar POU;
options {
    language=Python3;
}
@header {
}

TYPE : 'UINT' | 'SAFEUINT' ;

safe_program_POU: 'PROGRAM' ID variableHeader CODE_SHEET? 'END_PROGRAM' EOF ;

variableHeader : '{' 'VariableWorksheet' ':=' '\'Variables\'' '}' groupDefs vars+ ;

CODE_SHEET : '{' 'CodeWorksheet' ':=' '\'' ID '\'' ',' 'Type' ':=' '\'' ID '\'' '}' ;

VAR_TYPE : 'VAR_INPUT' | 'VAR_OUTPUT' | 'VAR' ;

vars : VAR_TYPE '{' 'Group' '(' groupNr=INT  ')' '}' varLine* 'END_VAR' ;

varLine : '{' 'LINE' '(' lineNr=INT ')' '}' varName=ID ':' varType=TYPE (':=' INT)? ';' varDesc=DESCRIPTION? ;

groupDefs : groupDef+ ;

groupDef : '{' 'GroupDefinition' '(' groupID=INT ',' '\'' groupName=ID '\'' ')' '}' ;

NEWLINE : [\n\r]+ -> skip;

WHITESPACE : [ \t]+ -> skip ;

INT     : [0-9]+ ;

ID      : [a-zA-Z][a-zA-Z0-9]* ;


DESCRIPTION : '(*' .*? '*)' ; // TODO: Will currently not allow '*' or ')' alone in description