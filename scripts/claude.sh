#!/usr/bin/env sh
# Lightweight launcher for Claude Code without a global install or sudo.
# Usage:
#   sh scripts/claude.sh           # default mode
#   sh scripts/claude.sh chat      # chat mode
#   sh scripts/claude.sh code      # code mode

set -e

MODE="$1"

if [ -z "$MODE" ]; then
  npx -y @anthropic-ai/claude-code
else
  npx -y @anthropic-ai/claude-code "$MODE"
fi
