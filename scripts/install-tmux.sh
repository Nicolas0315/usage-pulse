#!/usr/bin/env bash
# Install usage-pulse as tmux status-right
set -eu

TMUX_CONF="${TMUX_CONF:-$HOME/.tmux.conf}"
USAGE_PULSE="$(command -v usage-pulse 2>/dev/null || echo 'usage-pulse')"
RETENTION_COUNT="${USAGE_PULSE_BACKUP_KEEP:-5}"

backup_tmux_conf() {
  if [ -f "$TMUX_CONF" ]; then
    ts="$(date +%Y%m%d%H%M%S)"
    backup="${TMUX_CONF}.usage-pulse.bak.${ts}"
    cp "$TMUX_CONF" "$backup"
    echo "Backup: $backup (retention: newest $RETENTION_COUNT)"
    ls -1t "${TMUX_CONF}".usage-pulse.bak.* 2>/dev/null | awk "NR>$RETENTION_COUNT" | while read -r stale; do
      rm -f "$stale"
    done
  fi
}

if ! grep -q 'usage-pulse' "$TMUX_CONF" 2>/dev/null; then
  backup_tmux_conf
  # Add to existing status-right or append new block
  if grep -q 'status-right' "$TMUX_CONF" 2>/dev/null; then
    python3 - "$TMUX_CONF" "$USAGE_PULSE" << 'PYEOF'
from pathlib import Path
import sys

path = Path(sys.argv[1])
usage_pulse = sys.argv[2]
needle = 'set -g status-right "'
replacement = f'set -g status-right "#({usage_pulse} statusline) | '
text = path.read_text()
path.write_text(text.replace(needle, replacement, 1))
PYEOF
    echo "Updated $TMUX_CONF"
  else
    cat >> "$TMUX_CONF" << EOF

# --- usage-pulse ---
set -g status-interval 30
set -g status-right "#($USAGE_PULSE statusline) | %H:%M"
set -g status-right-length 80
EOF
    echo "Appended to $TMUX_CONF"
  fi
else
  echo "usage-pulse already in $TMUX_CONF"
fi

tmux source-file "$TMUX_CONF" 2>/dev/null && echo "tmux reloaded" || echo "Run: tmux source-file $TMUX_CONF"
