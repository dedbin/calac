from __future__ import annotations
from typing import Dict, Callable
import sympy as sp
from .astnodes import AST, Num, Const, Call, Unary, Binary, SimplifyCommand
from .evaluator import Evaluator
from .errors import EvalError, NameResolutionError


_SYMPY_CONSTANTS: Dict[str, sp.Expr] = {
    'pi': sp.pi,
    'e': sp.E,
    'phi': sp.GoldenRatio,
}
_SYMPY_FUNCTIONS: Dict[str, Callable[..., sp.Expr]] = {
    'abs': sp.Abs,
    'max': lambda *args: sp.Max(*args),
    'min': lambda *args: sp.Min(*args),
    'round': lambda *args: sp.Function('round')(*args),
    'sin': sp.sin,
    'cos': sp.cos,
    'tan': sp.tan,
    'sqrt': sp.sqrt,
    'log': sp.log,
    'sinh': sp.sinh,
    'cosh': sp.cosh,
    'tanh': sp.tanh,
    'asin': sp.asin,
    'acos': sp.acos,
    'atan': sp.atan,
}
def _to_sympy(node: AST, evaluator: Evaluator) -> sp.Expr:
    if isinstance(node, Num):
        value = node.value
        if isinstance(value, int):
            return sp.Integer(value)
        return sp.Float(value)
    if isinstance(node, Const):
        name = node.name.lower()
        if name in evaluator.variables:
            return _to_sympy(Num(evaluator.variables[name], node.pos), evaluator)
        if name in _SYMPY_CONSTANTS:
            return _SYMPY_CONSTANTS[name]
        if name in evaluator.constants:
            return sp.Float(evaluator.constants[name])
        return sp.Symbol(node.name)
    if isinstance(node, Unary):
        expr = _to_sympy(node.expr, evaluator)
        if node.op == '+':
            return expr
        if node.op == '-':
            return -expr
        raise EvalError(f"Неизвестный унарный оператор '{node.op}' (позиция {node.pos})")
    if isinstance(node, Binary):
        left = _to_sympy(node.left, evaluator)
        right = _to_sympy(node.right, evaluator)
        op = node.op
        if op == '+':
            return left + right
        if op == '-':
            return left - right
        if op == '*':
            return left * right
        if op == '/':
            return left / right
        if op == '//':
            return sp.floor(left / right)
        if op == '%':
            return sp.Mod(left, right)
        if op == '**':
            return left ** right
        raise EvalError(f"Неизвестный бинарный оператор '{op}' (позиция {node.pos})")
    if isinstance(node, Call):
        func_name = node.func.lower()
        if func_name not in _SYMPY_FUNCTIONS:
            raise NameResolutionError(
                f"Функция '{node.func}' не поддерживается в режиме simplify (позиция {node.pos})"
            )
        args = [_to_sympy(arg, evaluator) for arg in node.args]
        func = _SYMPY_FUNCTIONS[func_name]
        return func(*args)
    raise EvalError('Команда simplify поддерживает только арифметические выражения.')
def execute_simplify(command: SimplifyCommand, evaluator: Evaluator) -> str:
    expr = _to_sympy(command.expr, evaluator)
    simplified = sp.simplify(expr)
    return sp.sstr(simplified)