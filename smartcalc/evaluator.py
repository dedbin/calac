from __future__ import annotations
from typing import Union, Optional, Dict
import math

import numpy as np
from .astnodes import AST, Num, Const, Call, Unary, Binary, Assign, PlotCommand, SimplifyCommand
from .errors import NameResolutionError, EvalError
from .constants import DEFAULT_CONSTANTS, ROUND_CONST

Number = Union[int, float]

SAFE_FUNCS = { # при добавлении новой функции в этот словарь, не забудьте добавить ее в _SYMPY_FUNCTIONS
    'abs': (1, abs),
    'max': ('2+', max),
    'min': ('2+', min),
    'round': ((1, 2), round),
    'sin': (1, lambda x: round(np.sin(x), ROUND_CONST)),
    'cos': (1, lambda x: round(np.cos(x), ROUND_CONST)),
    'tan': (1, lambda x: round(np.tan(x), ROUND_CONST)),
    'sqrt': (1, math.sqrt),
    'log': ((1, 2), lambda *xs: math.log(*xs)),
    'sinh': (1, lambda x: round(np.sinh(x), ROUND_CONST)),
    'cosh': (1, lambda x: round(np.cosh(x), ROUND_CONST)),
    'tanh': (1, lambda x: round(np.tanh(x), ROUND_CONST)),
    'asin': (1, math.asin),
    'acos': (1, math.acos),
    'atan': (1, math.atan),
    "exp": (1, lambda x: round(np.exp(x), ROUND_CONST)),
}

PROTECTED_NAMES = frozenset({name.lower() for name in DEFAULT_CONSTANTS} | set(SAFE_FUNCS.keys()))


class Evaluator:
    def __init__(self, constants: Optional[Dict[str, Number]] = None):
        self.constants = {k.lower(): v for k, v in DEFAULT_CONSTANTS.items()}
        if constants:
            for k, v in constants.items():
                self.constants[k.lower()] = v
        self.variables: Dict[str, Number] = {}

    def eval(self, node: AST) -> Number:
        if isinstance(node, PlotCommand):
            raise EvalError("Команды plot нельзя вычислять как числовые выражения.")
        if isinstance(node, SimplifyCommand):
            raise EvalError("Команды simplify нельзя вычислять как числовые выражения.")
        if isinstance(node, Num):
            return node.value
        if isinstance(node, Assign):
            name = node.name.lower()
            if name in PROTECTED_NAMES:
                raise EvalError(f"Нельзя изменять значение константы '{node.name}' так как она защищена (позиция {node.pos})")
            value = self.eval(node.expr)
            self.variables[name] = value
            return value
        if isinstance(node, Const):
            name = node.name.lower()
            if name in self.variables:
                return self.variables[name]
            if name not in self.constants:
                raise NameResolutionError(f"Константа или переменная'{node.name}' не определена (позиция {node.pos})")
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
            if op == '+': return left + right
            if op == '-': return left - right
            if op == '*': return left * right
            if op == '/': return left / right
            if op == '//': return left // right
            if op == '%': return left % right
            if op == '**': return left ** right
            raise EvalError(f"Неизвестный бинарный оператор '{op}' (позиция {node.pos})")
        if isinstance(node, Call):
            name = node.func.lower()
            if name not in SAFE_FUNCS:
                raise NameResolutionError(f"Функция '{node.func}' не определена (позиция {node.pos})")
            spec, func = SAFE_FUNCS[name]
            args = [self.eval(arg) for arg in node.args]
            for a in args:
                if not isinstance(a, (int, float)):
                    raise EvalError(f"Функция '{node.func}' ожидает числовые аргументы (позиция {node.pos})")
            n = len(args)
            if isinstance(spec, int):
                if n != spec:
                    raise EvalError(f"Функция '{node.func}' ожидает {spec} аргумент(ов), но получила {n} (позиция {node.pos})")
            elif isinstance(spec, str) and spec.endswith('+'):
                min_args = int(spec[:-1])
                if n < min_args:
                    raise EvalError(
                        f"Функция '{node.func}' ожидает как минимум {min_args} аргумент(ов), но получила {n} (позиция {node.pos})"
                    )
            elif isinstance(spec, tuple) and len(spec) == 2 and all(isinstance(x, int) for x in spec):
                min_a, max_a = spec
                if not (min_a <= n <= max_a):
                    raise EvalError(f"Функция '{node.func}' ожидает от {min_a} до {max_a} аргумент(ов), но получила {n} (позиция {node.pos})")
            try:
                result = func(*args)
            except ValueError:
                raise EvalError(
                    f"Аргументы функции '{node.func}' выходят за допустимую область определения (позиция {node.pos})"
                ) from None
            if isinstance(result, (float, np.floating)) and math.isnan(float(result)):
                raise EvalError(
                    f"Функция '{node.func}' вернула недопустимое значение (NaN) (позиция {node.pos})."
                )
            return result
        raise EvalError('Неподдерживаемый тип узла AST.')
