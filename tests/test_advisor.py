"""Tests for model advisor."""

from usage_pulse.analysis.advisor import ModelAdvisor
from usage_pulse.providers.base import RateWindow, UsageData


def _make_data(cost=0.0, primary_pct=0.0, weekly_pct=0.0) -> UsageData:
    d = UsageData(
        date="2026-06-19",
        cost_usd=cost,
        input_tokens=100_000,
        output_tokens=20_000,
    )
    d.rate_windows["primary"] = RateWindow(window_minutes=300, used_percent=primary_pct)
    d.rate_windows["secondary"] = RateWindow(window_minutes=10080, used_percent=weekly_pct)
    return d


def test_ok_state():
    advisor = ModelAdvisor()
    rec = advisor.recommend(_make_data(cost=5.0, primary_pct=20.0), cost_threshold=50.0)
    assert rec.urgency == "ok"
    assert "sonnet" in rec.model


def test_critical_rate_window():
    advisor = ModelAdvisor()
    rec = advisor.recommend(_make_data(primary_pct=92.0), cost_threshold=50.0)
    assert rec.urgency == "critical"
    assert "haiku" in rec.model


def test_warning_rate_window():
    advisor = ModelAdvisor()
    rec = advisor.recommend(_make_data(primary_pct=85.0), cost_threshold=50.0)
    assert rec.urgency == "warning"
    assert "haiku" in rec.model


def test_cost_warning():
    advisor = ModelAdvisor()
    rec = advisor.recommend(_make_data(cost=48.0), cost_threshold=50.0)
    assert rec.urgency == "warning"
    assert "haiku" in rec.model


def test_cost_caution():
    advisor = ModelAdvisor()
    rec = advisor.recommend(_make_data(cost=36.0), cost_threshold=50.0)
    assert rec.urgency == "caution"
    assert "sonnet" in rec.model
