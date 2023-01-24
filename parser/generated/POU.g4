grammar POU;
options {
    language=Python3;
}
@header {
}


safe_program_POU: 'PROGRAM' ID varWS=variableWorkSheet codeWorkSheet? 'END_PROGRAM' EOF ;

variableWorkSheet : '{' 'VariableWorksheet' ':=' '\'Variables\'' '}' varGroups  ;

varGroups : groupDefs varDefGroups ;

groupDefs : groupDef+ ;

groupDef : '{' 'GroupDefinition' '(' groupID=INT ',' '\'' groupName=ID '\'' ')' '}' ;

varDefGroups : varDefGroup+ ;

varDefGroup : varType=VAR_TYPE '{' 'Group' '(' groupNr=INT  ')' '}' varLine* 'END_VAR' ;

varLine : '{' 'LINE' '(' lineNr=INT ')' '}' varName=ID ':' valueType=TYPE ':=' initVal=INT ';' varDesc=DESCRIPTION? ;


codeWorkSheet : '{' 'CodeWorksheet' ':=' '\'' ID '\'' ',' 'Type' ':=' '\'' ID '\'' '}' ;


NEWLINE : [\n\r]+ -> skip;

WHITESPACE : [ \t]+ -> skip ;

INT     : [0-9]+ ;

ID      : [a-zA-Z][a-zA-Z0-9]* ;

TYPE :  'UINT'
        | 'SAFEUINT' ;

VAR_TYPE :  'VAR'
            | 'VAR_INPUT'
            | 'VAR_OUTPUT'
            ;

DESCRIPTION : '(*' .*? '*)' ; // TODO: Will currently not allow '*' or ')' alone in description