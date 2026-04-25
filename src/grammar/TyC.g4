grammar TyC;

@lexer::header {
from lexererr import *
}

// ---------------------------------------------------------
// PARSER RULES
// ---------------------------------------------------------

program : (structDecl | funcDecl)* EOF ;

structDecl : STRUCT ID LBRACE structMember* RBRACE SEMI ;

structMember : typeSpec ID SEMI ;

funcDecl
    : typeSpec ID LP paramList? RP block # TypeFuncDecl
    | ID LP paramList? RP block          # InferredFuncDecl
    ;

paramList : param (COMMA param)* ;

param : typeSpec ID ;

block : LBRACE stmt* RBRACE ;

stmt
    : varDecl SEMI
    | ifStmt
    | whileStmt
    | forStmt
    | switchStmt
    | assignStmt
    | breakStmt
    | continueStmt
    | returnStmt
    | expr SEMI
    | block
    ;

varDecl : typeSpec ID (ASSIGN expr)? ;

lhs
    : ID
    | lhs DOT ID
    ;

ifStmt : IF LP expr RP stmt (ELSE stmt)? ;

whileStmt : WHILE LP expr RP stmt ;

forStmt : FOR LP forInit? SEMI expr? SEMI forUpdate? RP stmt ;

forInit : varDecl | expr ;

forUpdate : assignStmt | expr ;

assignStmt : operand ;

switchStmt : SWITCH LP expr RP LBRACE caseBlock* defaultBlock? RBRACE ;

caseBlock : CASE expr COLON stmt* ;

defaultBlock : DEFAULT COLON stmt* ;

breakStmt : BREAK SEMI ;

continueStmt : CONTINUE SEMI ;

returnStmt : RETURN expr? SEMI ;

argList : LP (expr (COMMA expr)*)? RP ;

expr
    : lhs ASSIGN expr
    | expr0
    ;

expr0
    : expr1
    | expr0 OR expr1
    ;

expr1
    : expr2
    | expr1 AND expr2
    ;

expr2
    : expr3
    | expr2 (EQ | NEQ) expr3
    ;

expr3
    : expr4
    | expr3 (LT | LE | GT | GE) expr4
    ;

expr4
    : expr5
    | expr4 (ADD | SUB) expr5
    ;

expr5
    : expr6
    | expr5 (MUL | DIV | MOD) expr6
    ;

expr6
    : (ADD | SUB | NOT | INC | DEC) expr6
    | expr7
    ;

expr7 : operand (INC | DEC)? ;

operand
    : literal                           # LiteralOperand
    | lhs                               # LhsOperand
    | ID argList                        # FunctionCallOperand
    | LP expr RP                        # ParenthesizedOperand
    | LBRACE argList? RBRACE            # StructLiteralOperand
    ;

literal : INTLIT | FLOATLIT | BOOLLIT | STRINGLIT ;

typeSpec : INT | FLOAT | BOOL | STRING | VOID | ID | AUTO ;

// ---------------------------------------------------------
// LEXER RULES
// ---------------------------------------------------------

AUTO: 'auto';
BREAK: 'break';
CONTINUE: 'continue';
CASE: 'case';
DEFAULT: 'default';
ELSE: 'else';
FOR: 'for';
IF: 'if';
RETURN: 'return';
STRUCT: 'struct';
SWITCH: 'switch';
WHILE: 'while';
INT: 'int';
FLOAT: 'float';
BOOL: 'bool';
STRING: 'string';
VOID: 'void';

BOOLLIT: 'true' | 'false';

ADD: '+';
SUB: '-';
MUL: '*';
DIV: '/';
MOD: '%';
OR: '||';
AND: '&&';
NOT: '!';
INC: '++';
DEC: '--';
EQ: '==';
NEQ: '!=';
LT: '<';
LE: '<=';
GT: '>';
GE: '>=';
ASSIGN: '=';

ID: [a-zA-Z_][a-zA-Z_0-9]*;
INTLIT: [0-9]+;
FLOATLIT: [0-9]+ '.' [0-9]* | '.' [0-9]+ ;

STRINGLIT: '"' (ESC | STR_CHAR)* '"' { self.text = self.text[1:-1] } ;

DOT: '.';
COLON: ':';
SEMI: ';';
COMMA: ',';
LP: '(';
RP: ')';
LBRACE: '{';
RBRACE: '}';

fragment ESC: '\\' [btnfr"'\\] ;
fragment STR_CHAR: ~["\\\r\n] ;

WS: [ \t\r\n]+ -> skip ;
LINE_COMMENT: '//' ~[\r\n]* -> skip ;
BLOCK_COMMENT: '/*' .*? '*/' -> skip ;

// Error Fallbacks (bound to the Python exceptions found in your generated code)
ILLEGAL_ESCAPE: '"' (ESC | STR_CHAR)* '\\' ~[btnfr"'\\] { raise IllegalEscape(self.text[1:]) } ;
UNCLOSE_STRING: '"' (ESC | STR_CHAR)* { raise UncloseString(self.text[1:]) } ;
ERROR_CHAR: . { raise ErrorToken(self.text) } ;