#!/usr/bin/env bash
# Install usage-pulse as a Claude Code PostToolUse hook for agent handshake
set -eu

SETTINGS="$HOME/.claude/settings.json"
USAGE_PULSE="$(command -v usage-pulse 2>/dev/null || echo 'usage-pulse')"
RETENTION_COUNT="${USAGE_PULSE_BACKUP_KEEP:-5}"

if [ ! -f "$SETTINGS" ]; then
  echo "Claude Code settings not found at $SETTINGS"
  echo "Run: usage-pulse sync  (manually after each session)"
  exit 0
fi

python3 - "$SETTINGS" "$USAGE_PULSE" "$RETENTION_COUNT" << 'PYEOF'
import glob
import json
import os
import shutil
import sys
from datetime import datetime

settings_path = sys.argv[1]
usage_pulse = sys.argv[2]
retention_count = int(sys.argv[3])

with open(settings_path) as f:
    settings = json.load(f)

hooks = settings.setdefault("hooks", {})
post_tool_use = hooks.setdefault("PostToolUse", [])

hook_cmd = f"{usage_pulse} sync --quiet 2>/dev/null &"

# Check if already installed
for entry in post_tool_use:
    if isinstance(entry, dict) and "usage-pulse" in json.dumps(entry):
        print("usage-pulse hook already installed in Claude Code settings")
        sys.exit(0)

post_tool_use.append({
    "matcher": "",
    "hooks": [{"type": "command", "command": hook_cmd}]
})

backup = settings_path + ".usage-pulse.bak." + datetime.utcnow().strftime("%Y%m%d%H%M%S")
shutil.copy2(settings_path, backup)
for stale in sorted(glob.glob(settings_path + ".usage-pulse.bak.*"), reverse=True)[retention_count:]:
    try:
        os.remove(stale)
    except OSError:
        pass

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Installed hook in {settings_path} (backup: {backup}; retention: newest {retention_count})")
PYEOF
