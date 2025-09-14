class SmartCalcError(Exception):
    pass

class LexError(SmartCalcError):
    pass

class ParseError(SmartCalcError):
    pass

class NameResolutionError(SmartCalcError):
    pass

class EvalError(SmartCalcError):
    pass

def make_caret_message(message: str, text: str, pos: int) -> str:
    expanded = text.replace("\t", "    ")
    safe_pos = max(0, min(pos, len(text)))
    caret_pos = len(text[:safe_pos].replace("\t", "    "))
    caret_line = " " * caret_pos + "^"
    return f"{message}\n{expanded}\n{caret_line}"