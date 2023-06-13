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

valTypeRule : INT | 'SAFETRUE' | 'SAFEFALSE' ;
feedbackRule : '{' 'Feedback' '(' 'true' ')' '}' ;

varLine : '{' 'LINE' '(' lineNr=INT ')' '}' varName=ID ':' valueType=val_Type (':=' initVal=valTypeRule)? (isFeedback=feedbackRule)? ';' (varDesc=DESCRIPTION)? ;

val_Type : elementary_type | derived_type | generic_type | safe_type | custom_type=ID  ;
elementary_type: 'ANALOG'
                | 'BOOL'
                | 'BYTE'
                | 'WORD'
                | 'DWORD'
                | 'LWORD'
                | 'SINT'
                | 'INT'
                | 'DINT'
                | 'LINT'
                | 'USINT'
                | 'UINT'
                | 'UDINT'
                | 'ULINT'
                | 'REAL'
                | 'LREAL'
                | 'TIME'
                | 'DATE'
                | 'DT'
                | 'TOD'
                | 'STRING'
                | 'WSTRING';

safe_type:      'SAFEANALOG'
               | 'SAFEBOOL'
               | 'SAFEBYTE'
               | 'SAFEDINT'
               | 'SAFEDWORD'
               | 'SAFEINT'
               | 'SAFESINT'
               | 'SAFETIME'
               | 'SAFEUDINT'
               | 'SAFEUINT'
               | 'SAFEUSINT'
               | 'SAFEWORD' ;

derived_type:   'ARRAY'
                | 'DERIVED'
                | 'ENUM'
                | 'SUBRANGESIGNED'
                | 'SUBRANGEUNSIGNED'
                | 'STRUCT';

generic_type:   'ANY'
                | 'ANY_DERIVED'
                | 'ANY_ELEMENTARY'
                | 'ANY_MAGNITUDE'
                | 'ANY_NUM'
                | 'ANY_REAL'
                | 'ANY_INT'
                | 'ANY_BIT'
                | 'ANY_STRING'
                | 'ANY_DATE';

var_type :  'VAR'
            | 'VAR_INPUT'
            | 'VAR_OUTPUT'
            ;