import csv
from pathlib import Path

import pytest

from smartcalc.api import parse
from smartcalc.evaluator import Evaluator
from smartcalc.errors import EvalError
from smartcalc.plotting import execute_plot

plotly = pytest.importorskip("plotly", reason="для тестов графиков необходим plotly")


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    return rows


def test_execute_plot_generates_csv(tmp_path):
    command = parse("plot sin(x) from -3.14 to 3.14 target csv")
    result = execute_plot(command, Evaluator(), show=False, output_dir=tmp_path)

    assert result.target_path is not None
    assert result.target_path.suffix == ".csv"
    assert result.target_path.exists()
    assert result.message.startswith("График сохранён в")

    assert result.domain[0] == pytest.approx(-3.14, rel=1e-4)
    assert result.domain[1] == pytest.approx(3.14, rel=1e-4)
    assert result.x_values[0] == pytest.approx(result.domain[0])
    assert result.x_values[-1] == pytest.approx(result.domain[1])
    assert len(result.x_values) == len(result.y_values)
    assert any(y is not None for y in result.y_values)

    rows = _read_csv(result.target_path)
    assert len(rows) == len(result.x_values)
    assert set(rows[0].keys()) == {"x", "y"}


def test_execute_plot_handles_invalid_points(tmp_path):
    command = parse("plot sqrt(x)")
    result = execute_plot(command, Evaluator(), show=False, output_dir=tmp_path)

    assert result.variable == "x"
    assert result.label == "f(x)"
    assert any(y is None for y in result.y_values)
    assert any(y is not None for y in result.y_values)


def test_execute_plot_respects_custom_variable(tmp_path):
    command = parse("plot f(t) = t**2 from -1 to 1")
    result = execute_plot(command, Evaluator(), show=False, output_dir=tmp_path)

    assert result.variable == "t"
    assert result.label == "f(t)"
    assert result.domain[0] == pytest.approx(-1.0)
    assert result.domain[1] == pytest.approx(1.0)


def test_execute_plot_png_export(tmp_path):
    command = parse("plot sin(x) from 0 to 1 target png")
    evaluator = Evaluator()
    try:
        result = execute_plot(command, evaluator, show=False, output_dir=tmp_path)
    except EvalError as exc:
        if "kaleido" in str(exc).lower():
            pytest.skip("движок kaleido недоступен")
        raise

    assert result.target_path is not None
    assert result.target_path.suffix == ".png"
    assert result.target_path.exists()
