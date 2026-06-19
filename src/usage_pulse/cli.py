"""usage-pulse CLI entry point."""

import os
import sys

import click

from .analysis.advisor import ModelAdvisor
from .analysis.roi import compute_roi, format_roi_table
from .display.notify import Notifier
from .handshake import STATE_FILE, write_state
from .providers.ccusage import CcusageProvider
from .providers.codexbar import CodexbarProvider


@click.group()
@click.version_option()
def main():
    """usage-pulse — AI tool usage monitor (Mac/Win/Linux)."""
    pass


@main.command()
@click.option(
    "--threshold",
    default=50.0,
    envvar="USAGE_PULSE_THRESHOLD",
    help="Daily cost threshold for color/alert (USD, default 50)",
)
@click.option("--no-cache", is_flag=True, help="Skip cache, fetch fresh data")
def statusline(threshold, no_cache):
    """Output tmux status-right string (cached, non-blocking)."""
    import time
    from pathlib import Path

    cache_dir = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "usage-pulse"
    cache_file = cache_dir / "statusline"
    cache_time_file = cache_dir / "statusline.time"
    ttl = int(os.environ.get("USAGE_PULSE_CACHE_TTL", "60"))

    cache_dir.mkdir(parents=True, exist_ok=True)

    now = int(time.time())
    cached_time = 0
    if cache_time_file.exists():
        try:
            cached_time = int(cache_time_file.read_text().strip())
        except ValueError:
            pass

    if no_cache or (now - cached_time) >= ttl:
        # Refresh in background
        import subprocess

        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "usage_pulse._refresh_worker",
                str(cache_file),
                str(cache_time_file),
                str(threshold),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    # Return cached result immediately
    if cache_file.exists():
        print(cache_file.read_text().rstrip(), end="")
    sys.stdout.flush()


@main.command()
@click.option("--threshold", default=50.0, envvar="USAGE_PULSE_THRESHOLD")
def sync(threshold):
    """Update agent handshake state file with current usage."""
    provider = CcusageProvider()
    data = provider.fetch_today()
    if data is None:
        click.echo("Error: could not fetch usage data", err=True)
        sys.exit(1)

    advisor = ModelAdvisor()
    rec = advisor.recommend(data, threshold)
    write_state(data, rec)

    notifier = Notifier()
    if data.cost_usd >= threshold:
        notifier.send_once(
            "cost-threshold",
            "Usage Alert",
            f"Today: ${data.cost_usd:.2f} (threshold ${threshold:.0f})",
        )
    else:
        notifier.reset("cost-threshold")

    click.echo(f"Synced: ${data.cost_usd:.2f} / {data.total_tokens // 1000}K tokens")
    click.echo(f"Recommend: {rec.model} — {rec.reason}")
    click.echo(f"State: {STATE_FILE}")


@main.command()
@click.option("--threshold", default=50.0, envvar="USAGE_PULSE_THRESHOLD")
def summary(threshold):
    """Print today's usage summary."""
    ccusage = CcusageProvider()
    data = ccusage.fetch_today()
    if data is None:
        click.echo("Error: could not fetch usage data", err=True)
        sys.exit(1)

    # Enrich with real-time rate windows from CodexBar (TTY-free per-provider calls)
    cb = CodexbarProvider()
    if cb.available:
        windows = cb.fetch_rate_windows()
        data = cb.enrich_usage_data(data, windows)
    else:
        windows = {}

    advisor = ModelAdvisor()
    rec = advisor.recommend(data, threshold)

    click.echo(f"\n{'=' * 50}")
    click.echo(f"  usage-pulse  —  {data.date}")
    click.echo(f"{'=' * 50}")
    click.echo(f"  Cost today:   ${data.cost_usd:.4f}")
    click.echo(f"  Tokens:       {data.total_tokens:,} ({data.total_tokens // 1000}K)")
    click.echo(f"  Input:        {data.input_tokens:,}")
    click.echo(f"  Output:       {data.output_tokens:,}")
    click.echo(f"  Cache read:   {data.cache_read_tokens:,}")
    click.echo(f"  5min rate:    {data.primary_rate_pct:.1f}%")
    click.echo(f"  Weekly rate:  {data.weekly_rate_pct:.1f}%")

    if windows:
        click.echo()
        click.echo("  Rate windows (CodexBar):")
        for prov, info in windows.items():
            click.echo(
                f"    {info['label']} {prov}: "
                f"primary={info['primary_pct']:.1f}% "
                f"secondary={info['secondary_pct']:.1f}%"
                + (f"  [{info['primary_reset_desc']}]" if info.get("primary_reset_desc") else "")
            )

    urgency_emoji = {"ok": "✅", "caution": "⚠️", "warning": "🟠", "critical": "🔴"}
    click.echo(f"\n  Recommended:  {urgency_emoji.get(rec.urgency, '')} {rec.model}")
    click.echo(f"  Reason:       {rec.reason}")
    click.echo(f"{'=' * 50}\n")


@main.command()
def roi():
    """Show token ROI table by model."""
    provider = CcusageProvider()
    data = provider.fetch_today()
    if data is None:
        click.echo("Error: could not fetch usage data", err=True)
        sys.exit(1)

    rois = compute_roi(data.model_breakdowns)
    click.echo(f"\nToken ROI — {data.date}\n")
    click.echo(format_roi_table(rois))
    click.echo()


@main.command()
@click.option("--cost-threshold", default=50.0, envvar="USAGE_PULSE_THRESHOLD")
@click.option(
    "--poll-interval",
    default=60,
    envvar="USAGE_PULSE_POLL_INTERVAL",
    help="Seconds between updates (default 60)",
)
def tray(cost_threshold, poll_interval):
    """Start cross-platform system tray daemon (Mac/Win/Linux)."""
    from .display.tray import run_tray

    run_tray(cost_threshold=cost_threshold, poll_interval=poll_interval)


@main.command()
def setup():
    """Interactive setup: install tmux hook and Claude Code integration."""
    import subprocess
    from pathlib import Path

    click.echo("\n=== usage-pulse setup ===\n")

    # Check dependencies
    import shutil

    checks = {
        "tmux": shutil.which("tmux"),
        "bunx (ccusage)": shutil.which("bunx"),
        "python3": shutil.which("python3"),
        "codexbar (Mac only)": shutil.which("codexbar"),
    }
    for name, path in checks.items():
        status = "✅" if path else "❌"
        click.echo(f"  {status} {name}: {path or 'not found'}")

    click.echo()
    if click.confirm("Install tmux statusline integration?", default=True):
        script_dir = Path(__file__).parent.parent.parent.parent / "scripts"
        install_script = script_dir / "install-tmux.sh"
        if install_script.exists():
            subprocess.run(["bash", str(install_script)])
        else:
            click.echo("  Run scripts/install-tmux.sh manually")

    if click.confirm("Install Claude Code hook (PostToolUse sync)?", default=True):
        script_dir = Path(__file__).parent.parent.parent.parent / "scripts"
        hook_script = script_dir / "install-claude-hook.sh"
        if hook_script.exists():
            subprocess.run(["bash", str(hook_script)])
        else:
            click.echo("  Run scripts/install-claude-hook.sh manually")

    click.echo("\nSetup complete. Run `usage-pulse summary` to verify.")
