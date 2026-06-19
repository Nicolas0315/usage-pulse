"""tmux status-right display."""

import sys

from ..providers.base import UsageData
from ..providers.ccusage import CcusageProvider


class TmuxDisplay:
    """Output a compact tmux-colored status string."""

    def __init__(self, cost_threshold: float = 50.0):
        self.threshold = cost_threshold

    def render(self, data: UsageData | None) -> str:
        if data is None:
            return ""
        provider = CcusageProvider()
        return provider.format_tmux(data, self.threshold)

    def print(self, data: UsageData | None) -> None:
        print(self.render(data), end="")
        sys.stdout.flush()
