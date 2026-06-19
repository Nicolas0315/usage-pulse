"""Tests for filesystem helper behavior."""

from concurrent.futures import ThreadPoolExecutor

from usage_pulse.io import write_text_atomic


def test_write_text_atomic_concurrent_writers_do_not_share_temp_path(tmp_path):
    target = tmp_path / "current.json"
    values = [f"value-{i}" for i in range(20)]

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda value: write_text_atomic(target, value), values))

    assert target.read_text(encoding="utf-8") in values
    assert list(tmp_path.glob(".current.json.*.tmp")) == []
