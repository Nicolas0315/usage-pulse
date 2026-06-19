"""Agent handshake: write usage state to a shared file for AI agents to read."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from .analysis.advisor import Recommendation
from .io import write_text_atomic
from .providers.base import UsageData

STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "usage-pulse"
STATE_FILE = STATE_DIR / "current.json"


def write_state(data: UsageData, rec: Recommendation) -> None:
    """Write current usage state for agent consumption."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    state = {
        "updated_at": datetime.now(UTC).isoformat(),
        "today": {
            "cost_usd": round(data.cost_usd, 4),
            "tokens": data.total_tokens,
            "input_tokens": data.input_tokens,
            "output_tokens": data.output_tokens,
            "top_models": [m.model_name for m in data.top_models[:3] if m.cost_usd > 0],
        },
        "rate_windows": {
            "claude_5min_pct": round(data.primary_rate_pct, 1),
            "claude_weekly_pct": round(data.weekly_rate_pct, 1),
        },
        "recommendation": {
            "model": rec.model,
            "reason": rec.reason,
            "urgency": rec.urgency,
        },
    }
    write_text_atomic(STATE_FILE, json.dumps(state, ensure_ascii=False, indent=2))


def read_state() -> dict | None:
    """Read the latest state file. Returns None if missing or stale (>5min)."""
    if not STATE_FILE.exists():
        return None
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        updated = datetime.fromisoformat(state["updated_at"])
        age = (datetime.now(UTC) - updated).total_seconds()
        if age > 300:  # 5 minutes
            return None
        return state
    except (json.JSONDecodeError, KeyError, ValueError):
        return None
