import ply.lex as lex

tokens = [
    'IDENTIFIER', 'NUMBER', 'PLUS', 'MINUS', 'MUL', 'DIVIDE', 'MATMUL',
    'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET', 'LBRACE', 'RBRACE', 'SEMICOLON',
    'COMMA', 'EQUALS', 'RETURN', 'FLOW', 'LET', 'BUILD', 'COLON', 'DOT', 'GT', 'LT'
]

t_PLUS      = r'\+'
t_MINUS     = r'-'
t_MUL       = r'\*'
t_DIVIDE    = r'/'
t_MATMUL    = r'@'
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_LBRACE    = r'\{'
t_RBRACE    = r'\}'
t_SEMICOLON = r';'
t_COMMA     = r','
t_EQUALS    = r'='
t_COLON     = r':'
t_DOT       = r'\.'
t_GT        = r'>'
t_LT        = r'<'


keywords = {
    'flow': 'FLOW',
    'let': 'LET',
    'return': 'RETURN',
    'build': 'BUILD',
}


def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = keywords.get(t.value, 'IDENTIFIER')
    return t

def t_NUMBER(t):
    r'-?\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore  = ' \t'


def t_comment(t):
    r'//.*'
    pass

# Error handling rule
def t_error(t):
    print(f"Illegal character '{t.value[0]}' on line {t.lineno}!")
    t.lexer.skip(1)



# Build the lexer
lexer : lex.Lexer = lex.lex()

