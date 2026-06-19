"""Model selection advisor based on current usage and rate-window state."""
from dataclasses import dataclass
from ..providers.base import UsageData


@dataclass
class Recommendation:
    model: str
    reason: str
    urgency: str  # "ok" | "caution" | "warning" | "critical"


class ModelAdvisor:
    """Recommend a model based on rate-window usage and daily cost."""

    # Models ordered from heaviest to lightest
    TIERS = [
        ("claude-opus-4-8",   "heavy reasoning, highest cost"),
        ("claude-sonnet-4-6", "balanced — default for complex tasks"),
        ("claude-haiku-4-5",  "fast, cheap — routine/simple tasks"),
    ]

    def recommend(self, data: UsageData, cost_threshold: float = 50.0) -> Recommendation:
        rate_5min = data.primary_rate_pct
        rate_weekly = data.weekly_rate_pct
        cost_ratio = data.cost_usd / cost_threshold if cost_threshold > 0 else 0

        if rate_5min >= 90:
            return Recommendation(
                model="claude-haiku-4-5",
                reason=f"5分レートウィンドウ {rate_5min:.0f}% — haiku で低負荷維持",
                urgency="critical",
            )
        if rate_5min >= 80:
            return Recommendation(
                model="claude-haiku-4-5",
                reason=f"5分レートウィンドウ {rate_5min:.0f}% — sonnet は控えて haiku を推奨",
                urgency="warning",
            )
        if rate_5min >= 50:
            return Recommendation(
                model="claude-sonnet-4-6",
                reason=f"5分レートウィンドウ {rate_5min:.0f}% — haiku/sonnet で節約",
                urgency="caution",
            )
        if cost_ratio >= 0.9:
            return Recommendation(
                model="claude-haiku-4-5",
                reason=f"今日のコスト ${data.cost_usd:.2f} — 上限 ${cost_threshold:.0f} に近い",
                urgency="warning",
            )
        if cost_ratio >= 0.7:
            return Recommendation(
                model="claude-sonnet-4-6",
                reason=f"今日のコスト ${data.cost_usd:.2f} / ${cost_threshold:.0f} (70%超) — コスト意識を",
                urgency="caution",
            )
        if rate_weekly >= 80:
            return Recommendation(
                model="claude-sonnet-4-6",
                reason=f"週次ウィンドウ {rate_weekly:.0f}% — opus は控えて sonnet が安全",
                urgency="caution",
            )

        return Recommendation(
            model="claude-sonnet-4-6",
            reason=f"使用量良好 (5min: {rate_5min:.0f}%, cost: ${data.cost_usd:.2f})",
            urgency="ok",
        )

    def format_for_skill(self, rec: Recommendation, data: UsageData) -> str:
        """Return a markdown block suitable for inclusion in a Claude Code Skill."""
        emoji = {"ok": "✅", "caution": "⚠️", "warning": "🟠", "critical": "🔴"}[rec.urgency]
        lines = [
            f"## 現在の使用量",
            f"- 今日のコスト: ${data.cost_usd:.2f}",
            f"- 今日のトークン: {data.total_tokens // 1000}K",
            f"- 5分レートウィンドウ: {data.primary_rate_pct:.0f}%",
            f"- 週次ウィンドウ: {data.weekly_rate_pct:.0f}%",
            f"",
            f"## 推奨モデル",
            f"{emoji} **{rec.model}** — {rec.reason}",
        ]
        return "\n".join(lines)
