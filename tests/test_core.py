import math
import pytest

from smartcalc.api import eval_expr, parse
from smartcalc.evaluator import Evaluator
from smartcalc.errors import SmartCalcError, EvalError


def test_add_mul_priority():
    assert eval_expr('2+2*2') == 6


def test_parentheses_priority():
    assert eval_expr('(2+2)*2') == 8


def test_division():
    assert eval_expr('10/4') == 2.5


def test_floor_division():
    assert eval_expr('7//3') == 2


def test_modulo():
    assert eval_expr('10%4') == 2


def test_power_right_assoc():
    assert eval_expr('2**3**2') == 512


def test_power_unary():
    assert eval_expr('-3**2') == -9


def test_power_unary_paren():
    assert eval_expr('(-3)**2') == 9


def test_constant_pi():
    assert eval_expr('pi') == pytest.approx(math.pi)


def test_constants_mix():
    expr = '2*pi + tau/2'
    assert eval_expr(expr) == pytest.approx(2 * math.pi + math.tau / 2)


def test_nested_parentheses():
    assert eval_expr('2*(3+(4-1))') == 12


def test_number_formats():
    assert eval_expr('1_000 + 2_000') == 3000
    assert eval_expr('1e-3 + .5') == pytest.approx(0.501)


def test_mixed_precedence1():
    assert eval_expr('2 + 3*4 - 5') == 9


def test_mixed_precedence2():
    assert eval_expr('2*3 + 4//2') == 8


@pytest.mark.parametrize('expr', ['1/0', '1//0', '1%0'])
def test_zero_division(expr):
    with pytest.raises(ZeroDivisionError):
        eval_expr(expr)


def test_error_unknown_symbol():
    with pytest.raises(SmartCalcError) as e:
        parse('2 + @ 3')
    msg = str(e.value)
    assert '@' in msg and '^' in msg


def test_error_unclosed_parenthesis():
    with pytest.raises(SmartCalcError) as e:
        parse('(2+3')
    assert '^' in str(e.value)


def test_error_extra_input():
    with pytest.raises(SmartCalcError) as e:
        parse('2+2 2')
    assert '^' in str(e.value)


def test_empty_input():
    with pytest.raises(SmartCalcError):
        parse('')

def test_assignment_persists_with_reassignment():
    ev = Evaluator()
    assert ev.eval(parse('x = 10')) == 10
    assert ev.eval(parse('x + 5')) == 15
    assert ev.eval(parse('x = x + 1')) == 11
    assert ev.eval(parse('X')) == 11


@pytest.mark.parametrize('expr', ['pi = 3', 'sin = 1'])
def test_assignment_protected_names(expr):
    ev = Evaluator()
    with pytest.raises(EvalError):
        ev.eval(parse(expr))
