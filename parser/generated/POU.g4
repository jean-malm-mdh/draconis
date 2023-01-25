grammar POU;
options {
    tokenVocab=POU_Code_Lexer;
    language=Python3;
}
import POU_Code_Parser;

safe_program_POU: 'PROGRAM' ID varWS=variableWorkSheet codeWorkSheet? codeSheet 'END_PROGRAM' EOF ;

variableWorkSheet : '{' 'VariableWorksheet' ':=' '\'Variables\'' '}' varGroups  ;

varGroups : groupDefs varDefGroups ;

groupDefs : groupDef+ ;

groupDef : '{' 'GroupDefinition' '(' groupID=INT ',' '\'' groupName=ID '\'' ')' '}' ;

varDefGroups : varDefGroup+ ;

varDefGroup : varType=var_type '{' 'Group' '(' groupNr=INT  ')' '}' varLine* 'END_VAR' ;

varLine : '{' 'LINE' '(' lineNr=INT ')' '}' varName=ID ':' valueType=val_Type (':=' initVal=INT)? ';' (varDesc=DESCRIPTION)? ;


codeWorkSheet : '{' 'CodeWorksheet' ':=' '\'' ID '\'' ',' 'Type' ':=' '\'' FILE_EXT '\'' '}' ;


NEWLINE : [\n\r]+ -> skip;

WHITESPACE : [ \t]+ -> skip ;

INT     : [-]?[0-9]+ ;

ID      : [a-zA-Z][a-zA-Z0-9]* ;

FILE_EXT: [.][a-zA-Z0-9_]+ ;

DESCRIPTION : '(*' .*? '*)' ; // TODO: Will currently not allow '*' or ')' alone in description

val_Type :  'INT'
            | 'UINT'
            | 'SAFEUINT' ;

var_type :  'VAR'
            | 'VAR_INPUT'
            | 'VAR_OUTPUT'
            ;
