"""Background worker: fetch usage data and write statusline cache.

Spawned by `usage-pulse statusline` as a detached process so tmux never blocks.
"""

import sys
import time
from pathlib import Path


def main():
    if len(sys.argv) != 4:
        sys.exit(1)
    cache_file = Path(sys.argv[1])
    cache_time_file = Path(sys.argv[2])
    threshold = float(sys.argv[3])

    try:
        from usage_pulse.analysis.advisor import ModelAdvisor
        from usage_pulse.display.notify import Notifier
        from usage_pulse.handshake import write_state
        from usage_pulse.io import write_text_atomic
        from usage_pulse.providers.ccusage import CcusageProvider

        provider = CcusageProvider()
        data = provider.fetch_today()

        if data is not None:
            text = provider.format_tmux(data, threshold)

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
        else:
            text = ""

        write_text_atomic(cache_file, text)
        write_text_atomic(cache_time_file, str(int(time.time())))
    except Exception:
        pass


if __name__ == "__main__":
    main()
