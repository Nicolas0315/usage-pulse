"""Tests for ROI calculation."""
import pytest
from src.usage_pulse.providers.base import ModelBreakdown
from src.usage_pulse.analysis.roi import compute_roi, format_roi_table


def test_compute_roi_basic():
    breakdowns = [
        ModelBreakdown(
            model_name="claude-sonnet-4-6",
            cost_usd=5.0,
            input_tokens=100_000,
            output_tokens=20_000,
            cache_read_tokens=500_000,
        ),
        ModelBreakdown(
            model_name="claude-haiku-4-5",
            cost_usd=0.5,
            input_tokens=200_000,
            output_tokens=50_000,
        ),
    ]
    rois = compute_roi(breakdowns)
    assert len(rois) == 2
    # Sorted by cost descending
    assert rois[0].model_name == "claude-sonnet-4-6"
    assert rois[0].cost_usd == 5.0


def test_cost_per_1k_output():
    m = ModelBreakdown(
        model_name="test",
        cost_usd=1.0,
        input_tokens=0,
        output_tokens=10_000,
    )
    rois = compute_roi([m])
    # $1.0 / 10K output = $0.1 per 1K
    assert abs(rois[0].cost_per_1k_output - 0.1) < 0.001


def test_cache_efficiency():
    m = ModelBreakdown(
        model_name="test",
        cost_usd=0.5,
        input_tokens=10_000,
        output_tokens=5_000,
        cache_read_tokens=90_000,
    )
    rois = compute_roi([m])
    # cache_read / (input + cache_read) = 90K / 100K = 0.9
    assert abs(rois[0].cache_efficiency - 0.9) < 0.01


def test_format_roi_table_empty():
    result = format_roi_table([])
    assert "No model data" in result


def test_format_roi_table_with_data():
    m = ModelBreakdown(
        model_name="claude-sonnet-4-6",
        cost_usd=3.5,
        input_tokens=50_000,
        output_tokens=15_000,
    )
    rois = compute_roi([m])
    table = format_roi_table(rois)
    assert "claude-sonnet-4-6" in table
    assert "3.500" in table
