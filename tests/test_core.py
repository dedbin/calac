import math
from smartcalc.api import eval_expr

def as_int_if_possible(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x

def test_basic_arith():
    assert as_int_if_possible(eval_expr('2+2*2')) == 6
    assert as_int_if_possible(eval_expr('(2+2)*2')) == 8
    assert eval_expr('10/4') == 2.5
    assert as_int_if_possible(eval_expr('7//3')) == 2
    assert as_int_if_possible(eval_expr('10%4')) == 2

def test_power_and_unary():
    assert as_int_if_possible(eval_expr('2**3**2')) == 512   # правоассоциативно
    assert as_int_if_possible(eval_expr('-3**2')) == -9      # ** сильнее унарного -
    assert as_int_if_possible(eval_expr('(-3)**2')) == 9

def test_constants():
    assert eval_expr('pi') == math.pi
    assert as_int_if_possible(eval_expr('2*pi + tau/2')) == 2*math.pi + math.tau/2

def test_paren_nesting():
    assert as_int_if_possible(eval_expr('2*(3+(4-1))')) == 12

def test_zero_division():
    try:
        eval_expr('1/0')
        assert False, 'must raise'
    except ZeroDivisionError:
        pass