import math
import pytest

from smartcalc.api import eval_expr
from smartcalc.errors import EvalError, NameResolutionError


def test_sin_pi_zero():
    assert eval_expr('sin(pi)') == pytest.approx(0.0)


def test_log_with_base():
    assert eval_expr('log(100,10)') == pytest.approx(2.0)


def test_abs_power_precedence():
    assert eval_expr('abs(-3**2)') == 9


def test_max_variadic():
    assert eval_expr('max(1,5,2,3)') == 5


def test_round_two_args():
    assert eval_expr('round(3.1415,2)') == pytest.approx(3.14)


def test_nested_calls():
    assert eval_expr('abs(sin(pi))') == pytest.approx(0.0)


def test_calls_with_operators():
    assert eval_expr('2+sqrt(16)*3') == pytest.approx(14.0)


def test_error_too_few_args():
    with pytest.raises(EvalError):
        eval_expr('max(1)')


def test_error_too_many_args():
    with pytest.raises(EvalError):
        eval_expr('sin(1,2)')


def test_error_range_args():
    with pytest.raises(EvalError):
        eval_expr('log(1,2,3)')


def test_unknown_function():
    with pytest.raises(NameResolutionError):
        eval_expr('foo(1)')
