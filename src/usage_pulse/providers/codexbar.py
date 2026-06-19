"""CodexBar provider: reads rate-window data via per-provider CLI calls.

Root-cause analysis of the TTY hang (issue #1329):
  `codexbar usage --json` (all providers) hangs without a TTY because the
  `codex` provider defaults to --source auto, which attempts browser OAuth and
  prompts interactively.

Fix: call each supported provider individually. Per-provider calls that use
web cookies or the CLI binary work without any TTY. The codex provider must
use --source cli to skip the web OAuth flow.

Confirmed background-safe providers (tested 2026-06-19):
  claude, gemini, cursor, opencodego  -- exit 0, no TTY needed
  codex --source cli                  -- exit 0, no TTY needed
  amp                                 -- exit 1 (no cookie), but non-blocking
"""

import json
import platform
import shutil
import subprocess

from .base import RateWindow, UsageData

# Providers to query and their display labels
_PROVIDERS: list[tuple[str, str, list[str]]] = [
    # (provider_name, display_label, extra_flags)
    ("claude", "CC", []),
    ("gemini", "GM", []),
    ("cursor", "CU", []),
    ("opencodego", "OC", []),
    ("codex", "CX", ["--source", "cli"]),  # --source cli avoids browser OAuth hang
]


class CodexbarProvider:
    """Fetch rate-window data from CodexBar CLI without TTY.

    Uses per-provider calls instead of `codexbar usage --json` (all-providers)
    to avoid the codex-provider TTY hang. Works on macOS; returns {} elsewhere.
    """

    def __init__(self, timeout: int = 12):
        self.timeout = timeout
        self._binary: str = shutil.which("codexbar") or "codexbar"

    @property
    def available(self) -> bool:
        return platform.system() == "Darwin" and shutil.which("codexbar") is not None

    def _fetch_one(self, provider: str, extra_flags: list[str]) -> dict | None:
        """Run codexbar for a single provider; return parsed dict or None."""
        cmd = [self._binary, "usage", "--provider", provider, "--json"] + extra_flags
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            raw = result.stdout.strip()
            if not raw:
                return None
            items = json.loads(raw)
            if not items:
                return None
            item = items[0]
            if "error" in item:
                return None
            return item
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return None

    def fetch_rate_windows(self) -> dict[str, dict]:
        """Return {provider: {label, primary_pct, secondary_pct, ...}} for each live provider."""
        if not self.available:
            return {}

        out = {}
        for provider, label, extra in _PROVIDERS:
            item = self._fetch_one(provider, extra)
            if item is None:
                continue
            usage = item.get("usage", {})
            if not usage:
                continue
            primary = usage.get("primary") or {}
            secondary = usage.get("secondary") or {}
            out[provider] = {
                "label": label,
                "primary_pct": float(primary.get("usedPercent", 0)),
                "secondary_pct": float(secondary.get("usedPercent", 0)),
                "primary_resets_at": primary.get("resetsAt"),
                "primary_reset_desc": primary.get("resetDescription"),
                "primary_window_minutes": int(primary.get("windowMinutes", 300)),
            }
        return out

    def format_tmux(self, windows: dict) -> str:
        """Format rate windows for tmux status-right."""
        parts = []
        for _provider, info in windows.items():
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
        """Merge CodexBar rate windows into a UsageData object."""
        claude = windows.get("claude", {})
        if claude:
            data.rate_windows["primary"] = RateWindow(
                window_minutes=claude.get("primary_window_minutes", 300),
                used_percent=claude.get("primary_pct", 0),
                resets_at=claude.get("primary_resets_at"),
                reset_description=claude.get("primary_reset_desc"),
            )
            data.rate_windows["secondary"] = RateWindow(
                window_minutes=10080,
                used_percent=claude.get("secondary_pct", 0),
            )
        return data
