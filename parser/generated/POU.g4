grammar POU;
options {
    language=Python3;
}
@header {
}
safe_program_POU: 'PROGRAM' ID VariableHeader? CodeSheet? 'END_PROGRAM' EOF ;

VariableHeader : WorkSheet GroupDefs VarBlock ;

CodeSheet : '{' SheetType ':=' '\'' ID '\'' ',' 'Type' ':=' '\'' ID '\'' '}' ;

VarBlock : 'VAR_INPUT' | 'VAR_OUTPUT' | 'VAR' ;

SheetType : 'VariableWorksheet' | 'CodeWorksheet' ;

Vars : VarBlock '{' 'Group' '(' INT  ')' '}' VarLine* 'END_VAR' ;

VarLine : '{' 'LINE' '(' INT ')' '}' ID ':' TYPE (':=' INT)? Description? ;

WorkSheet : '{' SheetType ':=' '\'' ID '\'' '}' ;

GroupDefs : GroupDef+ ;

GroupDef : '{' 'GroupDefinition' '(' INT ',' '\'' ID '\'' ')' '}' ;

NEWLINE : [\n\r]+ -> skip;

INT     : [0-9]+ ;

ID      : [a-zA-Z][a-zA-Z0-9]* ;

TYPE : 'UINT' | 'SAFEUINT' ;

Description : '(*' ~[*)]* '*)' ; // TODO: Will currently not allow '*' or ')' alone in description