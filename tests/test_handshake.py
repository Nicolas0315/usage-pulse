"""Tests for agent handshake state file."""
import json
import pytest
from pathlib import Path
from src.usage_pulse.providers.base import UsageData, RateWindow
from src.usage_pulse.analysis.advisor import ModelAdvisor, Recommendation
from src.usage_pulse.handshake import write_state, read_state, STATE_FILE


@pytest.fixture(autouse=True)
def cleanup_state():
    yield
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def _make_data():
    d = UsageData(
        date="2026-06-19",
        cost_usd=12.5,
        input_tokens=100_000,
        output_tokens=20_000,
    )
    d.rate_windows["primary"] = RateWindow(window_minutes=300, used_percent=22.0)
    d.rate_windows["secondary"] = RateWindow(window_minutes=10080, used_percent=35.0)
    return d


def test_write_and_read_state():
    data = _make_data()
    advisor = ModelAdvisor()
    rec = advisor.recommend(data)
    write_state(data, rec)

    state = read_state()
    assert state is not None
    assert state["today"]["cost_usd"] == pytest.approx(12.5)
    assert state["today"]["tokens"] == 120_000
    assert state["rate_windows"]["claude_5min_pct"] == pytest.approx(22.0)
    assert "model" in state["recommendation"]


def test_state_has_required_keys():
    write_state(_make_data(), ModelAdvisor().recommend(_make_data()))
    state = json.loads(STATE_FILE.read_text())
    assert "updated_at" in state
    assert "today" in state
    assert "rate_windows" in state
    assert "recommendation" in state
