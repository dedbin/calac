from __future__ import annotations
from typing import List
from .tokens import Token, K_NUM, K_IDENT, K_OP, K_LP, K_RP, K_EOF
from .errors import LexError

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.i = 0
        self.n = len(text)

    def peek(self) -> str:
        return self.text[self.i] if self.i < self.n else ''

    def advance(self) -> str:
        ch = self.peek()
        self.i += 1
        return ch

    def at_end(self) -> bool:
        return self.i >= self.n

    def skip_ws(self):
        while not self.at_end() and self.peek().isspace():
            self.advance()

    def lex_number(self) -> Token:
        start = self.i
        seen_dot = False
        seen_exp = False

        def is_dig_or_underscore(c: str) -> bool:
            return c.isdigit() or c == '_'
        # целая часть
        while not self.at_end() and is_dig_or_underscore(self.peek()):
            self.advance()
        # дробная часть
        if not self.at_end() and self.peek() == '.':
            seen_dot = True
            self.advance()
            while not self.at_end() and is_dig_or_underscore(self.peek()):
                self.advance()
        # экспонента
        if not self.at_end() and self.peek() in 'eE':
            seen_exp = True
            self.advance()
            if not self.at_end() and self.peek() in '+-':
                self.advance()
            while not self.at_end() and is_dig_or_underscore(self.peek()):
                self.advance()

        lexeme = self.text[start:self.i]
        cleaned = lexeme.replace('_', '')
        pos = start

        try:
            if seen_dot or seen_exp:
                val = float(cleaned)
            else:
                if cleaned in ('', '.'):
                    val = float(cleaned)  # вызовет ошибку
                else:
                    val = int(cleaned)
            return Token(K_NUM, val, pos)
        except Exception:
            try:
                val = float(cleaned)
                return Token(K_NUM, val, pos)
            except Exception:
                raise LexError(f"Некорректное число '{lexeme}' на позиции {pos}")

    def lex_ident(self) -> Token:
        start = self.i
        self.advance()  # первый символ a..z/_ уже проверен
        while not self.at_end() and (self.peek().isalnum() or self.peek() == '_'):
            self.advance()
        ident = self.text[start:self.i]
        return Token(K_IDENT, ident, start)

    def next_token(self) -> Token:
        self.skip_ws()
        if self.at_end():
            return Token(K_EOF, None, self.i)

        ch = self.peek()
        pos = self.i

        # число: цифра или .цифра
        if ch.isdigit() or (ch == '.' and self.i + 1 < self.n and self.text[self.i+1].isdigit()):
            return self.lex_number()

        # идентификатор
        if ch.isalpha() or ch == '_':
            return self.lex_ident()

        # скобки
        if ch == '(':
            self.advance()
            return Token(K_LP, '(', pos)
        if ch == ')':
            self.advance()
            return Token(K_RP, ')', pos)

        # операторы (двухсимвольные сначала)
        two = self.text[self.i:self.i+2]
        if two in ('**', '//'):
            self.i += 2
            return Token(K_OP, two, pos)
        if ch in '+-*/%':
            self.advance()
            return Token(K_OP, ch, pos)

        bad = self.advance()
        raise LexError(f"Неожиданный символ '{bad}' на позиции {pos}")

    def tokenize(self) -> List[Token]:
        out = []
        while True:
            tok = self.next_token()
            out.append(tok)
            if tok.kind == K_EOF:
                break
        return out
