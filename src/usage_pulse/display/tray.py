"""Cross-platform system tray using pystray (Win/Linux) or rumps (Mac)."""

import platform
import threading
import time

from ..analysis.advisor import ModelAdvisor
from ..analysis.roi import compute_roi, format_roi_table
from ..handshake import write_state
from ..providers.ccusage import CcusageProvider
from ..providers.codexbar import CodexbarProvider
from .notify import Notifier


def _create_icon_image(color: str = "green"):
    """Create a minimal colored dot image for the tray icon."""
    from PIL import Image, ImageDraw

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    colors = {
        "green": (80, 200, 80, 255),
        "yellow": (240, 200, 60, 255),
        "red": (220, 60, 60, 255),
        "gray": (160, 160, 160, 255),
    }
    c = colors.get(color, colors["gray"])
    draw.ellipse([4, 4, size - 4, size - 4], fill=c)
    return img


class TrayApp:
    """pystray-based cross-platform system tray (Windows / Linux)."""

    def __init__(self, cost_threshold: float = 50.0, poll_interval: int = 60):
        self.threshold = cost_threshold
        self.poll_interval = poll_interval
        self._ccusage = CcusageProvider()
        self._codexbar = CodexbarProvider()
        self._advisor = ModelAdvisor()
        self._notifier = Notifier()
        self._data = None
        self._icon = None

    def _fetch_and_update(self):
        data = self._ccusage.fetch_today()
        if data is None:
            return
        self._data = data
        rec = self._advisor.recommend(data, self.threshold)
        write_state(data, rec)

        # Notification check
        if data.cost_usd >= self.threshold:
            self._notifier.send_once(
                "cost-threshold",
                "Usage Alert",
                f"Today: ${data.cost_usd:.2f} (threshold ${self.threshold:.0f})",
            )
        else:
            self._notifier.reset("cost-threshold")

        # Update icon color
        cost_ratio = data.cost_usd / self.threshold if self.threshold > 0 else 0
        if data.primary_rate_pct >= 80 or cost_ratio >= 0.9:
            color = "red"
        elif data.primary_rate_pct >= 50 or cost_ratio >= 0.7:
            color = "yellow"
        else:
            color = "green"

        if self._icon:
            self._icon.icon = _create_icon_image(color)
            self._update_title()

    def _update_title(self):
        if self._data and self._icon:
            cost = self._data.cost_usd
            tokens_k = self._data.total_tokens // 1000
            self._icon.title = f"usage-pulse: ${cost:.2f} / {tokens_k}K today"

    def _poll_loop(self):
        while True:
            try:
                self._fetch_and_update()
            except Exception:
                pass
            time.sleep(self.poll_interval)

    def _make_menu(self):
        import pystray

        def show_summary(icon, item):
            if self._data:
                rec = self._advisor.recommend(self._data, self.threshold)
                msg = (
                    f"Today: ${self._data.cost_usd:.2f} / {self._data.total_tokens // 1000}K tokens\n"
                    f"Recommended: {rec.model}\n{rec.reason}"
                )
                self._notifier.send("usage-pulse Summary", msg)

        def show_roi(icon, item):
            if self._data:
                rois = compute_roi(self._data.model_breakdowns)
                print(format_roi_table(rois))

        def quit_app(icon, item):
            icon.stop()

        return pystray.Menu(
            pystray.MenuItem("Show Summary", show_summary),
            pystray.MenuItem("Show ROI", show_roi),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", quit_app),
        )

    def run(self):
        """Start the system tray daemon (blocking)."""
        import pystray

        # Initial fetch in background
        threading.Thread(target=self._fetch_and_update, daemon=True).start()
        # Start polling thread
        threading.Thread(target=self._poll_loop, daemon=True).start()

        self._icon = pystray.Icon(
            name="usage-pulse",
            icon=_create_icon_image("gray"),
            title="usage-pulse: loading...",
            menu=self._make_menu(),
        )
        self._icon.run()


def run_tray(cost_threshold: float = 50.0, poll_interval: int = 60):
    """Entry point for the system tray daemon."""
    os_name = platform.system()
    if os_name == "Darwin":
        # On Mac, codexbar already provides the menu bar.
        # We run pystray as a complementary tray (or skip and just show a message).
        print("Mac: codexbar already provides the menu bar.")
        print("Running usage-pulse tray as a supplement...")

    app = TrayApp(cost_threshold=cost_threshold, poll_interval=poll_interval)
    app.run()
