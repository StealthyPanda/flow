from nodes import *


class Context:
    def __init__(
            self, initshapes : dict = None, dims : list[Dimension] = None, sls : list[ShapeLength] = None,
            program : Program = None, flow : FlowDef = None
        ) -> None:
        self.shapes : dict[Var | Symbol | Arg | str, Shape | Context] = initshapes if initshapes is not None else dict()
        self.dimensions : list[Dimension] = dims if dims is not None else []
        self.shapelengths : list[ShapeLength] = sls if sls is not None else []
        self.program = program
        self.flow = flow
    
    def __getitem__(self, key : Var | Symbol | Arg) -> Shape:
        return self.shapes[key]
    
    def __setitem__(self, key : Var | Symbol | Arg, value : Any | Shape):
        self.shapes[key] = value
    
    def __contains__(self, key : Var | Symbol | Arg) -> bool:
        for each in self.shapes.keys():
            if each.__hash__() == key.__hash__(): return True
        return False
    
    def define_dimension(self) -> Dimension:
        newdim = Dimension()
        self.dimensions.append(newdim)
        return newdim
    
    def define_shape_length(self) -> ShapeLength:
        newsl = ShapeLength()
        self.shapelengths.append(newsl)
        return newsl
    
    def subcontext(self, call : Call) -> object:
        caller = call.name
        flowargs = call.flow.proto.symbols
        callshapes = [flowlengths_expr(x, self) for x in (call.args.vals if type(call.args) == Tuple else call.args)]
        print('callargs:',  call.args)
        print('shapes:',  self.shapes)
        print('Callshapes:',  callshapes)
        subcont = {
            arg : shape for arg, shape in zip(flowargs, callshapes)
        }
        subcont = Context(
            initshapes=subcont, dims=self.dimensions, sls=self.shapelengths, program=self.program,
            flow=call.flow
        )
        
        self.shapes[caller] = subcont
        print('subcont:', subcont)
        return subcont
    
    def seed_shapes(self) -> None:
        for _, each in enumerate(self.shapelengths):
            if type(each) != int:
                raise InferenceError(
                    f'Cannot seed shapes; found un-inferred shape length {each}!'
                )
        for each in (self.shapes):
            if type(self.shapes[each]) == Context: self.shapes[each].seed_shapes()
            else:
                if not self.shapes[each].dims:
                    print(f'Seeding {each}...')
                    self.shapes[each].dims = [self.define_dimension() for _ in range(self.shapes[each].length)]
            
    
    def bake(self) -> None:
        for each in (self.shapes):
            if type(self.shapes[each]) == Context: self.shapes[each].bake()
            else:
                print(f'Baking {each}...')
                self.shapes[each].dims = [followdim(x, self) for x in self.shapes[each].dims]
    
    
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def getdict(self) -> dict:
        rep = {
            str(a) : (str(self.shapes[a]) if type(self.shapes[a]) != Context else self.shapes[a].getdict()) for a in self.shapes
        }
        return rep
    
    def __str__(self) -> str:
        return (
            f'ShapeLengths  : {self.shapelengths}\n' +
            f'Dimensions    : {self.dimensions}\n' +
            json.dumps(self.getdict(), indent = '    ')
        )





def transposeshape(varshape : Shape, d1 : Number | int = -1, d2 : Number | int = -2, *args) -> Shape:
    length = len(varshape.dims)
    d1 = d1.value if type(d1) == Number else d1
    d2 = d2.value if type(d2) == Number else d2
    
    nd1, nd2 = d1, d2
    if d1 < 0 : nd1 += length
    if d2 < 0 : nd2 += length
    
    if not ((0 <= nd1) and (nd1 < length)):
        raise InvalidTranspose(
            f'Dimension {d1} is out of bounds for transposing in {varshape}!'
        )
    if not ((0 <= nd2) and (nd2 < length)):
        raise InvalidTranspose(
            f'Dimension {d1} is out of bounds for transposing in {varshape}!'
        )
    
    newshape = [x for x in varshape.dims]
    newshape[nd1], newshape[nd2] = newshape[nd2], newshape[nd1]
    newshape = Shape(length=length, dims=newshape)
    
    return newshape

attrs = {
    'min' : {
        'length' : (lambda varshape, args, context : Shape(length=1)),
        'shape' : (lambda varshape, args, context : Shape(dims=[1]))
    },
    'max' : {
        'length' : (lambda varshape, args, context : Shape(length=1)),
        'shape' : (lambda varshape, args, context : Shape(dims=[1]))
    },
    'len' : {
        'length' : (lambda varshape, args, context : Shape(length=1)),
        'shape' : (lambda varshape, args, context : Shape(dims=[1]))
    },
    'shape' : {
        'length' : (lambda varshape, args, context : Shape(length=2)),
        'shape' : (lambda varshape, args, context : Shape(dims=[1, varshape.length]))
    },
    'T' : {
        'length' : (lambda varshape, args, context : Shape(length=varshape.length)),
        'shape' : (lambda varshape, args, context : transposeshape(varshape, *args))
    },
}




def followdim(dim : Dimension | ShapeLength, context : Context) -> Dimension | int:
    if type(dim) not in [Dimension, ShapeLength]: return dim
    while True:
        dim = context.dimensions[dim.id] if type(dim) == Dimension else context.shapelengths[dim.id]
        if type(dim) == Dimension:
            if context.dimensions[dim.id] == dim: return dim
        if type(dim) == ShapeLength:
            if context.shapelengths[dim.id] == dim: return dim
        else: return dim

def followlen(sl : ShapeLength, context : Context) -> ShapeLength | int:
    if type(sl) != ShapeLength: return sl
    while True:
        sl = context.shapelengths[sl.id]
        if type(sl) == ShapeLength:
            if context.shapelengths[sl.id] == sl: return sl
        else: return sl




def consolidatelength(a : Shape | None, b : Shape | None, context : Context) -> Shape:
    if (a is None) and (b is None):
        return Shape(length = context.define_shape_length())
    
    elif a is None: return b
    elif b is None: return a
    
    elif a == b: return a
    
    # else:
    al, bl = followlen(a.length, context), followlen(b.length, context)
    if (integer(al) and integer(bl)) and (al != bl):
        raise ShapeClash(
            f'Shape lengths do not match for {a} and {b}; ' +
            f'`{a.length}` ~> `{al}` and `{b.length}` ~> `{bl}`!'
        )
    elif type(al) == ShapeLength:
        context.shapelengths[al.id] = bl
        a.length = bl
        # outlength = bl
    elif type(bl) == ShapeLength:
        context.shapelengths[bl.id] = al
        b.length = al
        # outlength = al
    
    # return Shape(length = outlength.length if type(outlength) == Shape else outlength)
    return a


def flowlengths_flow(flow : FlowDef, context : Context) -> Shape:
    if flow.subftable is None:
        flow.subftable = dict()
    
    subftable = flow.subftable
    
    outlength = None
    
    for stmt in flow.body.statements:
        
        if type(stmt) == Assignment:
            left, right = stmt.left, stmt.right
            context[left] = flowlengths_expr(right, context)
        
        elif type(stmt) == Let:
            flowdef = stmt.flow
            for every in context.program.flows[::-1]:
                if every.name == flowdef:
                    flowdef = every
                    break
            for var in stmt.idts:
                subftable[var.name] = flowdef
        
        elif type(stmt) == Return:
            flow.retstmt = stmt
            print(f'\nCalulating return length for {flow.name}...')
            outlength = flowlengths_expr(stmt.value, context)
            print(f'Outlength in {flow.name} is {outlength}\n')
            if 'output' in context:
                context['output'].length = consolidatelength(outlength, context['output'], context).length
            else:
                context['output'] = outlength
            # context['output'] = Shape(length = context['output'].length)
    
    return outlength

def flowlengths_expr(node : Expr | Var | Number | str, context : Context) -> Shape | None:    
    if type(node) in [Number, int, float]: return None
    if isinstance(node, Var) or (type(node) == str):
        print(f'Finding length of variable {node}...')
        ret = None
        if node in context: ret = context[node]
        else:
            context[node] = Shape(length=context.define_shape_length())
            ret = context[node]
        print(f'{node} length is {ret}\n')
        return ret
    
    if type(node) == Op:
        
        if node.value == '.':
            if type(node.right) not in [Call, Var, str, Symbol, Arg]:
                raise UnknownAttribute(
                    f'Unknown attribute; got {node.right}!'
                )
            
            left = flowlengths_expr(node.left, context)
            args = []
            name = node.right
            
            if type(node.right) == Call:
                args = node.right.args
                name = node.right.name
            
            if name not in attrs:
                raise UnknownAttribute(
                    f'Unknown attribute; got {node.right}!'
                )
            
            return attrs[name]['length'](left, args, context)
        
        
        else:
            left, right = flowlengths_expr(node.left, context), flowlengths_expr(node.right, context)
            length = consolidatelength(left, right, context)
            
            
            print(f'FLE {node.left} {node.value} {node.right}')
            
            if isinstance(node.left, Var) or (type(node.left) == str):
                if (node.left not in context) or (context[node.left] is None):
                    context[node.left] = Shape(length = length.length)
            if isinstance(node.right, Var) or (type(node.right) == str):
                if (node.right not in context) or (context[node.right] is None):
                    context[node.right] = Shape(length = length.length)
            
            return Shape(length = length.length)
    
    if type(node) == Call:
        node.flow = context.flow.subftable[node.name]
        
        print(f'Flowing lengths into `{node.name}` of type `{node.flow.name}`...')
        sub = context.subcontext(node)
        length = flowlengths_flow(node.flow, sub)
        print(f'Got length {length}...\n')
        return length




def unknown(x) : return type(x) in [Dimension, ShapeLength]

def consolidate(a : Shape, b : Shape, context : Context) -> Shape:
    if (a is None) and (b is None):
        return None
    
    if a is None: return Shape(dims=[x for x in b.dims])
    if b is None: return Shape(dims=[x for x in a.dims])
    
    if a == b: 
        a.dims = b.dims
        return Shape(dims=[x for x in a.dims])
    
    
    newshape = []
    
    for ai, bi in zip(a.dims, b.dims):
        if ai == bi: newshape.append(followdim(ai, context))
        else:
            if unknown(ai) and unknown(bi):
                terminala = followdim(ai, context)
                terminalb = followdim(bi, context)
                if (not unknown(terminala)) and (not unknown(terminalb)):
                    raise DimClash(
                        f'Cannot consolidate shapes {a.dims} and {b.dims} @ `{ai}` and `{bi}`;' + 
                        f'`{ai}` ~> `{terminala}` and `{bi}` ~> `{terminalb}`!'
                    )
                elif unknown(terminala) and unknown(terminalb):
                    context.dimensions[terminala.id] = terminalb
                    newshape.append(terminalb)
                elif unknown(terminala):
                    context.dimensions[terminala.id] = terminalb
                    newshape.append(terminalb)
                else:
                    context.dimensions[terminalb.id] = terminala
                    newshape.append(terminala)
            elif unknown(ai):
                terminal = followdim(ai, context)
                if unknown((terminal)):
                    context.dimensions[terminal.id] = bi
                    newshape.append(bi)
                elif terminal == bi:
                    newshape.append(bi)
                else:
                    raise DimClash(
                        f'Cannot consolidate shapes {a.dims} and {b.dims} @ `{ai}` and `{bi}`;' + 
                        f'`{ai}` ~> `{terminal}` and `{bi}`!'
                    )
            elif unknown(bi):
                terminal = followdim(bi, context)
                if type(terminal) == Dimension:
                    context.dimensions[terminal.id] = ai
                    newshape.append(ai)
                elif terminal == ai:
                    newshape.append(ai)
                else:
                    raise DimClash(
                        f'Cannot consolidate shapes {a.dims} and {b.dims} @ `{ai}` and `{bi}`; ' + 
                        f'`{ai}` and `{bi}` ~> `{terminal}`!'
                    )
            else:
                raise DimClash(
                    f'Cannot consolidate shapes {a.dims} and {b.dims} @ `{ai}` and `{bi}`!'
                )
    
    return Shape(dims=newshape)



def flowshape_expr(node : Expr | Var | Number, context : Context) -> Shape | None:
    if type(node) in [Number, int, float]: return None
    if isinstance(node, Var) or (type(node) == str):
        if node in context: return context[node]
        else: return None
    
    if type(node) == Op:
        if node.value in ['+', '-', '*', '/', '^']:
            
            left = flowshape_expr(node.left, context)
            right = flowshape_expr(node.right, context)
            shape = consolidate(left, right, context)
            
            return shape
        
        elif node.value == '@':
            
            left, right = flowshape_expr(node.left, context), flowshape_expr(node.right, context)
            
            bl, br = left.dims[:-2], right.dims[:-2]
            batch = consolidate(Shape(dims=bl), Shape(dims=br), context)
            
            li, ri = Shape([left.dims[-1]]), Shape([right.dims[-2]])
            consolidate(li, ri, context)
            
            shape = Shape(dims= batch.dims + [left.dims[-2], right.dims[-1]])
            return shape
        
        elif node.value == '.':
            if type(node.right) not in [Call, Var, str, Symbol, Arg]:
                raise UnknownAttribute(
                    f'Unknown attribute; got {node.right}!'
                )
            
            left = flowshape_expr(node.left, context)
            args = []
            name = node.right
            
            if type(node.right) == Call:
                args = node.right.args
                name = node.right.name
            
            if name not in attrs:
                raise UnknownAttribute(
                    f'Unknown attribute; got {node.right}!'
                )
            
            return attrs[name]['shape'](left, args, context)
    
    elif type(node) == Call:
        subcont = context[node.name]
        subflow = node.flow
        callshapes = [flowshape_expr(x, context) for x in (node.args.vals if type(node.args) == Tuple else node.args)]
        
        for each, shape in zip(subflow.proto.symbols, callshapes):
            subcont[each] = consolidate(subcont[each], shape, subcont)
        
        finalshape = flowshape_flow(subflow, subcont)
        return finalshape

def flowshape_flow(flow : FlowDef, context : Context) -> Shape | None:
    outshape = None
    
    for stmt in flow.body.statements:
        if type(stmt) == Assignment:
            context[stmt.left] = flowshape_expr(stmt.right, context)
        elif type(stmt) == Return:
            shape = flowshape_expr(stmt.value, context)
            context['output'] = consolidate(context['output'], shape, context)
            outshape = context['output']
    
    return outshape












def integer(x) : return (type(x) == int) or ((type(x) == Number) and (type(x.value) == int))

def isfloat(x):
    try:
        float(x)
        return True
    except: return False

def isint(x):
    try:
        int(x)
        return True
    except: return False

def varandnums(root : Expr, flow : FlowDef) -> Var | Number:
    if type(root) == Op:
        if root.left:
            root.left = varandnums(root.left, flow)
        if root.right:
            root.right = varandnums(root.right, flow)
        return root
    elif type(root) == Tuple:
        root.vals = list(map(lambda x: varandnums(x, flow), root.vals))
        return root
    elif integer(root) or isint(root):
        return int(root)
    elif (type(root) == float) or isfloat(root):
        return float(root)
    elif (type(root) == str):
        if flow is not None:
            if (flow.proto.symbols is not None) and (root in flow.proto.symbols): return Symbol(name = root)
            elif (flow.proto.args is not None) and (root in flow.proto.args): return Arg(name = root)
            else: return Var(name = root)
        else: return root
    else:
        return root

def iron(root : Program) -> Program:
    flows : list[FlowDef] = root.flows
    for each in flows:
        if each.proto.symbols:
            if type(each.proto.symbols) == Tuple: each.proto.symbols = each.proto.symbols.vals
            each.proto.symbols = list(map(lambda x: Symbol(name = x), each.proto.symbols))
        if each.proto.args:
            if type(each.proto.args) == Tuple: each.proto.args = each.proto.args.vals
            each.proto.args = list(map(lambda x: Arg(name = x), each.proto.args))

        for stmt in each.body.statements:
            if type(stmt) == Return:
                stmt.value = varandnums(stmt.value, each)
            elif type(stmt) == Let:
                # stmt.init = varandnums(stmt.init, each)
                pass
            elif type(stmt) == Assignment:
                stmt.left = varandnums(stmt.left, each)
                stmt.right = varandnums(stmt.right, each)
    
    builds : list[Build] = root.builds
    for each in builds:
        for s in each.body.statements:
            s.var = varandnums(s.var, None)
            if type(s.shape) == list:
                s.shape = Tuple(vals=s.shape, bracks='none')
            elif type(s.shape) == Tuple:
                pass
            else:
                s.shape = Tuple(vals=[s.shape], bracks='none')
            s.shape = varandnums(s.shape, None)
    
    return root



def semantic_check_expr(expr : Expr, scope : list, subfs : dict[str | Var, FlowDef]):
    if type(expr) in [str, Var, Symbol, Arg]:
        if expr not in scope:
            raise UnkownVar(
                f'Unkown identifier; {expr}!'
            )
    elif type(expr) in [int, float, Number]: pass
    elif type(expr) == Op:
        if expr.value == '.':
            if type(expr.right) not in [Call, str, Var, Symbol, Arg]:
                raise InvalidAttribute(
                    f'Invalid attribute; got `{expr.right}`!'
                )
            
            name = expr.right.name if type(expr.right) in [Symbol, Var, Arg, Call] else expr.right
            if name not in attrs:
                raise UnknownAttribute(
                    f'Unknown attribute `{name}`!'
                )
            
            semantic_check_expr(expr.left, scope, subfs)
            
        else:
            semantic_check_expr(expr.left, scope, subfs)
            semantic_check_expr(expr.right, scope, subfs)
    elif type(expr) == Call:
        if expr.name not in subfs:
            raise UnkownSubFlow(
                f'Unknown subflow; got `{expr.name}`!'
            )
        args = expr.args.vals if type(expr.args) == Tuple else expr.args
        for each in args:
            semantic_check_expr(each, scope, subfs)
        semantic_check_flow(subfs[expr.name])



def semantic_check_flow(flow : FlowDef, program : Program) -> None:
    symbols = flow.proto.symbols if flow.proto.symbols is not None else []
    params = flow.proto.args if flow.proto.args is not None else []
    scope = symbols + params
    subfs = dict()
    
    for stmt in flow.body.statements:
        if type(stmt) == Assignment:
            if type(stmt.left) not in [Var, Symbol]:
                raise InvalidAssignment(
                    f'Invalid assignment, can only assign to `Symbol` or `Var`; type(left) ~> {type(stmt.left)}!'
                )
            
            semantic_check_expr(stmt.right, scope, subfs)
            scope.append(stmt.left)
        
        elif type(stmt) == Let:
            for fl in program.flows[::-1]:
                if fl.name == stmt.flow:
                    for each in stmt.idts:
                        subfs[each] = fl
        
        elif type(stmt) == Return:
            if type(stmt.value) == Tuple:
                raise TypeError(
                    f'Cannot return multiple types from a flow!'
                )
            
            semantic_check_expr(stmt.value, scope, subfs), subfs

