#!/usr/bin/env bash
# Install model-advisor skill to Claude Code and Codex skill directories
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$SCRIPT_DIR/../skills/model-advisor"

for skills_dir in \
  "$HOME/.agent/skills" \
  "$HOME/.claude/skills" \
  "$HOME/.codex/skills"
do
  if [ -d "$(dirname "$skills_dir")" ]; then
    mkdir -p "$skills_dir/model-advisor"
    cp "$SKILL_SRC/SKILL.md" "$skills_dir/model-advisor/SKILL.md"
    echo "Installed: $skills_dir/model-advisor/SKILL.md"
  fi
done

echo "Done. Use /model-advisor in Claude Code or Codex to check usage."
