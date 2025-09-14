from __future__ import annotations
from typing import Union, Optional, Dict
from .astnodes import AST, Num, Const, Unary, Binary
from .errors import NameResolutionError, EvalError
from .constants import DEFAULT_CONSTANTS

Number = Union[int, float]

class Evaluator:
    def __init__(self, constants: Optional[Dict[str, Number]] = None):
        self.constants = {k.lower(): v for k, v in DEFAULT_CONSTANTS.items()}
        if constants:
            for k, v in constants.items():
                self.constants[k.lower()] = v

    def eval(self, node: AST) -> Number:
        if isinstance(node, Num):
            return node.value
        if isinstance(node, Const):
            name = node.name.lower()
            if name not in self.constants:
                raise NameResolutionError(f"Константа '{node.name}' не определена (позиция {node.pos})")
            return self.constants[name]
        if isinstance(node, Unary):
            val = self.eval(node.expr)
            if node.op == '+':
                return +val
            if node.op == '-':
                return -val
            raise EvalError(f"Неизвестный унарный оператор '{node.op}' (позиция {node.pos})")
        if isinstance(node, Binary):
            left = self.eval(node.left)
            right = self.eval(node.right)
            op = node.op
            if op == '+':  return left + right
            if op == '-':  return left - right
            if op == '*':  return left * right
            if op == '/':  return left / right
            if op == '//': return left // right
            if op == '%':  return left % right
            if op == '**': return left ** right
            raise EvalError(f"Неизвестный оператор '{op}' (позиция {node.pos})")
        raise EvalError("Неизвестный узел AST")
