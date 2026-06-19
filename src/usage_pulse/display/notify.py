"""Cross-platform OS desktop notifications."""

import os
import platform
import subprocess


def _os_type() -> str:
    s = platform.system()
    if s == "Darwin":
        return "mac"
    if s == "Linux":
        try:
            with open("/proc/version") as f:
                if "microsoft" in f.read().lower():
                    return "wsl"
        except OSError:
            pass
        return "linux"
    if s == "Windows":
        return "windows"
    return "other"


class Notifier:
    """Send desktop notifications without external dependencies."""

    def __init__(self):
        self._os = _os_type()
        self._state_dir = os.path.join(
            os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state")),
            "usage-pulse",
            "notify-flags",
        )
        os.makedirs(self._state_dir, exist_ok=True)

    @staticmethod
    def _esc_applescript(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    @staticmethod
    def _esc_ps_single(s: str) -> str:
        return s.replace("'", "''")

    def send(self, title: str, message: str) -> None:
        try:
            match self._os:
                case "mac":
                    t = self._esc_applescript(title)
                    m = self._esc_applescript(message)
                    subprocess.run(
                        [
                            "osascript",
                            "-e",
                            f'display notification "{m}" with title "{t}"',
                        ],
                        capture_output=True,
                        timeout=5,
                    )
                case "linux":
                    subprocess.run(
                        ["notify-send", title, message],
                        capture_output=True,
                        timeout=5,
                    )
                case "wsl":
                    t = self._esc_ps_single(title)
                    m = self._esc_ps_single(message)
                    ps_cmd = (
                        "[Windows.UI.Notifications.ToastNotificationManager, "
                        "Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null; "
                        "$xml = [Windows.UI.Notifications.ToastNotificationManager]::"
                        "GetTemplateContent('ToastText02'); "
                        f"$xml.GetElementsByTagName('text')[0].InnerText = '{t}'; "
                        f"$xml.GetElementsByTagName('text')[1].InnerText = '{m}'; "
                        "[Windows.UI.Notifications.ToastNotificationManager]::"
                        "CreateToastNotifier('usage-pulse').Show("
                        "[Windows.UI.Notifications.ToastNotification]::new($xml))"
                    )
                    subprocess.run(
                        ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
                        capture_output=True,
                        timeout=10,
                    )
                case "windows":
                    t = self._esc_ps_single(title)
                    m = self._esc_ps_single(message)
                    ps_cmd = (
                        "Add-Type -AssemblyName System.Windows.Forms; "
                        "$n = New-Object System.Windows.Forms.NotifyIcon; "
                        "$n.Icon = [System.Drawing.SystemIcons]::Information; "
                        "$n.Visible = $true; "
                        f"$n.ShowBalloonTip(5000, '{t}', '{m}', "
                        "[System.Windows.Forms.ToolTipIcon]::Info)"
                    )
                    subprocess.run(
                        ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
                        capture_output=True,
                        timeout=10,
                    )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

    def send_once(self, key: str, title: str, message: str) -> bool:
        """Send notification only once per key; returns True if sent."""
        flag = os.path.join(self._state_dir, f"{key}.flag")
        if os.path.exists(flag):
            return False
        open(flag, "w").close()
        self.send(title, message)
        return True

    def reset(self, key: str) -> None:
        """Clear send-once flag so next threshold crossing triggers again."""
        flag = os.path.join(self._state_dir, f"{key}.flag")
        try:
            os.remove(flag)
        except OSError:
            pass
