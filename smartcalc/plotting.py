from __future__ import annotations

import csv
import math
import numbers
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

import numpy as np

try:  # pragma: no cover - import guarded to provide friendly error
    import plotly.graph_objects as go
    from plotly import io as pio
except ImportError:  # pragma: no cover
    go = None  # type: ignore
    pio = None  # type: ignore

from .astnodes import PlotCommand
from .constants import DEFAULT_CONSTANTS
from .evaluator import Evaluator, PROTECTED_NAMES
from .errors import EvalError, SmartCalcError

_ALLOWED_TARGETS = {"png", "svg", "csv"}
_DEFAULT_DOMAIN = (-10.0, 10.0)
_BASE_SAMPLE_COUNT = 128
_MAX_SAMPLE_COUNT = 4096
_SLOPE_THRESHOLD = 25.0


@dataclass
class PlotExecution:
    command: PlotCommand
    x_values: List[float]
    y_values: List[Optional[float]]
    domain: Tuple[float, float]
    variable: str
    label: str
    target_format: Optional[str]
    target_path: Optional[Path]
    figure: Any
    message: str


def execute_plot(
    command: PlotCommand,
    evaluator: Evaluator,
    *,
    show: bool = True,
    output_dir: Optional[Path] = None,
) -> PlotExecution:
    clone = _clone_evaluator(evaluator)
    variable = _resolve_variable(command, clone)
    label = command.label or f"f({variable})"
    domain = _resolve_domain(command, clone)
    x_values, y_values = _sample_function(clone, command.expr, variable, domain)

    target_format = None
    target_path: Optional[Path] = None
    if command.target:
        target_format = command.target.format.lower()
        if target_format not in _ALLOWED_TARGETS:
            allowed = ', '.join(sorted(_ALLOWED_TARGETS))
            raise EvalError(f"Формат вывода '{target_format}' не поддерживается. Допустимо: {allowed}.")
    fig = _build_figure(x_values, y_values, variable, label)

    if target_format:
        output_dir = output_dir or (Path.cwd() / "plots")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        base_name = f"plot-{variable}-{timestamp}.{target_format}"
        target_path = output_dir / base_name
        if target_format == "csv":
            _export_csv(target_path, x_values, y_values)
        else:
            _write_image(fig, target_path, target_format)
        message = f"График сохранён в {target_path}"
    else:
        if show:
            message = _show_figure(fig)
        else:
            message = "Интерактивный показ пропущен (неинтерактивный режим)."

    return PlotExecution(
        command=command,
        x_values=x_values,
        y_values=y_values,
        domain=domain,
        variable=variable,
        label=label,
        target_format=target_format,
        target_path=target_path,
        figure=fig,
        message=message,
    )


def _clone_evaluator(evaluator: Evaluator) -> Evaluator:
    clone = Evaluator(constants=evaluator.constants)
    clone.variables = dict(evaluator.variables)
    return clone


def _resolve_variable(command: PlotCommand, evaluator: Evaluator) -> str:
    if command.variable:
        name = command.variable
    else:
        candidates = _collect_variable_candidates(command.expr)
        name = sorted(candidates)[0] if candidates else "x"
    lowered = name.lower()
    if lowered in PROTECTED_NAMES or lowered in DEFAULT_CONSTANTS:
        raise EvalError(f"Нельзя использовать имя '{name}' для переменной графика.")
    return name


def _collect_variable_candidates(node) -> set[str]:
    from .astnodes import Call, Const, Unary, Binary, Assign

    result: set[str] = set()

    def visit(n):
        if isinstance(n, Const):
            result.add(n.name)
        elif isinstance(n, Call):
            for arg in n.args:
                visit(arg)
        elif isinstance(n, Unary):
            visit(n.expr)
        elif isinstance(n, Binary):
            visit(n.left)
            visit(n.right)
        elif isinstance(n, Assign):
            visit(n.expr)

    visit(node)
    return {name for name in result if name.lower() not in DEFAULT_CONSTANTS and name.lower() not in PROTECTED_NAMES}


def _resolve_domain(command: PlotCommand, evaluator: Evaluator) -> Tuple[float, float]:
    if command.domain_start and command.domain_end:
        start = _eval_to_float(evaluator, command.domain_start, "начало диапазона")
        end = _eval_to_float(evaluator, command.domain_end, "конец диапазона")
    else:
        start, end = _DEFAULT_DOMAIN
    if not math.isfinite(start) or not math.isfinite(end):
        raise EvalError("Границы графика должны быть конечными числами.")
    if start == end:
        raise EvalError("Границы графика не должны совпадать.")
    if start > end:
        start, end = end, start
    return float(start), float(end)


def _eval_to_float(evaluator: Evaluator, node, what: str) -> float:
    try:
        value = evaluator.eval(node)
    except SmartCalcError as exc:
        raise EvalError(f"Не удалось вычислить {what}: {exc}") from exc
    if not isinstance(value, numbers.Real):
        raise EvalError(f"{what.capitalize()} должно быть вещественным числом.")
    return float(value)


def _sample_function(evaluator: Evaluator, expr, variable: str, domain: Tuple[float, float]) -> Tuple[List[float], List[Optional[float]]]:
    start, end = domain
    if start > end:
        start, end = end, start

    count = _BASE_SAMPLE_COUNT
    best_x: List[float] = []
    best_y: List[Optional[float]] = []

    while count <= _MAX_SAMPLE_COUNT:
        xs = np.linspace(start, end, count)
        ys: List[Optional[float]] = []
        for x in xs:
            try:
                y_raw = _evaluate_at(evaluator, expr, variable, float(x))
            except (SmartCalcError, ZeroDivisionError, ValueError):
                ys.append(None)
                continue
            if not isinstance(y_raw, numbers.Real):
                ys.append(None)
                continue
            y = float(y_raw)
            if not math.isfinite(y):
                ys.append(None)
                continue
            ys.append(y)

        slope = _max_slope(xs, ys)
        best_x = [float(x) for x in xs]
        best_y = ys
        if slope is None or slope <= _SLOPE_THRESHOLD or count == _MAX_SAMPLE_COUNT:
            break
        count *= 2

    valid_points = sum(1 for y in best_y if y is not None)
    if valid_points < 2:
        raise EvalError("Команда plot дала меньше двух допустимых точек. Измените диапазон.")
    return best_x, best_y


def _evaluate_at(evaluator: Evaluator, expr, variable: str, value: float):
    var_name = variable.lower()
    sentinel = object()
    previous = evaluator.variables.get(var_name, sentinel)
    evaluator.variables[var_name] = value
    try:
        return evaluator.eval(expr)
    finally:
        if previous is sentinel:
            evaluator.variables.pop(var_name, None)
        else:
            evaluator.variables[var_name] = previous


def _max_slope(xs: Sequence[float], ys: Sequence[Optional[float]]) -> Optional[float]:
    max_value: Optional[float] = None
    for i in range(len(xs) - 1):
        y1 = ys[i]
        y2 = ys[i + 1]
        if y1 is None or y2 is None:
            continue
        dx = xs[i + 1] - xs[i]
        if dx == 0:
            continue
        slope = abs((y2 - y1) / dx)
        if not math.isfinite(slope):
            continue
        if max_value is None or slope > max_value:
            max_value = slope
    return max_value


def _build_figure(x_values: List[float], y_values: List[Optional[float]], variable: str, label: str):
    if go is None:
        raise EvalError("Для построения графиков требуется библиотека plotly. Установите её командой 'pip install plotly'.")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=x_values, y=y_values, mode="lines", name=label, line=dict(width=2))
    )
    fig.update_layout(
        xaxis_title=variable,
        yaxis_title=label,
        template="plotly_white",
        showlegend=False,
    )
    return fig


def _export_csv(path: Path, xs: List[float], ys: List[Optional[float]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["x", "y"])
        for x, y in zip(xs, ys):
            if y is None:
                writer.writerow([f"{x:.12g}", ""])
            else:
                writer.writerow([f"{x:.12g}", f"{y:.12g}"])


def _write_image(fig, path: Path, fmt: str) -> None:
    if pio is None:
        raise EvalError(
            "Сохранение изображений доступно только при установленном plotly с движком 'kaleido'. Установите их: 'pip install plotly kaleido'."
        )
    try:
        pio.write_image(fig, str(path), format=fmt)
    except ValueError as exc:
        raise EvalError(
            "Для экспорта изображений необходим движок 'kaleido'. Установите его: 'pip install kaleido'."
        ) from exc


def _show_figure(fig) -> str:
    if go is None:
        raise EvalError("Для отображения графиков требуется библиотека plotly. Установите её командой 'pip install plotly'.")
    try:
        fig.show(renderer="browser")
        return "График открыт в браузере по умолчанию."
    except Exception as exc:  # pragma: no cover
        return f"Не удалось автоматически открыть интерактивный график: {exc}"
