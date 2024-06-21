import ply.yacc as yacc

# Get the token map from the lexer
from frontend.lexy import tokens
from utils.nodes import *





def p_blocks(p):
    '''blocks : blocks flow
              | blocks build
              | flow
              | build
    '''
    if len(p) == 3: p[0] = p[1] + [p[2]]
    else : p[0] = [p[1]]



def p_build(p):
    '''build : BUILD term term body
    '''
    p[0] = Build(
        name = p[3],
        flow = p[2],
        body = p[4],
        line=p.lineno(1), charpos=p.lexpos(1)
    )


def p_flowdef(p):
    '''flow : flowproto body'''
    p[0] = FlowDef(
        name = p[1].name,
        proto = p[1],
        body = p[2],
        line=p.lineno(1), charpos=p.lexpos(1)
    )


def p_flowproto(p):
    '''flowproto : flowproto LBRACKET term RBRACKET LPAREN term RPAREN
                 | flowproto LPAREN term RPAREN LBRACKET term RBRACKET
                 
                 | flowproto LPAREN term RPAREN stuple
                 | flowproto stuple LPAREN term RPAREN
                 | flowproto LBRACKET term RBRACKET rtuple
                 | flowproto rtuple LBRACKET term RBRACKET
                 
                 | flowproto LBRACKET term RBRACKET
                 | flowproto LPAREN term RPAREN
                 
                 | flowproto stuple rtuple
                 | flowproto rtuple stuple
                 
                 | flowproto stuple
                 | flowproto rtuple
                 
                 | FLOW term
    '''
    if len(p) == 8:
        # print('single single')
        if p[2] == '(':
            p[0] = FlowProto(
                name = p[1].name, 
                symbols = [p[6]],
                args = [p[3]],
                line=p.lineno(1),
                charpos=p.lexpos(1)
            )
        else:
            p[0] = FlowProto(
                name = p[1].name, 
                symbols = [p[3]],
                args = [p[6]],
                line=p.lineno(1),
                charpos=p.lexpos(1)
            )
    elif len(p) == 6:
        # print('single tuple')
        if p[2] == '(':
            p[0] = FlowProto(
                name = p[1].name, 
                symbols = [p[3]],
                args = p[5],
                line=p.lineno(1),
                charpos=p.lexpos(1)
            )
        elif p[3] == '(':
            p[0] = FlowProto(
                name = p[1].name, 
                symbols = [p[4]],
                args = p[2],
                line=p.lineno(1),
                charpos=p.lexpos(1)
            )
        elif p[2] == '[':
            p[0] = FlowProto(
                name = p[1].name, 
                symbols = p[5],
                args = [p[3]],
                line=p.lineno(1),
                charpos=p.lexpos(1)
            )
        elif p[3] == '[':
            p[0] = FlowProto(
                name = p[1].name, 
                symbols = p[2],
                args = [p[4]],
                line=p.lineno(1),
                charpos=p.lexpos(1)
            )
    elif len(p) == 5:
        # print('single')
        p[0] = FlowProto(
            name = p[1].name,
            symbols = p[3] if p[2] == '(' else None,
            args = p[3] if p[2] == '[' else None,
            line=p.lineno(1),
            charpos=p.lexpos(1)
        )
    elif len(p) == 4:
        # print('tuple tuple')
        p[0] = FlowProto(
            name = p[1].name, 
            symbols = p[2] if p[2].bracks == 'round' else p[3],
            args = p[3] if p[3].bracks == 'square' else p[2],
            line=p.lineno(1),
            charpos=p.lexpos(1)
        )
    else:
        # print('tuple or none')
        if p[1] == 'flow': p[0] = FlowProto(name = p[2], symbols = None, args = None)
        else:
            p[0] = FlowProto(
                name = p[1].name,
                symbols = p[2] if p[2].bracks == 'round' else None,
                args = p[2] if p[2].bracks == 'square' else None,
                line=p.lineno(1),
                charpos=p.lexpos(1)
            )




def p_body(p):
    '''body : LBRACE statements RBRACE'''
    p[0] = Body(statements=p[2])




def p_statements(p):
    '''statements : statements statement
                  | statement
    '''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_statement(p):
    '''statement : retstmt
                 | letstmt
                 | assstmt
                 | shapespec
    '''
    p[0] = p[1]


def p_shape_spec(p):
    '''shapespec : term EQUALS GT tuple SEMICOLON
                 | term EQUALS GT tuple_s SEMICOLON
                 | term EQUALS GT stuple SEMICOLON
                 | term EQUALS GT rtuple SEMICOLON
                 | term EQUALS GT term SEMICOLON
                 | term EQUALS GT body SEMICOLON
    '''
    p[0] = ShapeSpec(var=p[1], shape=p[4], line=p[1].line, charpos=p[1].charpos)


def p_retter(p):
    '''retstmt : RETURN expr SEMICOLON
               | RETURN tuple SEMICOLON
               | RETURN tuple_s SEMICOLON
               | RETURN stuple SEMICOLON
               | RETURN rtuple SEMICOLON
               | RETURN term SEMICOLON
    '''
    p[0] = Return(value=p[2], line=p.lineno(1), charpos=p.lexpos(1))

def p_asser(p):
    '''assstmt : asslhs expr SEMICOLON
               | asslhs tuple SEMICOLON
               | asslhs tuple_s SEMICOLON
               | asslhs stuple SEMICOLON
               | asslhs rtuple SEMICOLON
               | asslhs term SEMICOLON
    '''
    p[0] = Assignment(left=p[1], right=p[2], line=p.lineno(1), charpos=p.lexpos(1))
    

def p_ass_lhs(p):
    '''asslhs : expr EQUALS
              | tuple EQUALS
              | tuple_s EQUALS
              | stuple EQUALS
              | rtuple EQUALS
              | term EQUALS
    '''
    p[0] = p[1]


def p_letter(p):
    '''letstmt : LET term term SEMICOLON
               | LET term term stuple SEMICOLON
    '''
    p[0] = Let(
        flow = p[2], idts=[p[3]], init=p[4] if p[4] != ';' else None, line=p.lineno(1), charpos=p.lexpos(1)
    )


def p_rtuple(p):
    '''rtuple : LPAREN tuple RPAREN
              | LPAREN tuple_s RPAREN
    '''
    p[0] = Tuple(vals=p[2], bracks='round', line=p.lineno(2), charpos=p.lexpos(2))


def p_stuple(p):
    '''stuple : LBRACKET tuple RBRACKET
              | LBRACKET tuple_s RBRACKET
    '''
    p[0] = Tuple(vals=p[2], bracks='square', line=p.lineno(2), charpos=p.lexpos(2))






def p_tuple_cont(p):
    '''tuple   : tuple_s term
               | tuple_s expr
               | tuple_s slice_l
               | tuple_s slice_r
               | tuple_s slice_e
               | tuple_s stuple
               | tuple_s rtuple
               
               | tuple COMMA term
               | tuple COMMA expr
               | tuple COMMA slice_l
               | tuple COMMA slice_r
               | tuple COMMA slice_e
               | tuple COMMA stuple
               | tuple COMMA rtuple
    '''
    # print('trigged here')
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = p[1] + [p[3]]


def p_tuple_start(p):
    '''tuple_s : term COMMA
               | expr COMMA
               | stuple COMMA
               | rtuple COMMA
               | slice_l COMMA
               | slice_r COMMA
               | slice_e COMMA
    '''
    # print('trigged')
    p[0] = [p[1]]



def p_call(p):
    '''expr : term LPAREN expr RPAREN
            | term LPAREN term RPAREN
            | term LPAREN RPAREN
            
            | term rtuple
    '''
    p[0] = Call(name=p[1], args=p[2].vals if type(p[2]) == Tuple else ([p[3]] if p[3] != ')' else None),
                line=p[1].line, charpos=p[1].charpos)


def p_slice_left(p):
    '''slice_l : term slice_e 
               | term slice_r
    '''
    s : Slice = p[2]
    s.left = p[1]
    p[0] = s

def p_slice_right(p):
    '''slice_r : slice_e term 
               | slice_l term
    '''
    s : Slice = p[1]
    s.right = p[2]
    p[0] = s


def p_slice_empty(p):
    '''slice_e : COLON
    '''
    p[0] = Slice(left=0, right=-1, step=1, line=p.lineno(0), charpos=p.lexpos(0))


def p_slice(p):
    '''slice : LBRACKET slice_l RBRACKET
             | LBRACKET slice_r RBRACKET
             | LBRACKET slice_e RBRACKET
             | LBRACKET term RBRACKET
    '''
    p[0] = p[2]





def p_expr(p):
    '''expr : term op term
            | term op expr
            | expr op expr
            | expr op term
            
            | MINUS term
            | MINUS expr
            
            | term stuple
            | term slice
            | expr stuple
            | expr slice
            
            | LPAREN expr RPAREN
    '''
    if len(p) == 3:
        if p[1] == '-':
            p[0] = Op(value='-', left=None, right=p[2], line=p.lineno(2), charpos=p.lexpos(2))
        else:
            p[0] = Op(name='slice', left=p[1], right=p[2], line=p.lineno(1), charpos=p.lexpos(1))
    elif p[1] == '(': p[0] = p[2]
    else : p[0] = Op(value=p[2], left=p[1], right=p[3], line=p.lineno(1), charpos=p.lexpos(1))


def p_term(p):
    '''term : IDENTIFIER
            | NUMBER
    '''
    p[0] = Term(line = p.lineno(1), charpos=p.lexpos(1), value=p[1])


def p_ops(p):
    '''op : PLUS
          | MINUS
          | MUL
          | DIVIDE
          | MATMUL
          | DOT
    '''
    p[0] = p[1]





def p_error(p):
    if p: raise InvalidSyntax(f"Syntax error at '{p.value}' on line number {p.lineno}!", line = p.lineno)
    else : print('End of file (maybe?)')


# Build the parser
parser = yacc.yacc()