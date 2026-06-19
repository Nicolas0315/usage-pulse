"""Tests for CodexbarProvider."""

import json
from unittest.mock import MagicMock, patch

import pytest

from usage_pulse.providers.codexbar import CodexbarProvider


def _mock_run(stdout: str, returncode: int = 0):
    result = MagicMock()
    result.stdout = stdout
    result.returncode = returncode
    return result


CLAUDE_JSON = json.dumps(
    [
        {
            "provider": "claude",
            "source": "web",
            "usage": {
                "primary": {
                    "windowMinutes": 300,
                    "usedPercent": 42.5,
                    "resetsAt": "2026-06-19T12:00:00Z",
                    "resetDescription": "Resets at noon",
                },
                "secondary": {
                    "windowMinutes": 10080,
                    "usedPercent": 30.0,
                },
            },
        }
    ]
)

ERROR_JSON = json.dumps([{"provider": "amp", "source": "auto", "error": {"message": "No cookie"}}])


@pytest.fixture()
def provider():
    return CodexbarProvider(timeout=5)


def test_fetch_one_parses_claude(provider):
    with patch("subprocess.run", return_value=_mock_run(CLAUDE_JSON)):
        item = provider._fetch_one("claude", [])
    assert item is not None
    assert item["provider"] == "claude"
    assert item["usage"]["primary"]["usedPercent"] == pytest.approx(42.5)


def test_fetch_one_returns_none_on_error_json(provider):
    with patch("subprocess.run", return_value=_mock_run(ERROR_JSON, returncode=1)):
        item = provider._fetch_one("amp", [])
    assert item is None


def test_fetch_one_returns_none_on_empty(provider):
    with patch("subprocess.run", return_value=_mock_run("")):
        item = provider._fetch_one("claude", [])
    assert item is None


def test_default_timeout_can_be_overridden(monkeypatch):
    monkeypatch.setenv("USAGE_PULSE_CODEXBAR_TIMEOUT", "2")
    assert CodexbarProvider().timeout == 2


def test_default_timeout_ignores_invalid_env(monkeypatch):
    monkeypatch.setenv("USAGE_PULSE_CODEXBAR_TIMEOUT", "not-a-number")
    assert CodexbarProvider().timeout == 4


def test_fetch_rate_windows_aggregates(provider):
    def fake_run(cmd, **kwargs):
        provider_arg = cmd[cmd.index("--provider") + 1]
        if provider_arg == "claude":
            return _mock_run(CLAUDE_JSON)
        return _mock_run(ERROR_JSON, returncode=1)

    with (
        patch("subprocess.run", side_effect=fake_run),
        patch("platform.system", return_value="Darwin"),
        patch("shutil.which", return_value="/usr/bin/codexbar"),
    ):
        windows = provider.fetch_rate_windows()

    assert "claude" in windows
    assert windows["claude"]["primary_pct"] == pytest.approx(42.5)
    assert windows["claude"]["secondary_pct"] == pytest.approx(30.0)
    assert windows["claude"]["label"] == "CC"


def test_format_tmux_colors(provider):
    windows = {
        "claude": {"label": "CC", "primary_pct": 95.0, "secondary_pct": 30.0},
        "gemini": {"label": "GM", "primary_pct": 10.0, "secondary_pct": 0.0},
    }
    out = provider.format_tmux(windows)
    assert "red" in out  # 95% → red
    assert "green" in out  # 10% → green
    assert "CC:95%" in out
    assert "GM:10%" in out


def test_enrich_usage_data(provider):
    from usage_pulse.providers.base import UsageData

    data = UsageData(date="2026-06-19", cost_usd=5.0, input_tokens=10000, output_tokens=2000)
    windows = {
        "claude": {
            "label": "CC",
            "primary_pct": 42.5,
            "secondary_pct": 30.0,
            "primary_resets_at": "2026-06-19T12:00:00Z",
            "primary_reset_desc": "Resets at noon",
            "primary_window_minutes": 300,
        }
    }
    data = provider.enrich_usage_data(data, windows)
    assert data.primary_rate_pct == pytest.approx(42.5)
    assert data.weekly_rate_pct == pytest.approx(30.0)
