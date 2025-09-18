from __future__ import annotations
from typing import List
from .tokens import Token, K_NUM, K_IDENT, K_OP, K_LP, K_RP, K_COMMA, K_EOF, K_ASSIGN
from .astnodes import AST, Num, Const, Call, Unary, Binary, Assign
from .precedence import INFIX_BP, PREFIX_BP
from .errors import ParseError, make_caret_message


class Parser:
    def __init__(self, text: str, tokens: List[Token]):
        self.text = text
        self.tokens = tokens
        self.i = 0

    def peek(self) -> Token:
        return self.tokens[self.i]

    def lookahead(self, n: int) -> Token:
        idx = self.i + n
        if idx >= len(self.tokens):
            idx = len(self.tokens) - 1
        return self.tokens[idx]

    def advance(self) -> Token:
        tok = self.peek()
        if tok.kind != K_EOF:
            self.i += 1
        return tok

    def expect(self, kind: str, value=None) -> Token:
        tok = self.peek()
        if tok.kind != kind or (value is not None and tok.value != value):
            expected = f"{kind}('{value}')" if value is not None else kind
            raise ParseError(make_caret_message(
                f"Ожидается {expected}, найдено {tok.kind}('{tok.value}')", self.text, tok.pos
            ))
        self.advance()
        return tok

    def parse(self) -> AST:
        node = self.parse_assignment()
        if self.peek().kind != K_EOF:
            tok = self.peek()
            raise ParseError(make_caret_message(
                f"Лишний ввод начиная с позиции {tok.pos}: '{tok.value}'", self.text, tok.pos
            ))
        return node

    def parse_assignment(self) -> AST:
        if self.peek().kind == K_IDENT and self.lookahead(1).kind == K_ASSIGN:
            ident_tok = self.advance()
            self.advance()
            value = self.parse_assignment()
            return Assign(str(ident_tok.value), value, ident_tok.pos)
        return self.parse_expr(0)

    def parse_expr(self, min_bp: int) -> AST:
        # nud
        tok = self.peek()
        if tok.kind == K_NUM:
            self.advance()
            left: AST = Num(tok.value, tok.pos)
        elif tok.kind == K_IDENT:
            self.advance()
            name = str(tok.value)
            if self.peek().kind == K_LP:
                self.advance()
                args = []
                if self.peek().kind != K_RP:
                    while True:
                        args.append(self.parse_expr(0))
                        if self.peek().kind == K_COMMA:
                            self.advance()
                        else:
                            break
                self.expect(K_RP)
                left = Call(name, args, tok.pos)
            else:
                left = Const(name, tok.pos)
        elif tok.kind == K_OP and tok.value in ('+', '-'):
            op_tok = self.advance()
            right = self.parse_expr(PREFIX_BP)
            left = Unary(op_tok.value, right, op_tok.pos)
        elif tok.kind == K_LP:
            self.advance()
            left = self.parse_expr(0)
            self.expect(K_RP)
        else:
            raise ParseError(make_caret_message(
                f"Неожиданный токен {tok.kind}('{tok.value}')", self.text, tok.pos
            ))

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