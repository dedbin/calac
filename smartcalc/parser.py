from __future__ import annotations
from typing import List, Optional, Tuple
from .tokens import (
    Token,
    K_NUM,
    K_IDENT,
    K_OP,
    K_LP,
    K_RP,
    K_COMMA,
    K_EOF,
    K_ASSIGN,
    K_PLOT,
    K_FROM,
    K_TO,
    K_TARGET,
)
from .astnodes import AST, Num, Const, Call, Unary, Binary, Assign, PlotCommand, PlotTarget
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
                f"Ожидалось {expected}, получено {tok.kind}('{tok.value}')", self.text, tok.pos
            ))
        self.advance()
        return tok

    def parse(self) -> AST:
        node = self.parse_statement()
        if self.peek().kind != K_EOF:
            tok = self.peek()
            raise ParseError(make_caret_message(
                f"Лишний ввод, начиная с позиции {tok.pos}: '{tok.value}'", self.text, tok.pos
            ))
        return node

    def parse_statement(self) -> AST:
        tok = self.peek()
        if tok.kind == K_PLOT:
            return self.parse_plot()
        return self.parse_assignment()

    def parse_assignment(self) -> AST:
        if self.peek().kind == K_IDENT and self.lookahead(1).kind == K_ASSIGN:
            ident_tok = self.advance()
            self.advance()
            value = self.parse_assignment()
            return Assign(str(ident_tok.value), value, ident_tok.pos)
        return self.parse_expr(0)

    def parse_plot(self) -> AST:
        plot_tok = self.expect(K_PLOT)
        label: Optional[str] = None
        variable: Optional[str] = None
        domain_start: Optional[AST] = None
        domain_end: Optional[AST] = None
        target: Optional[PlotTarget] = None

        if self._has_assign_before_stop():
            label, variable = self._parse_plot_signature()
            self.expect(K_ASSIGN)

        expr = self.parse_expr(0)

        while True:
            tok = self.peek()
            if tok.kind == K_FROM and domain_start is None:
                self.advance()
                domain_start = self.parse_expr(0)
                self.expect(K_TO)
                domain_end = self.parse_expr(0)
            elif tok.kind == K_TARGET and target is None:
                self.advance()
                fmt_tok = self.peek()
                if fmt_tok.kind != K_IDENT:
                    raise ParseError(make_caret_message(
                        "После 'target' ожидается идентификатор", self.text, fmt_tok.pos
                    ))
                fmt_tok = self.expect(K_IDENT)
                fmt = str(fmt_tok.value).lower()
                target = PlotTarget(fmt, None, fmt_tok.pos)
            else:
                break

        return PlotCommand(
            expr=expr,
            variable=variable,
            label=label,
            domain_start=domain_start,
            domain_end=domain_end,
            target=target,
            pos=plot_tok.pos,
        )

    def _has_assign_before_stop(self) -> bool:
        idx = self.i
        stop_kinds = {K_EOF, K_FROM, K_TARGET}
        while idx < len(self.tokens):
            tok = self.tokens[idx]
            if tok.kind == K_ASSIGN:
                return True
            if tok.kind in stop_kinds:
                return False
            idx += 1
        return False

    def _parse_plot_signature(self) -> Tuple[str, Optional[str]]:
        name_tok = self.expect(K_IDENT)
        name = str(name_tok.value)
        variable: Optional[str] = None
        if self.peek().kind == K_LP:
            self.advance()
            param_tok = self.expect(K_IDENT)
            variable = str(param_tok.value)
            self.expect(K_RP)
            label = f"{name}({variable})"
        else:
            label = name
        return label, variable

    def parse_expr(self, min_bp: int) -> AST:
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
