from dataclasses import dataclass
from typing import Optional, Union

K_NUM   = 'NUM'
K_IDENT = 'IDENT'
K_OP    = 'OP'
K_ASSIGN = 'ASSIGN'
K_LP    = 'LPAREN'
K_RP    = 'RPAREN'
K_COMMA = 'COMMA'
K_EOF   = 'EOF'

@dataclass(frozen=True)
class Token:
    kind: str
    value: Optional[Union[str, int, float]]
    pos: int