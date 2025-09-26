from __future__ import annotations

import math
import numbers
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

import gradio as gr

from smartcalc import api
from smartcalc.astnodes import PlotCommand
from smartcalc.evaluator import Evaluator
from smartcalc.errors import EvalError, SmartCalcError

HistoryEntry = Dict[str, Any]
RuntimeState = Dict[str, Any]


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _create_session_state() -> RuntimeState:
    return {
        "evaluator": Evaluator(),
        "history": [],
        "next_entry_id": 1,
        "pending_guard": None,
    }


def _format_result(value: Any) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, numbers.Real):
        float_value = float(value)
        if math.isfinite(float_value):
            if float_value.is_integer():
                return str(int(float_value))
            return f"{float_value:.10g}"
        return str(float_value)
    return str(value)


def _history_rows(history: List[HistoryEntry]) -> List[List[str]]:
    rows: List[List[str]] = []
    for entry in history:
        rows.append(
            [
                str(entry["entry_id"]),
                entry["timestamp"],
                entry["expression"],
                entry["result"],
                entry["status"],
                entry["origin"],
            ]
        )
    return rows


def _allocate_entry_id(runtime: RuntimeState) -> int:
    entry_id = runtime.setdefault("next_entry_id", 1)
    runtime["next_entry_id"] = entry_id + 1
    return entry_id


def _make_history_entry(
    runtime: RuntimeState,
    expression: str,
    result: str,
    status: str,
    origin_label: str,
    message: str,
) -> HistoryEntry:
    entry = {
        "entry_id": _allocate_entry_id(runtime),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "expression": expression,
        "result": result,
        "status": status,
        "origin": origin_label,
        "last_message": message,
    }
    runtime.setdefault("history", []).insert(0, entry)
    return entry


def _evaluate_expression(
    expression: str, runtime: RuntimeState, origin: str
) -> Tuple[str, RuntimeState, List[List[str]]]:
    if runtime is None:
        runtime = _create_session_state()

    expr = (expression or "").strip()
    if not expr:
        message = "Введите выражение (например: 2 + 2)."
        return message, runtime, _history_rows(runtime["history"])

    evaluator: Evaluator = runtime.setdefault("evaluator", Evaluator())

    if origin == "manual":
        status_label = "Успех"
        origin_label = "Вручную"
    else:
        status_label = "Повтор"
        origin_label = "Повтор"

    try:
        ast = api.parse(expr)
        if isinstance(ast, PlotCommand):
            raise EvalError("Команды plot сейчас работают только в консольной версии.")
        value = evaluator.eval(ast)
        formatted_result = _format_result(value)
        message = f"`{expr}` -> **{formatted_result}**"
        status = status_label
    except (SmartCalcError, EvalError) as exc:
        clean_message = _strip_ansi(str(exc))
        formatted_result = "-"
        message = f"Ошибка при вычислении `{expr}`: {clean_message}"
        status = f"Ошибка: {clean_message}"
    except Exception as exc:  # pragma: no cover
        formatted_result = "-"
        message = f"Непредвиденная ошибка при `{expr}`: {exc}"
        status = f"Ошибка: {exc}"

    _make_history_entry(runtime, expr, formatted_result, status, origin_label, message)
    rows = _history_rows(runtime["history"])
    return message, runtime, rows


def _on_submit(expression: str, runtime: RuntimeState):
    message, runtime, rows = _evaluate_expression(expression, runtime, origin="manual")
    runtime["pending_guard"] = None
    return message, runtime, rows, expression


def _on_history_select(evt: gr.SelectData, runtime: RuntimeState):
    runtime = runtime or _create_session_state()
    history = runtime["history"]
    if not history:
        info = "История пуста. Сначала выполните выражение."
        return info, runtime, _history_rows(history), ""

    index = evt.index
    if isinstance(index, (tuple, list)):
        index = index[0]

    if index is None:
        info = "Строка в истории не выбрана."
        return info, runtime, _history_rows(history), ""

    try:
        entry = history[int(index)]
    except (ValueError, TypeError, IndexError):
        info = "Не удалось определить выбранную строку истории."
        return info, runtime, _history_rows(history), ""

    guard_id = runtime.get("pending_guard")
    if guard_id == entry["entry_id"]:
        runtime["pending_guard"] = None
        message = entry.get(
            "last_message",
            f"`{entry['expression']}` -> **{entry['result']}**",
        )
        return message, runtime, _history_rows(history), entry["expression"]

    message, runtime, rows = _evaluate_expression(entry["expression"], runtime, origin="replay")
    latest_entry = runtime["history"][0]
    runtime["pending_guard"] = latest_entry["entry_id"]
    return message, runtime, rows, entry["expression"]


def _on_clear(runtime: RuntimeState):
    message = "История очищена. Можно вводить новые выражения."
    new_runtime = _create_session_state()
    return message, new_runtime, _history_rows(new_runtime["history"]), ""


def build_interface() -> gr.Blocks:
    with gr.Blocks(title="SmartCalc Web") as demo:
        runtime_state = gr.State()

        demo.load(fn=_create_session_state, inputs=None, outputs=runtime_state)

        gr.Markdown(
            "# SmartCalc Web\n"
            "Безопасно вычисляйте выражения, просматривайте историю и повторяйте вычисления."
        )

        with gr.Row():
            expression = gr.Textbox(
                label="Выражение",
                placeholder="Пример: sin(pi / 4) ** 2 + 1",
                lines=1,
            )
            with gr.Column(min_width=140):
                evaluate_btn = gr.Button("Вычислить", variant="primary")
                clear_btn = gr.Button("Очистить историю")

        result_display = gr.Markdown("Введите выражение и нажмите «Вычислить».")
        history_table = gr.Dataframe(
            headers=["№", "Время", "Выражение", "Результат", "Статус", "Источник"],
            datatype=["str", "str", "str", "str", "str", "str"],
            row_count=(0, "dynamic"),
            col_count=(6, "fixed"),
            interactive=False,
            label="История вычислений (сначала последние записи)",
        )

        evaluate_btn.click(
            fn=_on_submit,
            inputs=[expression, runtime_state],
            outputs=[result_display, runtime_state, history_table, expression],
        )

        history_table.select(
            fn=_on_history_select,
            inputs=[runtime_state],
            outputs=[result_display, runtime_state, history_table, expression],
        )

        clear_btn.click(
            fn=_on_clear,
            inputs=[runtime_state],
            outputs=[result_display, runtime_state, history_table, expression],
        )

    return demo


def main() -> None:
    build_interface().queue().launch()


if __name__ == "__main__":
    main()
