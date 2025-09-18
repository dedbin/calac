from __future__ import annotations
from typing import Union, Optional, Dict
import math

import numpy as np
from .astnodes import AST, Num, Const, Call, Unary, Binary
from .errors import NameResolutionError, EvalError
from .constants import DEFAULT_CONSTANTS

Number = Union[int, float]

SAFE_FUNCS = {
    'abs': (1, abs),
    'max': ('2+', max),
    'min': ('2+', min),
    'round': ((1, 2), round),
    'sin': (1, lambda x: round(np.sin(x), 5)),
    'cos': (1, lambda x: round(np.cos(x), 5)),
    'sqrt': (1, np.sqrt),
    'log': ((1, 2), lambda *xs: math.log(*xs)),
    'sinh': (1, lambda x: round(np.sinh(x), 5)),
    'cosh': (1, lambda x: round(np.cosh(x), 5)),
    'tanh': (1, lambda x: round(np.tanh(x), 5)),
    'asin': (1, np.arcsin),
    'acos': (1, np.arccos),
    'atan': (1, np.arctan),
}

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
        if isinstance(node, Call):
            name = node.func.lower()
            if name not in SAFE_FUNCS:
                raise NameResolutionError(f"Функция '{node.func}' не определена (позиция {node.pos})")
            spec, func = SAFE_FUNCS[name]
            args = [self.eval(arg) for arg in node.args]
            for a in args:
                if not isinstance(a, (int, float)):
                    raise EvalError(f"Аргументы функции должны быть числами (позиция {node.pos})")
            n = len(args)
            if isinstance(spec, int):
                if n != spec:
                    raise EvalError(
                        f"Функция '{node.func}' требует {spec} аргумент(ов), получено {n} (позиция {node.pos})"
                    )
            elif isinstance(spec, str) and spec.endswith('+'):
                min_args = int(spec[:-1])
                if n < min_args:
                    raise EvalError(
                        f"Функция '{node.func}' требует не менее {min_args} аргумент(ов), получено {n} (позиция {node.pos})"
                    )
            elif isinstance(spec, tuple) and len(spec) == 2 and all(isinstance(x, int) for x in spec):
                min_a, max_a = spec
                if not (min_a <= n <= max_a):
                    raise EvalError(
                        f"Функция '{node.func}' требует от {min_a} до {max_a} аргумент(ов), получено {n} (позиция {node.pos})"
                    )
            return func(*args)
        raise EvalError("Неизвестный узел AST")
