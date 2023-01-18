grammar POU;
options {
    language=Python3;
}
@members {
    s
}
prog:	'PROGRAM' ID VariableHeader CodeSheet 'END_PROGRAM' EOF ;

VariableHeader : WorkSheet GroupDefs VarBlock ;

CodeSheet : '{' SheetType ':=' '\'' ID '\'' ',' 'Type' ':=' '\'' ID '\'' '}' ;

VarBlock : 'VAR_INPUT' | 'VAR_OUTPUT' | 'VAR' ;

SheetType : 'VariableWorksheet' | 'CodeWorksheet' ;

Vars : VarBlock '{' 'Group' '(' INT  ')' '}' VarLine* 'END_VAR' ;

VarLine : '{' 'LINE' '(' INT ')' '}' ID ':' TYPE (':=' INT)? Desc? ; 

WorkSheet : '{' SheetType ':=' '\'' ID '\'' '}' ;

GroupDefs : GroupDef+ ;

GroupDef : '{' 'GroupDefinition' '(' INT ',' '\'' ID '\'' ')' '}' ;

Desc : '(' '*' STRING ; 

expr:	expr ('*'|'/') expr
    |	expr ('+'|'-') expr
    |	INT
    |	'(' expr ')'
    ;

NEWLINE : []+ -> skip;

INT     : [0-9]+ ;

ID      : [a-zA-Z][a-zA-Z0-9]* ;

STRING : STRING_ESCAPE | [ a-zA-Z0-9]* ;

STRING_ESCAPE : '*)' ;