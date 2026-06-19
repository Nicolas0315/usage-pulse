#!/usr/bin/env bash
# Check for updates to ccusage and codexbar
set -eu

echo "=== usage-pulse provider update check ==="
echo ""

# ccusage
echo "[ccusage]"
current=$(bunx ccusage --version 2>/dev/null | head -1 || echo "unknown")
echo "  installed: $current"
latest=$(bunx npm view ccusage version 2>/dev/null || echo "check failed")
echo "  latest:    $latest"

echo ""

# codexbar
echo "[codexbar]"
if command -v codexbar &>/dev/null; then
  current=$(codexbar --version 2>/dev/null | head -1 || echo "unknown")
  echo "  installed: $current"
  brew_latest=$(brew info --json codexbar 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d[0]['versions']['stable'])" 2>/dev/null || echo "check failed")
  echo "  homebrew:  $brew_latest"
else
  echo "  not installed (macOS only)"
fi

echo ""

# VERSION_PINS
pins_file="$(dirname "$0")/../providers/VERSION_PINS.json"
if [ -f "$pins_file" ]; then
  echo "[pinned versions]"
  cat "$pins_file"
else
  echo "[no VERSION_PINS.json found]"
fi

echo ""
echo "To update ccusage:   bun add -g ccusage@latest"
echo "To update codexbar:  brew upgrade --cask codexbar"
