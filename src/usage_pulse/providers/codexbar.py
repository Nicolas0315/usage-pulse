"""CodexBar provider: reads rate-window data on macOS (TTY required)."""

import json
import shutil
import subprocess

from .base import RateWindow, UsageData


class CodexbarProvider:
    """Fetch rate-window usage from CodexBar CLI (macOS only, requires TTY).

    CodexBar exits with code 3 when any provider has an error (e.g. Codex has
    no rate-limit events yet), but still outputs valid JSON for other providers.
    We capture stdout regardless of exit code and fall back to None on empty output.

    NOTE: `codexbar usage --json` HANGS without a TTY (issue #1329).
    This provider should only be called in interactive/foreground contexts, or
    via `script -q /dev/null codexbar usage --json` to allocate a pseudo-TTY.
    """

    PROVIDER_LABELS = {
        "claude": "CC",
        "codex": "CX",
        "cursor": "CU",
        "gemini": "GM",
        "opencodego": "OC",
        "amp": "AP",
    }

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self._binary: str = shutil.which("codexbar") or "codexbar"

    @property
    def available(self) -> bool:
        return self._binary is not None

    def fetch_rate_windows(self) -> dict[str, dict]:
        """Return {provider: {primary_pct, secondary_pct, resets_at}} or {}."""
        if not self.available:
            return {}
        try:
            # Use script(1) to allocate a pseudo-TTY, avoiding the hang-without-TTY issue
            import platform

            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["script", "-q", "/dev/null", self._binary, "usage", "--json"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
            else:
                return {}
            raw = result.stdout.strip()
            if not raw:
                return {}
            data = json.loads(raw)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return {}

        out = {}
        for item in data:
            usage = item.get("usage")
            if not usage:
                continue
            provider = item.get("provider", "?")
            primary = usage.get("primary", {})
            secondary = usage.get("secondary", {})
            out[provider] = {
                "label": self.PROVIDER_LABELS.get(provider, provider[:2].upper()),
                "primary_pct": float(primary.get("usedPercent", 0)),
                "secondary_pct": float(secondary.get("usedPercent", 0)),
                "primary_resets_at": primary.get("resetsAt"),
                "primary_reset_desc": primary.get("resetDescription"),
            }
        return out

    def format_tmux(self, windows: dict) -> str:
        """Format rate windows for tmux status-right."""
        parts = []
        for provider, info in windows.items():
            pct = int(info["primary_pct"])
            label = info["label"]
            if pct >= 90:
                color = "#[fg=red,bold]"
            elif pct >= 80:
                color = "#[fg=yellow]"
            elif pct >= 50:
                color = "#[fg=cyan]"
            else:
                color = "#[fg=green]"
            parts.append(f"{color}{label}:{pct}%#[default]")
        return " ".join(parts)

    def enrich_usage_data(self, data: UsageData, windows: dict) -> UsageData:
        """Add rate window info from CodexBar to a UsageData object."""
        claude = windows.get("claude", {})
        if claude:
            data.rate_windows["primary"] = RateWindow(
                window_minutes=300,
                used_percent=claude.get("primary_pct", 0),
                resets_at=claude.get("primary_resets_at"),
                reset_description=claude.get("primary_reset_desc"),
            )
            data.rate_windows["secondary"] = RateWindow(
                window_minutes=10080,
                used_percent=claude.get("secondary_pct", 0),
            )
        return data
