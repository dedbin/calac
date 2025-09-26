from .lexer import Lexer
from .parser import Parser
from .astnodes import SimplifyCommand
from .evaluator import Evaluator
from .simplify import execute_simplify


def tokenize(text: str):
    return Lexer(text).tokenize()

def parse(text: str):
    return Parser(text, tokenize(text)).parse()

def eval_expr(text: str, constants=None):
    return Evaluator(constants).eval(parse(text))

def simplify_expr(text: str, constants=None, variables=None):
    evaluator = Evaluator(constants)
    if variables:
        for key, value in variables.items():
            evaluator.variables[key.lower()] = value
    ast = parse(text)
    if not isinstance(ast, SimplifyCommand):
        raise ValueError("simplify_expr ожидает команду 'simplify'.")
    return execute_simplify(ast, evaluator)