from typing import Callable
from utils.nodes import *
from codex import dblog, warning, ok, error

import json






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
        self.ichains = dict()
    
    def __getitem__(self, key : Var | Symbol | Arg) -> Shape:
        return self.shapes[key]
    
    def __setitem__(self, key : Var | Symbol | Arg, value : Any | Shape):
        self.shapes[key] = value
        if isinstance(key, Var): self.add_inference(key, key.line, value)
    
    def __contains__(self, key : Var | Symbol | Arg) -> bool:
        for each in self.shapes.keys():
            if each.__hash__() == key.__hash__(): return True
        return False
    
    def add_inference(self, k : Var, lineno : int, shape : Shape):
        if k not in self.ichains:
            self.ichains[k] = InferenceChain()
        self.ichains[k].push((lineno, shape))
    
    def define_dimension(self) -> Dimension:
        newdim = Dimension()
        self.dimensions.append(newdim)
        return newdim
    
    def define_shape_length(self) -> ShapeLength:
        newsl = ShapeLength()
        self.shapelengths.append(newsl)
        return newsl
    
    def subcontext(self, call : Call, init : object = None) -> object:
        caller = call.name
        flowargs = call.flow.proto.symbols
        callshapes = [flowlengths_expr(x, self) for x in (call.args.vals if type(call.args) == Tuple else call.args)]
        subcont = {
            arg : shape for arg, shape in zip(flowargs, callshapes)
        }
        
        if init is not None:
            for each in init.shapes: subcont[each] = init[each]
        
        subcont = Context(
            initshapes=subcont, dims=self.dimensions, sls=self.shapelengths, program=self.program,
            flow=call.flow
        )
        
        self.shapes[caller] = subcont
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
                    self.shapes[each].dims = [self.define_dimension() for _ in range(self.shapes[each].length)]
            
    
    def bake(self) -> None:
        for each in (self.shapes):
            if type(self.shapes[each]) == Context: self.shapes[each].bake()
            else:
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



def extract_shapes(context : Context) -> dict:
    retter = dict()
    for each in context.shapes:
        if type(context[each]) == Context:
            retter[each] = extract_shapes(context[each])
        else:
            retter[each] = context[each]
    return retter









def process_ss_body(body : Body, context : Context) -> None:
    for stmt in body.statements:
        if type(stmt.shape) == Tuple:
            if len(stmt.shape.vals) == 1: stmt.shape.vals.append(1)
            shape = Shape(dims=stmt.shape.vals)
            shape.length = len(shape.dims)
            
            for i, each in enumerate(shape.dims):
                if each == "_":
                    shape.dims[i] = context.define_dimension()
            
            if stmt.var != 'output':
                if (context.flow.proto.symbols is not None) and stmt.var in context.flow.proto.symbols:
                    stmt.var = Symbol(line = stmt.line, name = stmt.var)
                elif (context.flow.proto.args is not None) and stmt.var in context.flow.proto.args:
                    stmt.var = Arg(line = stmt.line, name = stmt.var)
                else: stmt.var = Var(line = stmt.line, name = stmt.var)
            context[stmt.var] = shape
        else:
            sc = Context(
                program = context.program, flow = stmt.flow, dims=context.dimensions,
                sls=context.shapelengths
            )
            context[stmt.var] = sc
            process_ss_body(stmt.shape, sc)

def contextfrombuild(build : Build, program : Program) -> Context:
    context = Context(program = program, flow = build.flow)
    process_ss_body(build.body, context)
    return context








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
        'length' : (lambda varshape, args, context : Shape(length=2)),
        'shape' : (lambda varshape, args, context : Shape(dims=['_', '_']))
    },
    'max' : {
        'length' : (lambda varshape, args, context : Shape(length=2)),
        'shape' : (lambda varshape, args, context : Shape(dims=['_', '_']))
    },
    'len' : {
        'length' : (lambda varshape, args, context : Shape(length=2)),
        'shape' : (lambda varshape, args, context : Shape(dims=['_', '_']))
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




def followdim(dim : Dimension | ShapeLength, context : Context) -> Dimension | ShapeLength | int:
    if type(dim) not in [Dimension, ShapeLength]: return dim
    while True:
        dim = context.dimensions[dim.id] if type(dim) == Dimension else context.shapelengths[dim.id]
        if type(dim) == Dimension:
            if context.dimensions[dim.id] == dim: return dim
        elif type(dim) == ShapeLength:
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
    
    elif a is None: return Shape(length=b.length)
    elif b is None: return Shape(length=a.length)
    
    elif a == b: return Shape(length=a)
    
    # else:
    al, bl = followlen(a.length, context), followlen(b.length, context)
    if (integer(al) and integer(bl)) and (al != bl):
        line = a.line if a.line is not None else b.line
        charpos = a.charpos if a.charpos is not None else b.charpos
        raise ShapeClash(
            f'Shape lengths do not match for {a} and {b}; ' +
            f'`{a.length}` ~> `{al}` and `{b.length}` ~> `{bl}`!',
            line=line, charpos=charpos
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
            outlength = flowlengths_expr(stmt.value, context)
            if 'output' in context:
                context['output'].length = consolidatelength(outlength, context['output'], context).length
            else:
                context['output'] = outlength
            # context['output'] = Shape(length = context['output'].length)
    
    return outlength

def flowlengths_expr(node : Expr | Var | Number | str, context : Context) -> Shape | None:    
    if type(node) in [Number, int, float]: return None
    if isinstance(node, Var) or (type(node) == str):
        ret = None
        if node in context: ret = context[node]
        else:
            context[node] = Shape(length=context.define_shape_length())
            ret = context[node]
        return ret
    
    if type(node) == Op:
        
        if node.value == '.':
            if type(node.right) not in [Call, Var, str, Symbol, Arg]:
                raise UnknownAttribute(
                    f'Unknown attribute; got {node.right}!',
                    line=node.right.line, charpos=node.right.charpos
                )
            
            left = flowlengths_expr(node.left, context)
            args = []
            name = node.right
            
            if type(node.right) == Call:
                args = node.right.args
                name = node.right.name
            
            if name not in attrs:
                raise UnknownAttribute(
                    f'Unknown attribute; got {node.right}!',
                    line=node.right.line, charpos=node.right.charpos
                )
            
            return attrs[name]['length'](left, args, context)
        
        
        else:
            left, right = flowlengths_expr(node.left, context), flowlengths_expr(node.right, context)
            length = consolidatelength(left, right, context)
            
            
            
            if isinstance(node.left, Var) or (type(node.left) == str):
                if (node.left not in context) or (context[node.left] is None):
                    context[node.left] = Shape(length = length.length)
            if isinstance(node.right, Var) or (type(node.right) == str):
                if (node.right not in context) or (context[node.right] is None):
                    context[node.right] = Shape(length = length.length)
            
            return Shape(length = length.length)
    
    if type(node) == Call:
        node.flow = context.flow.subftable[node.name]
        
        sub = context.subcontext(node, context[node.name] if node.name in context else None)
        length = flowlengths_flow(node.flow, sub)
        return length




def unknown(x) : return type(x) in [Dimension, ShapeLength]

def consolidate(a : Shape, b : Shape, context : Context) -> Shape:
    
    #TODO: Add a thing for scalar shapes in this function.
    
    if (a is None) and (b is None):
        return None
    
    if a is None: return Shape(dims=[x for x in b.dims])
    if b is None: return Shape(dims=[x for x in a.dims])
    
    if a == b: 
        a.dims = b.dims
        return Shape(dims=[x for x in a.dims])
    
    
    newshape = []
    
    for i, (ai, bi) in enumerate(zip(a.dims, b.dims)):
        if ai == '_':
            ai = context.define_dimension()
            a.dims[i] = ai
        
        if bi == '_':
            bi = context.define_dimension()
            b.dims[i] = bi
        
        if ai == bi: newshape.append(followdim(ai, context))
        else:
            if unknown(ai) and unknown(bi):
                terminala = followdim(ai, context)
                terminalb = followdim(bi, context)
                if (not unknown(terminala)) and (not unknown(terminalb)):
                    line = a.line if a.line is not None else b.line
                    charpos = a.charpos if a.charpos is not None else b.charpos
                    raise DimClash(
                        f'Cannot consolidate shapes {a.dims} and {b.dims} @ `{ai}` and `{bi}`;' + 
                        f'`{ai}` ~> `{terminala}` and `{bi}` ~> `{terminalb}`!',
                        line = line, charpos=charpos
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
                    line = a.line if a.line is not None else b.line
                    charpos = a.charpos if a.charpos is not None else b.charpos
                    raise DimClash(
                        f'Cannot consolidate shapes {a.dims} and {b.dims} @ `{ai}` and `{bi}`;' + 
                        f'`{ai}` ~> `{terminal}` and `{bi}`!',
                        line=line, charpos=charpos
                    )
            elif unknown(bi):
                terminal = followdim(bi, context)
                if type(terminal) == Dimension:
                    context.dimensions[terminal.id] = ai
                    newshape.append(ai)
                elif terminal == ai:
                    newshape.append(ai)
                else:
                    line = a.line if a.line is not None else b.line
                    charpos = a.charpos if a.charpos is not None else b.charpos
                    raise DimClash(
                        f'Cannot consolidate shapes {a.dims} and {b.dims} @ `{ai}` and `{bi}`; ' + 
                        f'`{ai}` and `{bi}` ~> `{terminal}`!',
                        line=line, charpos=charpos
                    )
            else:
                line = a.line if a.line is not None else b.line
                charpos = a.charpos if a.charpos is not None else b.charpos
                raise DimClash(
                    f'Cannot consolidate shapes {a.dims} and {b.dims} @ `{ai}` and `{bi}`!',
                    line=line, charpos=charpos
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
            try : shape = consolidate(left, right, context)
            except Exception as e:
                e.args = (
                    (f"Shape consolidation failed between `{left}` and `{right}`!\n")+
                    e.args[0],
                )
                e.line = node.line
                e.charpos = node.charpos
                raise e
            
            return shape
        
        elif node.value == '@':
            
            left, right = flowshape_expr(node.left, context), flowshape_expr(node.right, context)
            
            bl, br = left.dims[:-2], right.dims[:-2]
            try : batch = consolidate(Shape(dims=bl), Shape(dims=br), context)
            except Exception as e:
                e.args = (
                    (f"Shape consolidation failed for batch dimensions b/w `{left}` and `{right}`!\n")+
                    e.args[0],
                )
                e.line = node.line
                e.charpos = node.charpos
                raise e
            
            li, ri = Shape(length=1, dims=[left.dims[-1]]), Shape(length=1, dims=[right.dims[-2]])
            # dblog(li, ri)
            try : consolidate(li, ri, context)
            except Exception as e:
                e.args = (
                    (f"Inner dimensions don't match for matrix multiplication b/w `{left}` and `{right}`!\n")+
                    e.args[0],
                )
                e.line = node.line
                e.charpos = node.charpos
                raise e
            
            shape = Shape(dims= batch.dims + [left.dims[-2], right.dims[-1]])
            return shape
        
        elif node.value == '.':
            if type(node.right) not in [Call, Var, str, Symbol, Arg]:
                raise UnknownAttribute(
                    f'Unknown attribute; got {node.right}!',
                    line=node.right.line, charpos=node.right.charpos
                )
            
            left = flowshape_expr(node.left, context)
            args = []
            name = node.right
            
            if type(node.right) == Call:
                args = node.right.args
                name = node.right.name
            
            if name not in attrs:
                raise UnknownAttribute(
                    f'Unknown attribute; got {node.right}!',
                    line=node.right.line, charpos=node.right.charpos
                )
            
            return attrs[name]['shape'](left, args, context)
    
    elif type(node) == Call:
        subcont = context[node.name]
        subflow = node.flow
        callshapes = [flowshape_expr(x, context) for x in (node.args.vals if type(node.args) == Tuple else node.args)]
        
        for each, shape in zip(subflow.proto.symbols, callshapes):
            try : subcont[each] = consolidate(subcont[each], shape, subcont)
            except Exception as e:
                e.args = (
                    (f"Shape consolidation failed given and inferred; `{subcont[each]}` and `{shape}`!\n")+
                    e.args[0],
                )
                e.line = node.line
                e.charpos = node.charpos
                raise e
        
        finalshape = flowshape_flow(subflow, subcont)
        return finalshape

def flowshape_flow(flow : FlowDef, context : Context) -> Shape | None:
    outshape = None
    
    for stmt in flow.body.statements:
        if type(stmt) == Assignment:
            shape = flowshape_expr(stmt.right, context)
            context[stmt.left] = Shape(length=shape.length, dims=shape.dims, line=shape.line)
        elif type(stmt) == Return:
            shape = flowshape_expr(stmt.value, context)
            try : context['output'] = consolidate(context['output'], shape, context)
            except Exception as e:
                e.args = (
                    f'Consolidation failed b/w given output shape and inferred; `{context["output"]}` and `{shape}`!\n' +
                    e.args[0],
                )
                e.line = stmt.line
                e.charpos = stmt.charpos
                raise e
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

def isvalididt(x : str) -> bool:
    if type(x) != str: return False
    
    for each in x:
        if not((ord('a') <= ord(each)) and (ord(each) <= ord('z')) or
            (ord('A') <= ord(each)) and (ord(each) <= ord('Z')) or
            (ord('0') <= ord(each)) and (ord(each) <= ord('9')) or
            each == '_'): return False
    
    return not isint(x[0])


def varandnums(root : Expr, flow : FlowDef, lineno : int = None) -> Var | Number:
    if type(root) == Op:
        if root.left:
            root.left = varandnums(root.left, flow)
        if root.right:
            root.right = varandnums(root.right, flow)
        return root
    elif type(root) == Tuple:
        root.vals = list(map(lambda x: varandnums(x, flow), root.vals))
        return root
    elif type(root) == Call:
        root.name = varandnums(root.name, flow)
        root.args = list(map(lambda x:varandnums(x, flow), varandnums(root.args, flow)))
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
    elif type(root) == Term:
        val = varandnums(root.value, flow)
        if isinstance(val, Node):
            val.line = root.line
            val.charpos = root.charpos
        return val
    else:
        return root

def iron_bb(body : Body):
    for s in body.statements:
        if type(s) == ShapeSpec:
            s.var = varandnums(s.var, None)
            if type(s.shape) == list:
                s.shape = Tuple(vals=s.shape, bracks='none')
            elif type(s.shape) == Tuple:
                pass
            else:
                s.shape = Tuple(vals=[s.shape], bracks='none')
            s.shape = varandnums(s.shape, None)
            
            if type(s.shape.vals[0]) == Body:
                s.shape = s.shape.vals[0]
                iron_bb(s.shape)

def iron(root : Program) -> Program:
    flows : list[FlowDef] = root.flows
    for each in flows:
        each.name = each.name.value
        each.proto.name = each.proto.name.value
        if each.proto.symbols:
            if type(each.proto.symbols) == Tuple: each.proto.symbols = each.proto.symbols.vals
            if type(each.proto.symbols) != list: each.proto.symbols = [each.proto.symbols]
            for i, x in enumerate(each.proto.symbols):
                if type(x) == Term: each.proto.symbols[i] = x.value
                each.proto.symbols[i] = Symbol(name=each.proto.symbols[i])
        if each.proto.args:
            if type(each.proto.args) == Tuple: each.proto.args = each.proto.args.vals
            if type(each.proto.args) != list: each.proto.args = [each.proto.args]
            for i, x in enumerate(each.proto.args):
                if type(x) == Term: each.proto.args[i] = x.value
                each.proto.args[i] = Arg(name=each.proto.args[i])
        for stmt in each.body.statements:
            if type(stmt) == Return:
                stmt.value = varandnums(stmt.value, each)
            elif type(stmt) == Let:
                stmt.flow = varandnums(stmt.flow, each)
                stmt.idts = [varandnums(x, each) for x in stmt.idts]
            elif type(stmt) == Assignment:
                stmt.left = varandnums(stmt.left, each)
                stmt.right = varandnums(stmt.right, each)
        # print(each)
    
    builds : list[Build] = root.builds
    for each in builds:
        each.name = each.name.value
        each.flow = each.flow.value
        iron_bb(each.body)
    
    return root



def semantic_check_expr(expr : Expr, scope : list, subfs : dict[str | Var, FlowDef], program : Program):
    if type(expr) in [str, Var, Symbol, Arg]:
        if expr not in scope:
            raise UnknownVar(
                f'Unknown identifier; `{expr}`!', line=expr.line, charpos=expr.charpos
            )
    elif type(expr) in [int, float, Number]: pass
    elif type(expr) == Op:
        if expr.value == '.':
            if type(expr.right) not in [Call, str, Var, Symbol, Arg]:
                raise InvalidAttribute(
                    f'Invalid attribute; got `{expr.right}`!', line=expr.right.line, charpos=expr.right.charpos
                )
            
            name = expr.right.name if type(expr.right) in [Symbol, Var, Arg, Call] else expr.right
            if name not in attrs:
                raise UnknownAttribute(
                    f'Unknown attribute `{name}`!', line=expr.right.line, charpos=expr.right.charpos
                )
            
            semantic_check_expr(expr.left, scope, subfs, program)
            
        else:
            semantic_check_expr(expr.left, scope, subfs, program)
            semantic_check_expr(expr.right, scope, subfs, program)
    elif type(expr) == Call:
        if expr.name not in subfs:
            raise UnknownSubFlow(
                f'Unknown subflow; got `{expr.name}`!',
                line=expr.line, charpos=expr.charpos
            )
        args = expr.args.vals if type(expr.args) == Tuple else expr.args
        for each in args:
            semantic_check_expr(each, scope, subfs, program)
        semantic_check_flow(subfs[expr.name], program)



def semantic_check_flow(flow : FlowDef, program : Program, callback : Callable = None) -> None:
    symbols = flow.proto.symbols if flow.proto.symbols is not None else []
    params = flow.proto.args if flow.proto.args is not None else []
    scope = symbols + params
    flow.subftable = dict()
    subfs = flow.subftable
    
    if not isvalididt(flow.name):
        raise InvalidIdentifier(
            f'Invalid identifier for flow name; got `{flow.name}`!',
            line=flow.line, charpos=flow.charpos
        )
    
    for each in scope:
        name = each
        if isinstance(each, Var): name = each.name
        if not isvalididt(name):
            raise InvalidIdentifier(
                f'Invalid identifier in flow prototype; got `{name}`!',
                line=flow.line, charpos=flow.charpos
            )
    
    for stmt in flow.body.statements:
        if callback: callback(stmt)
        
        if type(stmt) == Assignment:
            if type(stmt.left) not in [Var]:
                raise InvalidAssignment(
                    f'Invalid assignment, can only assign to `Var`; type(left) ~> {type(stmt.left)}!',
                    line=stmt.line, charpos=stmt.charpos
                )
            
            semantic_check_expr(stmt.right, scope, subfs, program)
            scope.append(stmt.left)
        
        elif type(stmt) == Let:
            trigged = False
            for fl in program.flows[::-1]:
                if fl.name == stmt.flow:
                    trigged = True
                    for each in stmt.idts:
                        subfs[each] = fl
            if not trigged:
                raise UnknownSubFlow(
                    f'Cannot find subflow `{stmt.flow}`!',
                    line=stmt.line, charpos=stmt.charpos
                )
        
        elif type(stmt) == Return:
            if type(stmt.value) == Tuple:
                raise ReturnError(
                    f'Cannot return multiple types from a flow!', line=stmt.line, charpos=stmt.charpos
                )
            
            semantic_check_expr(stmt.value, scope, subfs, program)


def semantic_check_buildbody(body : Body, flow : FlowDef, callback : Callable = None) -> None:
    for stmt in body.statements:
        if callback: callback(stmt)
        
        if type(stmt) != ShapeSpec:
            raise InvalidStatement(
                f'Only shape specifications are allowed in the build block; got type ~> `{type(stmt)}`!',
                line=stmt.line, charpos=stmt.charpos
            )
        
        if type(stmt.var) not in [Var, Symbol, Arg, str]:
            raise InvalidIdentifier(
                f'Shapes can be only be assigned to symbols or args; got type ~> `{type(stmt.var)}`!',
                line=stmt.line, charpos=stmt.charpos
            )
        
        if stmt.var == '_':
            raise InvalidIdentifier(
                f'Shapes can be only be assigned to symbols or args; got `{(stmt.var)}`!',
                line=stmt.line, charpos=stmt.charpos
            )
        
        if type(stmt.shape) == Tuple:
            for each in stmt.shape.vals:
                if not ((type(each) == int) or (each == '_')):
                    raise InvalidShape(
                        f'Shapes must contain constant integer values, or `_`; got `{each}`!',
                        line=stmt.line, charpos=stmt.charpos
                    )
        else:
            try:
                sf = flow.subftable[stmt.var]
                stmt.flow = sf
                semantic_check_buildbody(stmt.shape, sf, callback)
            except KeyError:
                raise UnknownSubFlow(
                    f'Undefined subflow used; got `{stmt.var}` whose flow type couldn\'t be found!',
                    line = stmt.line,
                    charpos=stmt.charpos
                )


def semantic_check_build(build : Build, program : Program, callback : Callable = None) -> None:
    if not isvalididt(build.name):
        raise InvalidIdentifier(
            f'Invalid name for build; got `{build.name}`!',
            line=build.line, charpos=build.charpos
        )
    
    trigged = False
    for each in program.flows:
        if each.name == build.flow:
            trigged = True
            build.flow = each
    
    if not trigged:
        raise UnknownFlow(
            f'Cannot find flow `{build.flow}`!',
            line=build.line, charpos=build.charpos
        )
    
    
    semantic_check_buildbody(build.body, build.flow, callback)
    
    




