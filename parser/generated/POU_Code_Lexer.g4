// Adapted from example provided by "The Definitive ANTLR 4 Reference: 2nd Edition
lexer grammar POU_Code_Lexer;
options {
    language=Python3;
}
COMMENT : '<!--' .*? '-->' ;

CDATA : '<![CDATA[' .*? ']]>' ;

DTD     : '<!' .*? '>'  -> skip ;

EntityRef : '&' Name ';' ;

CharRef : '&#' DIGIT+ ';'
        | '&#x' HEXDIGIT+ ';'
        ;

SEA_WS  : (' ' | '\t' | '\r'? '\n') ;

OPEN    : '<'   -> pushMode(INSIDE) ;

XMLDeclOpen : '<?xml' S     -> pushMode(INSIDE) ;

SPECIAL_OPEN : '<?' Name    -> more, pushMode(PROC_INSTR) ;

TEXT        : ~[<&]+ ;  // Match 16 bit character except '<' and '&'

mode PROC_INSTR;
PI  : '?>'  -> popMode  ; // closing <?...?>
IGNORE  : . -> more ;

mode INSIDE;

CLOSE   : '>'   -> popMode ;
SPECIAL_CLOSE: '?>' -> popMode ;
SLASH_CLOSE:    '/>' -> popMode ;
SLASH       : '/' ;
EQUALS      : '=' ;
STRING      : '"' ~[<"]* '"'
            | '\'' ~[<']* '\''
            ;
Name        : NameStartChar NameChar* ;
S           : [ \t\r\n]             -> skip ;

fragment
HEXDIGIT    : [a-fA-F0-9] ;

fragment
DIGIT       : [0-9] ;

fragment
NameChar    : NameStartChar
            | '-' | '.' | DIGIT
            ;

fragment
NameStartChar : [:a-zA-Z] ;



