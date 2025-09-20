from __future__ import annotations

import math
import numbers
from datetime import datetime
from typing import Any, Dict, List, Tuple

import gradio as gr

from smartcalc import api
from smartcalc.evaluator import Evaluator

HistoryEntry = Dict[str, Any]
RuntimeState = Dict[str, Any]


def _create_session_state() -> RuntimeState:
    return {
        "evaluator": Evaluator(),
        "history": [],  # newest entry first
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
    for idx, entry in enumerate(history, start=1):
        rows.append(
            [
                str(idx),
                entry["timestamp"],
                entry["expression"],
                entry["result"],
                entry["status"],
                entry["origin"],
            ]
        )
    return rows


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
    timestamp = datetime.now().strftime("%H:%M:%S")

    try:
        ast = api.parse(expr)
        result_value = evaluator.eval(ast)
        formatted_result = _format_result(result_value)
        status = "Успешно" if origin == "manual" else "Воспроизведено"
        entry: HistoryEntry = {
            "expression": expr,
            "result": formatted_result,
            "status": status,
            "origin": "Вручную" if origin == "manual" else "Воспроизведение",
            "timestamp": timestamp,
        }
        runtime["history"].insert(0, entry)
        message = f"`{expr}` -> **{formatted_result}**"
    except Exception as exc:  # pragma: no cover - runtime display only
        entry = {
            "expression": expr,
            "result": "-",
            "status": f"Ошибка: {exc}",
            "origin": "Вручную" if origin == "manual" else "Воспроизведение",
            "timestamp": timestamp,
        }
        runtime["history"].insert(0, entry)
        message = f"Ошибка при вычислении `{expr}`: {exc}"
    return message, runtime, _history_rows(runtime["history"])


def _on_submit(expression: str, runtime: RuntimeState):
    message, runtime, rows = _evaluate_expression(expression, runtime, origin="manual")
    return message, runtime, rows, expression


def _on_history_select(evt: gr.SelectData, runtime: RuntimeState):
    runtime = runtime or _create_session_state()
    if not runtime["history"]:
        info = "История пуста. Сначала вычислите выражение."
        return info, runtime, _history_rows(runtime["history"]), ""

    index = evt.index
    if isinstance(index, (tuple, list)):
        row_idx = index[0]
    else:
        row_idx = index

    if row_idx is None:
        info = "Выберите строку истории для воспроизведения."
        return info, runtime, _history_rows(runtime["history"]), ""

    try:
        entry = runtime["history"][int(row_idx)]
    except (IndexError, ValueError, TypeError):
        info = "Выберите корректную запись истории для воспроизведения."
        return info, runtime, _history_rows(runtime["history"]), ""

    message, runtime, rows = _evaluate_expression(entry["expression"], runtime, origin="replay")
    return message, runtime, rows, entry["expression"]


def _on_clear(runtime: RuntimeState):
    runtime = _create_session_state()
    message = "История очищена и калькулятор сброшен."
    return message, runtime, _history_rows(runtime["history"]), ""


def build_interface() -> gr.Blocks:
    with gr.Blocks(title="SmartCalc Web") as demo:
        runtime_state = gr.State()

        demo.load(fn=_create_session_state, inputs=None, outputs=runtime_state)

        gr.Markdown(
            "# SmartCalc Web\n"
            "Вычисляйте выражения SmartCalc прямо в браузере. "
            "Присваивания и переменные сохраняются в памяти вашей сессии.\n"
            "Нажмите на строку истории, чтобы воспроизвести её с текущим состоянием."
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
            label="История сессии (нажмите строку для воспроизведения)",
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

