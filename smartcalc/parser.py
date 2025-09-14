from __future__ import annotations
from typing import List
from .tokens import Token, K_NUM, K_IDENT, K_OP, K_LP, K_RP, K_EOF
from .astnodes import AST, Num, Const, Unary, Binary
from .precedence import INFIX_BP, PREFIX_BP
from .errors import ParseError

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> Token:
        return self.tokens[self.i]

    def advance(self) -> Token:
        tok = self.peek()
        if tok.kind != K_EOF:
            self.i += 1
        return tok

    def expect(self, kind: str, value=None) -> Token:
        tok = self.peek()
        if tok.kind != kind or (value is not None and tok.value != value):
            expected = f"{kind}('{value}')" if value is not None else kind
            raise ParseError(f"Ожидается {expected}, найдено {tok.kind}('{tok.value}') на позиции {tok.pos}")
        self.advance()
        return tok

    def parse(self) -> AST:
        expr = self.parse_expr(0)
        if self.peek().kind != K_EOF:
            tok = self.peek()
            raise ParseError(f"Лишний ввод начиная с позиции {tok.pos}: '{tok.value}'")
        return expr

    def parse_expr(self, min_bp: int) -> AST:
        # nud
        tok = self.peek()
        if tok.kind == K_NUM:
            self.advance()
            left: AST = Num(tok.value, tok.pos)
        elif tok.kind == K_IDENT:
            self.advance()
            left = Const(str(tok.value), tok.pos)
        elif tok.kind == K_OP and tok.value in ('+', '-'):
            op_tok = self.advance()
            right = self.parse_expr(PREFIX_BP)
            left = Unary(op_tok.value, right, op_tok.pos)
        elif tok.kind == K_LP:
            self.advance()
            left = self.parse_expr(0)
            self.expect(K_RP)
        else:
            raise ParseError(f"Неожиданный токен {tok.kind}('{tok.value}') на позиции {tok.pos}")

        # led
        while True:
            tok = self.peek()
            if tok.kind == K_OP and tok.value in INFIX_BP:
                lbp, rbp = INFIX_BP[tok.value]
                if lbp < min_bp:
                    break
                op_tok = self.advance()
                right = self.parse_expr(rbp)
                left = Binary(op_tok.value, left, right, op_tok.pos)
            else:
                break
        return left