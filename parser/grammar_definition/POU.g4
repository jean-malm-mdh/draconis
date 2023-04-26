grammar POU;

WS      : [ \t\r\n]+ -> skip ;

INT     : [-]?[0-9]+ ;

ID      : [a-zA-Z][a-zA-Z0-9_]* ;

FILE_EXT: [.][a-zA-Z0-9_]+ ;

DESCRIPTION : '(*' .*? '*)' ;

safe_program_POU: pou_type ID varWS=variableWorkSheet codeWorkSheet EOF ;

pou_type: 'PROGRAM' | 'FUNCTION_BLOCK' ;

codeWorkSheet : '{' 'CodeWorksheet' ':=' '\'' ID '\'' ',' 'Type' ':=' '\'' FILE_EXT '\'' '}' ;

variableWorkSheet : '{' 'VariableWorksheet' ':=' '\'Variables\'' '}' varGroups  ;

varGroups : groupDefs varDefGroups ;

groupDefs : groupDef+ ;

groupDef : '{' 'GroupDefinition' '(' groupID=INT ',' '\'' groupName=ID '\'' ')' '}' ;

varDefGroups : varDefGroup+ ;

varDefGroup : varType=var_type '{' 'Group' '(' groupNr=INT  ')' '}' varLine* 'END_VAR' ;

varLine : '{' 'LINE' '(' lineNr=INT ')' '}' varName=ID ':' valueType=val_Type (':=' initVal=INT)? ';' (varDesc=DESCRIPTION)? ;

val_Type :  'INT'
            | 'UINT'
            | 'SAFEUINT'
            ;

var_type :  'VAR'
            | 'VAR_INPUT'
            | 'VAR_OUTPUT'
            ;