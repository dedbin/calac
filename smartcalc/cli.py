import argparse
import sys

from .api import parse
from .evaluator import Evaluator
from .errors import SmartCalcError

try:
    from colorama import Fore, Style, just_fix_windows_console
except ImportError:  # pragma: no cover - fallback for environments without colorama
    class _NoColor:
        def __getattr__(self, _):
            return ''

    Fore = _NoColor()
    Style = _NoColor()

    def just_fix_windows_console():
        return None
else:
    just_fix_windows_console()

RESET = getattr(Style, 'RESET_ALL', '')


def _apply_color(text: str, *codes: str) -> str:
    prefix = ''.join(code for code in codes if code)
    if not prefix:
        return text
    return f"{prefix}{text}{RESET}"


def _line_label(line_no: int) -> str:
    label = f"[line {line_no}]"
    return _apply_color(label, Style.BRIGHT, getattr(Fore, 'MAGENTA', ''))


ERROR_LABEL = _apply_color('Error:', Style.BRIGHT, getattr(Fore, 'RED', ''))
PROMPT = _apply_color('> ', Style.BRIGHT, getattr(Fore, 'CYAN', ''))
BYE_MESSAGE = 'Пока!'


def _emit_error(message: str) -> None:
    print(message, file=sys.stderr)


def repl() -> None:
    print("SmartCalc. Введите выражение (пустая строка — выход).")
    ev = Evaluator()
    while True:
        try:
            s = input(PROMPT).strip()
        except EOFError:
            print()
            break
        if not s:
            print(BYE_MESSAGE)
            break
        try:
            val = ev.eval(parse(s))
            if isinstance(val, float) and val.is_integer():
                val = int(val)
            print(val)
        except ZeroDivisionError:
            _emit_error(f'{ERROR_LABEL} деление на ноль.')
        except SmartCalcError as e:
            _emit_error(f'{ERROR_LABEL} {e}')
        except Exception as e:  # pragma: no cover - defensive fallback
            _emit_error(f'{ERROR_LABEL} : Ошибка выполнения: {e}')


def run_file(path: str) -> int:
    ev = Evaluator()
    had_err = False
    with open(path, 'r', encoding='utf-8') as f:
        for ln, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            try:
                val = ev.eval(parse(line))
                if isinstance(val, float) and val.is_integer():
                    val = int(val)
                print(val)
            except ZeroDivisionError:
                had_err = True
                _emit_error(f'{_line_label(ln)} {ERROR_LABEL} деление на ноль.')
            except SmartCalcError as e:
                had_err = True
                _emit_error(f'{_line_label(ln)} {ERROR_LABEL} {e}')
            except Exception as e:  # pragma: no cover - defensive fallback
                had_err = True
                _emit_error(f'{_line_label(ln)} {ERROR_LABEL} Ошибка выполнения: {e}')
    return 1 if had_err else 0


def main() -> None:
    ap = argparse.ArgumentParser(description='SmartCalc — безопасный парсер/вычислитель выражений.')
    ap.add_argument('-f', '--file', help='Путь к .calc файлу (по одному выражению в строке).')
    args = ap.parse_args()
    if args.file:
        sys.exit(run_file(args.file))
    repl()


if __name__ == '__main__':
    main()
