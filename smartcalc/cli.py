import argparse, sys
from .api import parse
from .evaluator import Evaluator
from .errors import SmartCalcError

def repl():
    print("SmartCalc. Введите выражение (пустая строка — выход).")
    ev = Evaluator()
    while True:
        try:
            s = input('> ').strip()
            if not s:
                print('Пока!')
                break
            val = ev.eval(parse(s))
            if isinstance(val, float) and val.is_integer():
                val = int(val)
            print(val)
        except ZeroDivisionError:
            print('Ошибка: деление на ноль.')
        except SmartCalcError as e:
            print(f'Ошибка: {e}')
        except Exception as e:
            print(f'Ошибка выполнения: {e}')

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
                print(f'[строка {ln}] Ошибка: деление на ноль.')
            except SmartCalcError as e:
                had_err = True
                print(f'[строка {ln}] Ошибка: {e}')
            except Exception as e:
                had_err = True
                print(f'[строка {ln}] Ошибка выполнения: {e}')
    return 1 if had_err else 0

def main():
    ap = argparse.ArgumentParser(description='SmartCalc — безопасный парсер/вычислитель выражений.')
    ap.add_argument('-f','--file', help='Путь к .calc файлу (по одному выражению в строке).')
    args = ap.parse_args()
    if args.file:
        sys.exit(run_file(args.file))
    else:
        repl()

if __name__ == "__main__":
    main()