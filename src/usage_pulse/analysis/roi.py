"""Token ROI calculation per model."""

from dataclasses import dataclass

from ..providers.base import ModelBreakdown

# Known list prices (USD per 1M tokens) as of 2026-06
# Update via: scripts/check-provider-updates.sh
MODEL_PRICES = {
    # Claude — https://www.anthropic.com/pricing (checked 2026-06-19)
    "claude-opus-4-8": {"input": 15.0, "output": 75.0, "cache_read": 1.5},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    "claude-haiku-4-5": {"input": 0.8, "output": 4.0, "cache_read": 0.08},
    "claude-fable-5": {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    "claude-3.5-sonnet": {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    # OpenAI — https://openai.com/api/pricing/ (checked 2026-06-19)
    "gpt-5.5": {"input": 2.0, "output": 8.0, "cache_read": 1.0},
    "gpt-4o": {"input": 2.5, "output": 10.0, "cache_read": 1.25},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6, "cache_read": 0.075},
    "gpt-4.1": {"input": 2.0, "output": 8.0, "cache_read": 0.5},
    "o3": {"input": 10.0, "output": 40.0, "cache_read": 2.5},
    "o4-mini": {"input": 1.1, "output": 4.4, "cache_read": 0.275},
    # Gemini — https://ai.google.dev/pricing (checked 2026-06-19)
    "gemini-2.5-pro": {"input": 1.25, "output": 10.0, "cache_read": 0.31},
    "gemini-2.5-flash": {"input": 0.075, "output": 0.3, "cache_read": 0.019},
    "gemini-2.0-flash": {"input": 0.075, "output": 0.3, "cache_read": 0.019},
    # Qwen — https://www.alibabacloud.com/en/product/modelstudio/pricing (checked 2026-06-19)
    "qwen-plus": {"input": 0.4, "output": 1.2, "cache_read": 0.07},
    "qwen-max": {"input": 1.6, "output": 6.4, "cache_read": 0.2},
    # Kimi — https://platform.moonshot.cn/pricing (checked 2026-06-19)
    "kimi-k2": {"input": 0.6, "output": 2.5, "cache_read": 0.15},
}


@dataclass
class ModelROI:
    model_name: str
    cost_usd: float
    output_tokens: int
    cache_efficiency: float  # cache_read / (input + cache_read)
    cost_per_1k_output: float  # USD per 1K output tokens
    effective_cost_ratio: float  # actual_cost / theoretical_max_cost (lower = better)
    sessions: int = 0


def compute_roi(breakdowns: list[ModelBreakdown]) -> list[ModelROI]:
    """Compute ROI metrics for each model in the breakdown."""
    results = []
    for m in breakdowns:
        if m.total_tokens == 0:
            continue

        prices = MODEL_PRICES.get(m.model_name)

        # Effective cost ratio: actual cost vs cost if no caching
        if prices and m.input_tokens > 0:
            theoretical = (m.input_tokens + m.cache_read_tokens) / 1_000_000 * prices[
                "input"
            ] + m.output_tokens / 1_000_000 * prices["output"]
            ratio = m.cost_usd / theoretical if theoretical > 0 else 1.0
        else:
            ratio = 1.0

        results.append(
            ModelROI(
                model_name=m.model_name,
                cost_usd=m.cost_usd,
                output_tokens=m.output_tokens,
                cache_efficiency=m.cache_efficiency,
                cost_per_1k_output=m.cost_per_1k_output,
                effective_cost_ratio=ratio,
            )
        )

    return sorted(results, key=lambda r: r.cost_usd, reverse=True)


def format_roi_table(rois: list[ModelROI]) -> str:
    """Return a human-readable ROI table."""
    if not rois:
        return "No model data available."

    lines = [
        f"{'Model':<22} {'Cost':>8} {'OutTok':>8} {'$/1K out':>9} {'Cache%':>7} {'EffRatio':>9}",
        "-" * 70,
    ]
    for r in rois:
        cache_pct = f"{r.cache_efficiency * 100:.0f}%"
        eff = f"{r.effective_cost_ratio:.2f}"
        lines.append(
            f"{r.model_name:<22} ${r.cost_usd:>7.3f} {r.output_tokens:>8,} "
            f"${r.cost_per_1k_output:>8.4f} {cache_pct:>7} {eff:>9}"
        )
    return "\n".join(lines)
