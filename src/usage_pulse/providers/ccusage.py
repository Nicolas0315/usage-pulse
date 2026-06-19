"""ccusage provider: fetches AI usage via `ccusage daily --json`."""
import json
import subprocess
import shutil
from datetime import datetime, timezone
from .base import UsageData, ModelBreakdown


# Short display names for known models
MODEL_SHORT = {
    "claude-opus-4-8": "Op4.8",
    "claude-sonnet-4-6": "So4.6",
    "claude-haiku-4-5": "Ha4.5",
    "claude-fable-5": "Fb5",
    "gpt-5.5": "GP5.5",
    "gpt-4o": "GP4o",
    "gpt-4o-mini": "4oMini",
    "o3": "O3",
    "o4-mini": "O4m",
    "codex-auto-review": "CXRev",
    "gemini-2.5-pro": "Gm2.5",
    "gemini-2.0-flash": "Gm2F",
}


def _model_short(name: str) -> str:
    return MODEL_SHORT.get(name, name[:6])


class CcusageProvider:
    """Fetch usage data via ccusage CLI (cross-platform, background-safe)."""

    def __init__(self, bunx_path: str | None = None, timeout: int = 30):
        self.bunx = bunx_path or shutil.which("bunx") or "bunx"
        self.timeout = timeout

    def fetch_today(self) -> UsageData | None:
        try:
            result = subprocess.run(
                [self.bunx, "ccusage", "daily", "--json"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            raw = result.stdout.strip()
            if not raw:
                return None
            data = json.loads(raw)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return None

        daily = data.get("daily", [])
        if not daily:
            return None

        today = daily[0]
        breakdowns = [
            ModelBreakdown(
                model_name=m.get("modelName", "unknown"),
                cost_usd=float(m.get("cost", 0)),
                input_tokens=int(m.get("inputTokens", 0)),
                output_tokens=int(m.get("outputTokens", 0)),
                cache_read_tokens=int(m.get("cacheReadTokens", 0)),
                cache_creation_tokens=int(m.get("cacheCreationTokens", 0)),
            )
            for m in today.get("modelBreakdowns", [])
        ]

        return UsageData(
            date=today.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            cost_usd=float(today.get("cost", 0)),
            input_tokens=int(today.get("inputTokens", 0)),
            output_tokens=int(today.get("outputTokens", 0)),
            cache_read_tokens=int(today.get("cacheReadTokens", 0)),
            cache_creation_tokens=int(today.get("cacheCreationTokens", 0)),
            model_breakdowns=breakdowns,
            source="ccusage",
            fetched_at=datetime.now(timezone.utc),
        )

    def format_tmux(self, data: UsageData, cost_threshold: float = 50.0) -> str:
        """Return tmux-colored status string."""
        cost = data.cost_usd
        tokens_k = data.total_tokens // 1000

        if cost >= cost_threshold:
            color = "#[fg=red,bold]"
        elif cost >= cost_threshold * 0.7:
            color = "#[fg=yellow]"
        elif cost >= cost_threshold * 0.3:
            color = "#[fg=cyan]"
        else:
            color = "#[fg=green]"

        top = [_model_short(m.model_name) for m in data.top_models[:2] if m.cost_usd > 0]
        model_str = "+".join(top)

        parts = [f"{color}${cost:.2f}#[default]"]
        if tokens_k > 0:
            parts.append(f"{tokens_k}K")
        if model_str:
            parts.append(f"[{model_str}]")
        return " ".join(parts)
