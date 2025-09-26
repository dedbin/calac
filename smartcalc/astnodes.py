from dataclasses import dataclass
from typing import Union, Optional


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
class Call(AST):
    func: str
    args: list[AST]
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


@dataclass
class Assign(AST):
    name: str
    expr: AST
    pos: int


@dataclass
class PlotTarget(AST):
    format: str
    path: Optional[str]
    pos: int


@dataclass
class PlotCommand(AST):
    expr: AST
    variable: Optional[str]
    label: Optional[str]
    domain_start: Optional[AST]
    domain_end: Optional[AST]
    target: Optional[PlotTarget]
    pos: int
