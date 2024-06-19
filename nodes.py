from dataclasses import dataclass
from typing import Any, Literal
import json

@dataclass
class Node:
    line : int = None
    charpos : int = None
    def __str__(self) -> str:
        return ''
    def __repr__(self) -> str:
        return self.__str__()
    def __hash__(self) -> int:
        return self.__repr__().__hash__()
    def __eq__(self, value: object) -> bool:
        if type(self) != type(value): return False
        return self.__hash__() == value.__hash__()
    def __ne__(self, value: object) -> bool:
        if type(self) != type(value): return True
        return self.__hash__() != value.__hash__()


class Dimension(Node):
    num : int = 0
    
    def __init__(self) -> None:
        self.id = Dimension.num
        Dimension.num += 1
        
    def __str__(self) -> str:
        return f'D({self.id})'
    
    def __eq__(self, value: object) -> bool:
        if type(value) != Dimension: return False
        return self.id == value.id
    
    def __ne__(self, value: object) -> bool:
        if type(value) != Dimension: return True
        return self.id != value.id


class ShapeLength(Node):
    num : int = 0
    
    def __init__(self) -> None:
        self.id = ShapeLength.num
        ShapeLength.num += 1
        
    def __str__(self) -> str:
        return f'SL({self.id})'
    
    def __eq__(self, value: object) -> bool:
        if type(value) != ShapeLength: return False
        return self.id == value.id
    
    def __ne__(self, value: object) -> bool:
        if type(value) != ShapeLength: return True
        return self.id != value.id




@dataclass(repr = False)
class Tuple(Node):
    vals : list[Node] = None
    bracks : Literal['round', 'square', 'none'] = None
    
    def __getitem__(self, index : int) -> Node:
        return self.vals[index]


@dataclass(repr = False, eq = False)
class Shape(Node):
    dims : list[int | Node] = None
    length : ShapeLength | int = None
    
    def __len__(self) -> int:
        return len(self.dims)
    
    def __getitem__(self, k : int) -> Node:
        return self.dims[k]
    
    def __setitem__(self, k : int, value : Node) -> None:
        self.dims[k] = value
    
    def __str__(self) -> str:
        return f'Shape({self.length}, {self.dims})'


@dataclass(repr = False)
class Expr(Node):
    value : Node = None
    shape : Shape = None


@dataclass(repr = False, eq = False)
class Var(Node):
    name : str = None
    
    def __eq__(self, value : object) -> bool:
        if not (isinstance(value, Var) or (type(value) == str)): return False
        if type(value) == str:
            return self.name == value
        return self.name == value.name
    
    def __str__(self) -> str:
        return f'Var({self.name})'
    
    def __hash__(self) -> int:
        return self.name.__hash__()


class Symbol(Var):
    def __str__(self) -> str:
        return f'Symbol({self.name})'

class Arg(Var):
    def __str__(self) -> str:
        return f'Arg({self.name})'




@dataclass(repr=False, eq=False)
class Number(Node):
    value : float | int = None
    def __eq__(self, value: object) -> bool:
        if not type(value) in [Number, int, float]: return False
        if type(value) == Number:
            return self.value == value.value
        else:
            return self.value == value
    def __str__(self) -> str:
        return f'N({self.value})'
    def __hash__(self) -> int:
        return self.__repr__().__hash__()



@dataclass(repr=False, eq=False)
class Op(Expr):
    left : Expr = None
    right : Expr = None
    def __str__(self) -> str:
        return f'Op({self.value}, left={self.left}, right={self.right})'


@dataclass(repr = False, eq=False)
class Statement:
    line : int = None
    charpos : int = None


@dataclass(repr = False, eq=False)
class Return(Statement):
    value : (
        Expr | Var |
        Number | Tuple
    ) = None
    
    def __str__(self) -> str:
        return f'Return({self.value})'

@dataclass(eq = False)
class Let(Statement):
    flow : Node = None
    idts : list[Node] = None
    init : Node = None


@dataclass(eq = False)
class Assignment(Statement):
    left : Expr = None
    right : Expr = None

@dataclass(eq = False)
class ShapeSpec(Statement):
    var : Node = None
    shape : Shape = None





@dataclass
class Body:
    statements : list[Statement] = None
    line : int = None
    charpos : int = None
    def __str__(self) -> str:
        return f'Body({self.statements})'


@dataclass
class Build(Node):
    name : str = None
    flow : Node = None
    body : Body = None


@dataclass
class FlowProto(Node):
    name : str = None
    symbols : list[Symbol] = None
    args : list[Arg] = None


@dataclass(repr = False)
class FlowDef(Node):
    name : str = None
    proto : FlowProto = None
    body : Body = None
    retstmt : Return = None
    subftable : dict = None

    def __str__(self) -> str:
        return f'FlowDef({self.name}, symbols={[x for x in self.proto.symbols] if self.proto.symbols else None}, args={[x for x in self.proto.args] if self.proto.args else None}, statements={len(self.body.statements)})'


@dataclass
class Program:
    name : str = None
    flows : list[FlowDef] = None
    builds : list[Build] = None
    
    def getflow(self, name : str) -> FlowDef:
        for each in self.flows:
            if each.name == name: return each



@dataclass(repr = False)
class Call(Expr):
    name : str = None
    args : Tuple | list[Node] = None
    flow : FlowDef = None
    
    def __str__(self) -> str:
        return f'Call( {self.flow.name if self.flow is not None else ""} {self.name}({self.args}))'



@dataclass
class Slice(Node):
    left : Node = None
    right : Node = None
    step : Node = None








class ShapeClash(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class DimClash(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class MatMulShape(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InferenceError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class UnknownAttribute(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidAttribute(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InvalidTranspose(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidAssignment(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class UnkownVar(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class UnkownSubFlow(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
