from .lexer import Lexer
from .parser import Parser
from .evaluator import Evaluator

def tokenize(text: str):
    return Lexer(text).tokenize()

def parse(text: str):
    return Parser(Lexer(text).tokenize()).parse()

def eval_expr(text: str, constants=None):
    return Evaluator(constants).eval(parse(text))