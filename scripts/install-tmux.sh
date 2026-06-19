#!/usr/bin/env bash
# Install usage-pulse as tmux status-right
set -eu

TMUX_CONF="${TMUX_CONF:-$HOME/.tmux.conf}"
USAGE_PULSE="$(command -v usage-pulse 2>/dev/null || echo 'usage-pulse')"

if ! grep -q 'usage-pulse' "$TMUX_CONF" 2>/dev/null; then
  # Add to existing status-right or append new block
  if grep -q 'status-right' "$TMUX_CONF" 2>/dev/null; then
    # Prepend usage-pulse to existing status-right
    sed -i.bak 's|set -g status-right "|set -g status-right "#(usage-pulse statusline) \| |g' "$TMUX_CONF"
    echo "Updated $TMUX_CONF (backup: $TMUX_CONF.bak)"
  else
    cat >> "$TMUX_CONF" << 'EOF'

# --- usage-pulse ---
set -g status-interval 30
set -g status-right "#(usage-pulse statusline) | %H:%M"
set -g status-right-length 80
EOF
    echo "Appended to $TMUX_CONF"
  fi
else
  echo "usage-pulse already in $TMUX_CONF"
fi

tmux source-file "$TMUX_CONF" 2>/dev/null && echo "tmux reloaded" || echo "Run: tmux source-file $TMUX_CONF"
