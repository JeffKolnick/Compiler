import re

# Define regular expressions for different token types
PATTERN_INT = r'[0-9]+'
PATTERN_DOUBLE = r'[0-9]*\.[0-9]+'
PATTERN_COMP = r'<>|<=|>=|<|>|=='
PATTERN_ADDOP = r'\+|-'
PATTERN_MULOP = r'\*|/|%'
PATTERN_ASSIGN = r'='
PATTERN_SEMICOLON = r';'
PATTERN_COMMA = r','
PATTERN_PERIOD = r'\.'
PATTERN_LPAREN = r'\('
PATTERN_RPAREN = r'\)'
PATTERN_LBRACKET = r'\['
PATTERN_RBRACKET = r'\]'
PATTERN_IF = r'\bif\b'
PATTERN_FI = r'\bfi\b'
PATTERN_THEN = r'\bthen\b'
PATTERN_ELSE = r'\belse\b'
PATTERN_WHILE = r'\bwhile\b'
PATTERN_OR = r'\bor\b'
PATTERN_AND = r'\band\b'
PATTERN_NOT = r'\bnot\b'
PATTERN_DO = r'\bdo\b'
PATTERN_OD = r'\bod\b'
PATTERN_PRINT = r'\bprint\b'
PATTERN_RETURN = r'\breturn\b'
PATTERN_DEF = r'\bdef\b'
PATTERN_FED = r'\bfed\b'
PATTERN_INT_TYPE = r'\bint\b'
PATTERN_DOUBLE_TYPE = r'\bdouble\b'
PATTERN_ID = r'[a-zA-Z_]+[a-zA-Z0-9]*'

KEYWORDS = {
    'if': PATTERN_IF,
    'fi': PATTERN_FI,
    'then': PATTERN_THEN,
    'else': PATTERN_ELSE,
    'while': PATTERN_WHILE,
    'or': PATTERN_OR,
    'and': PATTERN_AND,
    'not': PATTERN_NOT,
    'do': PATTERN_DO,
    'od': PATTERN_OD,
    'print': PATTERN_PRINT,
    'return': PATTERN_RETURN,
    'def': PATTERN_DEF,
    'fed': PATTERN_FED,
    'int': PATTERN_INT_TYPE,
    'double': PATTERN_DOUBLE_TYPE,
}

LITERALS = {
    '+': PATTERN_ADDOP,
    '-': PATTERN_ADDOP,
    '*': PATTERN_MULOP,
    '/': PATTERN_MULOP,
    '%': PATTERN_MULOP,
    '=': PATTERN_ASSIGN,
    ';': PATTERN_SEMICOLON,
    ',': PATTERN_COMMA,
    '.': PATTERN_PERIOD,
    '(': PATTERN_LPAREN,
    ')': PATTERN_RPAREN,
    '[': PATTERN_LBRACKET,
    ']': PATTERN_RBRACKET,
}

# Define a dictionary mapping regular expression patterns to token types

TOKEN_TYPES = {
    PATTERN_INT: 'INT',
    PATTERN_DOUBLE: 'DOUBLE',
    PATTERN_COMP: 'COMP',
    PATTERN_ADDOP: 'ADDOP',
    PATTERN_MULOP: 'MULOP',
    PATTERN_ASSIGN: 'ASSIGN',
    PATTERN_SEMICOLON: 'SEMICOLON',
    PATTERN_COMMA: 'COMMA',
    PATTERN_PERIOD: 'PERIOD',
    PATTERN_LPAREN: 'LPAREN',
    PATTERN_RPAREN: 'RPAREN',
    PATTERN_LBRACKET: 'LBRACKET',
    PATTERN_RBRACKET: 'RBRACKET',
    PATTERN_IF: 'IF',
    PATTERN_FI: 'FI',
    PATTERN_THEN: 'THEN',
    PATTERN_ELSE: 'ELSE',
    PATTERN_WHILE: 'WHILE',
    PATTERN_OR: 'OR',
    PATTERN_AND: 'AND',
    PATTERN_NOT: 'NOT',
    PATTERN_DO: 'DO',
    PATTERN_OD: 'OD',
    PATTERN_PRINT: 'PRINT',
    PATTERN_RETURN: 'RETURN',
    PATTERN_DEF: 'DEF',
    PATTERN_FED: 'FED',
    PATTERN_INT_TYPE: 'INT_TYPE',
    PATTERN_DOUBLE_TYPE: 'DOUBLE_TYPE',
    PATTERN_ID: 'ID',
}

FIRST = {
    '<program>': {'DEF', 'INT_TYPE', 'DOUBLE_TYPE'},
    '<fdecls>': {'DEF', 'ε'},
    '<fdecls\'>': {'DEF', 'ε'},
    '<fdec>': {'DEF'},
    '<params>': {'INT_TYPE', 'DOUBLE_TYPE', 'ε'},
    '<params\'>': {'COMMA', 'ε'},
    '<fname>': {'ID'},
    '<declarations>': {'INT_TYPE', 'DOUBLE_TYPE', 'ID', 'ε'},
    '<declarations\'>': {'INT_TYPE', 'DOUBLE_TYPE', 'ε'},
    '<decl>': {'INT_TYPE', 'DOUBLE_TYPE'},
    '<type>': {'INT_TYPE', 'DOUBLE_TYPE'},
    '<varlist>': {'ID', 'ε'},
    '<varlist\'>': {'COMMA', 'ε'},
    '<statement_seq>': {'ID', 'IF', 'WHILE', 'PRINT', 'RETURN', 'ε'},
    '<statement_seq\'>': {'SEMICOLON', 'ε'},
    '<statement>': {'ID', 'IF', 'WHILE', 'PRINT', 'RETURN', 'ε'},
    '<else_part>': {'ELSE', 'ε'},
    '<expr>': {'ID', 'INT', 'DOUBLE', 'LPAREN'},
    '<expr\'>': {'ADDOP', 'ε'},
    '<term>': {'ID', 'INT', 'DOUBLE', 'LPAREN'},
    '<term\'>': {'MULOP', 'ε'},
    '<factor>': {'LPAREN', 'ID', 'INT', 'DOUBLE',},
    '<exprseq>': {'ID', 'INT', 'DOUBLE', 'LPAREN'},
    '<exprseq\'>': {'COMMA', 'ε'},
    '<bexpr>': {'NOT','LPAREN'},
    '<bexpr\'>': {'OR', 'ε'},
    '<bterm>': {'NOT', 'LPAREN'},
    '<bterm\'>': {'AND', 'ε'},
    '<bfactor>': {'LPAREN', 'NOT'},
    '<comp>': {'COMP'},
    '<var>': {'ID'},
    '<letter>': {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'},
    '<digit>': {'1', '2', '3', '4', '5', '6', '7', '8', '9', '0'},
    '<id>': {'ID'},
    '<id_chars>': {'ID', 'ε'},
    '<number>': {'1', '2', '3', '4', '5', '6', '7', '8', '9', '0'},
}

FOLLOW = {
    '<program>': {'PERIOD'},
    '<fdecls>': {'INT', 'DOUBLE', 'ID', "PERIOD", 'IF', 'WHILE', 'PRINT', 'RETURN', 'FED', "PERIOD"},
    '<fdecls\'>': {'INT', 'DOUBLE', 'ID', "PERIOD", 'IF', 'WHILE', 'PRINT', 'RETURN', 'FED', "PERIOD"},
    '<fdec>': {'SEMICOLON', "PERIOD"},
    '<params>': {'RPAREN'},
    '<params\'>': {'RPAREN'},
    '<fname>': {'LPAREN'},
    '<declarations>': {'IF', 'WHILE', 'PRINT', 'RETURN', 'FED', "PERIOD"},
    '<declarations\'>': {'SEMICOLON', 'IF', 'WHILE', 'PRINT', 'RETURN', 'FED', "PERIOD"},
    '<decl>': {'SEMICOLON'},
    '<type>': {'ID', '<letter>'},
    '<varlist>': {'SEMICOLON'},
    '<varlist\'>': {'SEMICOLON'},
    '<statement_seq>': {'FI', 'OD', 'FED', 'ELSE', 'PERIOD'},
    '<statement_seq\'>': {'FI', 'OD', 'FED', 'ELSE', 'PERIOD'},
    '<statement>': {'SEMICOLON', 'FI', 'OD', 'FED', 'ELSE', 'PERIOD'},
    '<else_part>': {'FI'},
    '<expr>': {'RPAREN', 'COMMA', 'SEMICOLON', 'FI', 'OD', 'FED', 'ELSE', 'PERIOD', 'COMP'},
    '<expr\'>': {'RPAREN', 'COMMA', 'SEMICOLON', 'FI', 'OD', 'FED', 'ELSE', 'PERIOD', 'COMP'},
    '<term>': {'ADDOP', 'RPAREN', 'COMMA', 'SEMICOLON', 'FI', 'OD', 'FED', 'ELSE', 'PERIOD', 'COMP'},
    '<term\'>': {'ADDOP', 'RPAREN', 'COMMA', 'SEMICOLON', 'FI', 'OD', 'FED', 'ELSE', 'PERIOD', 'COMP'},
    '<factor>': {'MULOP', 'ADDOP', 'RPAREN', 'COMMA', 'SEMICOLON', 'FI', 'OD', 'FED', 'ELSE', 'PERIOD'},
    '<exprseq>': {'RPAREN'},
    '<exprseq\'>': {'RPAREN'},
    '<bexpr>': {'THEN'},
    '<bexpr\'>': {'THEN'},
    '<bterm>': {'OR', 'THEN'},
    '<bterm\'>': {'OR', 'THEN'},
    '<bfactor>': {'AND', 'OR', 'THEN', 'FI', 'OD', 'RPAREN', 'COMMA', 'SEMICOLON'},
    '<comp>': {'ID', '<number>', 'LPAREN', '<fname>'},
    '<var>': {'MULOP', 'ADDOP', 'COMP', 'RPAREN', 'ASSIGN', 'LBRACKET', 'COMMA', 'SEMICOLON', 'FI', 'OD', 'FED', 'ELSE', 'PERIOD'},
    """ '<letter>': {'<letter>', '<digit>'},
    '<digit>': {'<digit>'}, """
    '<id>': {'LPAREN', 'COMMA', 'MULOP', 'ADDOP', 'COMP', 'RPAREN', 'ASSIGN', 'LBRACKET', 'SEMICOLON', 'FI', 'OD', 'FED', 'ELSE', 'PERIOD'},
    '<id_chars>': {'LPAREN', 'COMMA', 'MULOP', 'ADDOP', 'COMP', 'RPAREN', 'ASSIGN', 'LBRACKET', 'SEMICOLON', 'FI', 'OD', 'FED', 'ELSE', 'PERIOD'},
    '<number>': {'MULOP', 'ADDOP', 'RPAREN', 'COMMA', 'SEMICOLON', 'COMP', 'RBRACKET', 'FI', 'OD', 'FED', 'ELSE', 'PERIOD'},
}
