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


try:
    from colorama import Fore, Style
except ImportError:  # pragma: no cover - fallback for environments without colorama
    class _NoColor:
        def __getattr__(self, _):
            return ''

    Fore = _NoColor()
    Style = _NoColor()

RESET = getattr(Style, 'RESET_ALL', '')


def _apply_color(text: str, *codes: str) -> str:
    prefix = ''.join(code for code in codes if code)
    if not prefix:
        return text
    return f"{prefix}{text}{RESET}"


def make_caret_message(message: str, text: str, pos: int) -> str:
    expanded = text.replace('\t', '    ')
    safe_pos = max(0, min(pos, len(text)))
    caret_pos = len(text[:safe_pos].replace('\t', '    '))
    caret_line = ' ' * caret_pos + _apply_color('^', Style.BRIGHT, getattr(Fore, 'YELLOW', ''))
    message_line = _apply_color(message, Style.BRIGHT, getattr(Fore, 'RED', ''))
    source_line = _apply_color(expanded, getattr(Fore, 'CYAN', ''))
    return f"{message_line}\n{source_line}\n{caret_line}"
