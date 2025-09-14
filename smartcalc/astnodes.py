from dataclasses import dataclass
from typing import Union

class AST:
    pass

@dataclass
class Num(AST):
    value: Union[int, float]
    pos: int

@dataclass
class Const(AST):
    name: str
    pos: int

@dataclass
class Unary(AST):
    op: str
    expr: AST
    pos: int

@dataclass
class Binary(AST):
    op: str
    left: AST
    right: AST
    pos: int