from copy import deepcopy
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from smartcalc_web import app


class DummySelectEvent:
    """Simple stand-in for gradio.SelectData used in callbacks."""

    def __init__(self, index):
        self.index = index


def test_create_session_state_produces_clean_runtime():
    runtime = app._create_session_state()

    assert set(runtime.keys()) == {"evaluator", "history", "next_entry_id", "pending_guard"}
    assert runtime["history"] == []
    assert runtime["next_entry_id"] == 1
    assert runtime["pending_guard"] is None


def test_on_submit_evaluates_expression_and_logs_history():
    runtime = app._create_session_state()

    message, updated_runtime, rows, returned_expr = app._on_submit("2 + 3", runtime)

    assert "**5**" in message
    assert returned_expr == "2 + 3"
    assert updated_runtime is runtime
    assert len(updated_runtime["history"]) == 1
    history_entry = updated_runtime["history"][0]
    assert history_entry["expression"] == "2 + 3"
    assert history_entry["result"] == "5"
    assert history_entry["status"] == "Успех"
    assert history_entry["origin"] == "Вручную"
    assert "\x1b" not in history_entry["status"]
    assert rows[0][5] == "Вручную"


def test_on_submit_records_errors_without_escape_codes():
    runtime = app._create_session_state()

    message, runtime, rows, returned_expr = app._on_submit("7=8", runtime)

    assert "Ошибка при вычислении" in message
    assert "\x1b" not in message
    entry = runtime["history"][0]
    assert entry["status"].startswith("Ошибка:")
    assert "\x1b" not in entry["status"]
    assert rows[0][4].startswith("Ошибка:")


def test_history_select_replays_expression_with_existing_state_once():
    runtime = app._create_session_state()
    app._on_submit("a = 10", runtime)
    app._on_submit("a * 2", runtime)

    runtime["evaluator"].variables["a"] = 5

    message, runtime, rows, expr = app._on_history_select(DummySelectEvent(0), runtime)

    assert expr == "a * 2"
    assert "**10**" in message
    assert rows[0][4] == "Повтор"
    assert rows[0][5] == "Повтор"

    snapshot = deepcopy(runtime["history"])
    message_again, runtime, rows_again, expr_again = app._on_history_select(DummySelectEvent(0), runtime)

    assert message_again == message
    assert expr_again == "a * 2"
    assert runtime["history"] == snapshot
    assert runtime["pending_guard"] is None


def test_history_select_allows_subsequent_replays():
    runtime = app._create_session_state()
    app._on_submit("a = 0", runtime)
    app._on_submit("a = a + 1", runtime)

    runtime["evaluator"].variables["a"] = 0

    app._on_history_select(DummySelectEvent(0), runtime)
    assert runtime["evaluator"].variables["a"] == 1

    app._on_history_select(DummySelectEvent(0), runtime)
    assert runtime["evaluator"].variables["a"] == 1

    app._on_history_select(DummySelectEvent(0), runtime)
    assert runtime["evaluator"].variables["a"] == 2


def test_clear_resets_runtime_state():
    runtime = app._create_session_state()
    app._on_submit("2 + 2", runtime)

    message, cleared_runtime, rows, expr = app._on_clear(runtime)

    assert message.startswith("История очищена")
    assert cleared_runtime is not runtime
    assert cleared_runtime["history"] == []
    assert cleared_runtime["next_entry_id"] == 1
    assert cleared_runtime["pending_guard"] is None
    assert rows == []
    assert expr == ""
