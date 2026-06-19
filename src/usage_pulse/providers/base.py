"""Shared data models for usage providers."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ModelBreakdown:
    model_name: str
    cost_usd: float
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost_per_1k_output(self) -> float:
        if self.output_tokens == 0:
            return 0.0
        return (self.cost_usd / self.output_tokens) * 1000

    @property
    def cache_efficiency(self) -> float:
        """Ratio of cache reads to total input — higher is better."""
        total = self.input_tokens + self.cache_read_tokens
        if total == 0:
            return 0.0
        return self.cache_read_tokens / total


@dataclass
class RateWindow:
    window_minutes: int
    used_percent: float
    resets_at: str | None = None
    reset_description: str | None = None


@dataclass
class UsageData:
    date: str
    cost_usd: float
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    model_breakdowns: list[ModelBreakdown] = field(default_factory=list)
    rate_windows: dict[str, RateWindow] = field(default_factory=dict)
    source: str = "unknown"
    fetched_at: datetime | None = None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def top_models(self) -> list[ModelBreakdown]:
        return sorted(self.model_breakdowns, key=lambda m: m.cost_usd, reverse=True)

    @property
    def primary_rate_pct(self) -> float:
        """Short-window (5min) rate usage percent, 0 if unavailable."""
        w = self.rate_windows.get("primary")
        return w.used_percent if w else 0.0

    @property
    def weekly_rate_pct(self) -> float:
        w = self.rate_windows.get("secondary")
        return w.used_percent if w else 0.0
