import ply.yacc as yacc

# Get the token map from the lexer
from lexy import tokens
from nodes import *





def p_blocks(p):
    '''blocks : blocks flow
              | blocks build
              | flow
              | build
    '''
    if len(p) == 3: p[0] = p[1] + [p[2]]
    else : p[0] = [p[1]]



def p_build(p):
    '''build : BUILD IDENTIFIER IDENTIFIER body
    '''
    p[0] = Build(
        name = p[3],
        flow = p[2],
        body = p[4],
    )


def p_flowdef(p):
    '''flow : flowproto body'''
    p[0] = FlowDef(
        name = p[1].name,
        proto = p[1],
        body = p[2],

    )


def p_flowproto(p):
    '''flowproto : flowproto LBRACKET IDENTIFIER RBRACKET LPAREN IDENTIFIER RPAREN
                 | flowproto LPAREN IDENTIFIER RPAREN LBRACKET IDENTIFIER RBRACKET
                 
                 | flowproto LPAREN IDENTIFIER RPAREN stuple
                 | flowproto stuple LPAREN IDENTIFIER RPAREN
                 | flowproto LBRACKET IDENTIFIER RBRACKET rtuple
                 | flowproto rtuple LBRACKET IDENTIFIER RBRACKET
                 
                 | flowproto LBRACKET IDENTIFIER RBRACKET
                 | flowproto LPAREN IDENTIFIER RPAREN
                 
                 | flowproto stuple rtuple
                 | flowproto rtuple stuple
                 
                 | flowproto stuple
                 | flowproto rtuple
                 
                 | FLOW IDENTIFIER
    '''
    if len(p) == 8:
        # print('single single')
        if p[2] == '(':
            p[0] = FlowProto(
                name = p[1].name, 
                symbols = [p[6]],
                args = [p[3]],
                # line=p.lineno(0),
                # charpos=p.lexpos(0)
            )
        else:
            p[0] = FlowProto(
                name = p[1].name, 
                symbols = [p[3]],
                args = [p[6]],
                # line=p.lineno(0),
                # charpos=p.lexpos(0)
            )
    elif len(p) == 6:
        # print('single tuple')
        if p[2] == '(':
            p[0] = FlowProto(
                name = p[1].name, 
                symbols = [p[3]],
                args = p[5],
                # line=p.lineno(0),
                # charpos=p.lexpos(0)
            )
        elif p[3] == '(':
            p[0] = FlowProto(
                name = p[1].name, 
                symbols = [p[4]],
                args = p[2],
                # line=p.lineno(0),
                # charpos=p.lexpos(0)
            )
        elif p[2] == '[':
            p[0] = FlowProto(
                name = p[1].name, 
                symbols = p[5],
                args = [p[3]],
                # line=p.lineno(0),
                # charpos=p.lexpos(0)
            )
        elif p[3] == '[':
            p[0] = FlowProto(
                name = p[1].name, 
                symbols = p[2],
                args = [p[4]],
                # line=p.lineno(0),
                # charpos=p.lexpos(0)
            )
    elif len(p) == 5:
        # print('single')
        p[0] = FlowProto(
            name = p[1].name,
            symbols = p[3] if p[2] == '(' else None,
            args = p[3] if p[2] == '[' else None,
            # line=p.lineno(0),
            # charpos=p.lexpos(0)
        )
    elif len(p) == 4:
        # print('tuple tuple')
        p[0] = FlowProto(
            name = p[1].name, 
            symbols = p[2] if p[2].bracks == 'round' else p[3],
            args = p[3] if p[3].bracks == 'square' else p[2],
            # line=p.lineno(0),
            # charpos=p.lexpos(0)
        )
    else:
        # print('tuple or none')
        if p[1] == 'flow': p[0] = FlowProto(name = p[2], symbols = None, args = None)
        else:
            p[0] = FlowProto(
                name = p[1].name,
                symbols = p[2] if p[2].bracks == 'round' else None,
                args = p[2] if p[2].bracks == 'square' else None,
                # line=p.lineno(0),
                # charpos=p.lexpos(0)
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
    '''shapespec : IDENTIFIER EQUALS GT tuple SEMICOLON
                 | IDENTIFIER EQUALS GT tuple_s SEMICOLON
                 | IDENTIFIER EQUALS GT stuple SEMICOLON
                 | IDENTIFIER EQUALS GT rtuple SEMICOLON
                 | IDENTIFIER EQUALS GT NUMBER SEMICOLON
                 | IDENTIFIER EQUALS GT IDENTIFIER SEMICOLON
                 | IDENTIFIER EQUALS GT body SEMICOLON
    '''
    p[0] = ShapeSpec(var=p[1], shape=p[4],)


def p_retter(p):
    '''retstmt : RETURN expr SEMICOLON
               | RETURN tuple SEMICOLON
               | RETURN tuple_s SEMICOLON
               | RETURN stuple SEMICOLON
               | RETURN rtuple SEMICOLON
               | RETURN IDENTIFIER SEMICOLON
               | RETURN NUMBER SEMICOLON
    '''
    p[0] = Return(value=p[2],)

def p_asser(p):
    '''assstmt : asslhs expr SEMICOLON
               | asslhs tuple SEMICOLON
               | asslhs tuple_s SEMICOLON
               | asslhs stuple SEMICOLON
               | asslhs rtuple SEMICOLON
               | asslhs IDENTIFIER SEMICOLON
               | asslhs NUMBER SEMICOLON
    '''
    p[0] = Assignment(left=p[1], right=p[2],)
    

def p_ass_lhs(p):
    '''asslhs : expr EQUALS
              | tuple EQUALS
              | tuple_s EQUALS
              | stuple EQUALS
              | rtuple EQUALS
              | IDENTIFIER EQUALS
    '''
    p[0] = p[1]


def p_letter(p):
    '''letstmt : LET IDENTIFIER IDENTIFIER SEMICOLON
               | LET IDENTIFIER IDENTIFIER stuple SEMICOLON
    '''
    p[0] = Let(flow = p[2], idts=[p[3]], init=p[4] if p[4] != ';' else None,)


def p_rtuple(p):
    '''rtuple : LPAREN tuple RPAREN
              | LPAREN tuple_s RPAREN
    '''
    p[0] = Tuple(vals=p[2], bracks='round')


def p_stuple(p):
    '''stuple : LBRACKET tuple RBRACKET
              | LBRACKET tuple_s RBRACKET
    '''
    p[0] = Tuple(vals=p[2], bracks='square')






def p_tuple_cont(p):
    '''tuple   : tuple_s IDENTIFIER
               | tuple_s NUMBER
               | tuple_s expr
               | tuple_s slice_l
               | tuple_s slice_r
               | tuple_s slice_e
               | tuple_s stuple
               | tuple_s rtuple
               
               | tuple COMMA NUMBER
               | tuple COMMA IDENTIFIER
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
    '''tuple_s : NUMBER COMMA
               | IDENTIFIER COMMA
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
    '''expr : IDENTIFIER LPAREN expr RPAREN
            | IDENTIFIER LPAREN NUMBER RPAREN
            | IDENTIFIER LPAREN IDENTIFIER RPAREN
            | IDENTIFIER LPAREN RPAREN
            
            | IDENTIFIER rtuple
    '''
    p[0] = Call(name=p[1], args=p[2].vals if type(p[2]) == Tuple else ([p[3]] if p[3] != ')' else None))


def p_slice_left(p):
    '''slice_l : IDENTIFIER slice_e 
               | NUMBER slice_e
               | IDENTIFIER slice_r 
               | NUMBER slice_r
    '''
    s : Slice = p[2]
    s.left = p[1]
    p[0] = s

def p_slice_right(p):
    '''slice_r : slice_e IDENTIFIER 
               | slice_e NUMBER
               | slice_l IDENTIFIER 
               | slice_l NUMBER
    '''
    s : Slice = p[1]
    s.right = p[2]
    p[0] = s


def p_slice_empty(p):
    '''slice_e : COLON
    '''
    p[0] = Slice(left=0, right=-1, step=1,)


def p_slice(p):
    '''slice : LBRACKET slice_l RBRACKET
             | LBRACKET slice_r RBRACKET
             | LBRACKET slice_e RBRACKET
             | LBRACKET IDENTIFIER RBRACKET
             | LBRACKET NUMBER RBRACKET
    '''
    p[0] = p[2]





def p_expr(p):
    '''expr : NUMBER op NUMBER
            | NUMBER op expr
            | NUMBER op IDENTIFIER
            
            | expr op expr
            | expr op NUMBER
            | expr op IDENTIFIER
            
            | IDENTIFIER op IDENTIFIER
            | IDENTIFIER op NUMBER
            | IDENTIFIER op expr
            
            | MINUS IDENTIFIER
            | MINUS NUMBER
            | MINUS expr
            
            | IDENTIFIER stuple
            | IDENTIFIER slice
            | expr stuple
            | expr slice
            
            | LPAREN expr RPAREN
    '''
    if len(p) == 3:
        if p[1] == '-':
            p[0] = Op(value='-', left=None, right=p[2], )
        else:
            p[0] = Op(name='slice', value=None, left=p[1], right=p[2], )
    elif p[1] == '(': p[0] = p[2]
    else : p[0] = Op(value=p[2], left=p[1], right=p[3], )




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
    if p: print(f"Syntax error at '{p.value}' on line number {p.lineno}")
    else : print('End of file (maybe?)')


# Build the parser
parser = yacc.yacc()