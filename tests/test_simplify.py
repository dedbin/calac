import pytest
from typing import Optional
from smartcalc import api
from smartcalc.astnodes import SimplifyCommand, Binary, Num
from smartcalc.evaluator import Evaluator
from smartcalc.errors import NameResolutionError, EvalError
from smartcalc.simplify import execute_simplify
def _simplify(text: str, evaluator: Optional[Evaluator] = None) -> str:
    ev = evaluator or Evaluator()
    ast = api.parse(text)
    assert isinstance(ast, SimplifyCommand)
    return execute_simplify(ast, ev)
def test_basic_linear_combination():
    assert _simplify('simplify 2*x + 3*x') == '5*x'
def test_trigonometric_identity():
    assert _simplify('simplify sin(x)**2 + cos(x)**2') == '1'
def test_rational_expression():
    assert _simplify('simplify (x**2 - 1)/(x - 1)') == 'x + 1'
def test_simplify_respects_assigned_numbers():
    ev = Evaluator()
    ev.eval(api.parse('a = 2'))
    assert _simplify('simplify a + a', evaluator=ev) == '4'
def test_unsupported_function_raises():
    with pytest.raises(NameResolutionError):
        _simplify('simplify foo(x)')
def test_unsupported_operator_raises():
    ev = Evaluator()
    bad_command = SimplifyCommand(Binary('<<', Num(1, 0), Num(2, 0), 0), 0)
    with pytest.raises(EvalError):
        execute_simplify(bad_command, ev)