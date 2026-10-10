#!/usr/bin/env bash
# Simuliert pre-push-Scan auf einem Commit (Default: HEAD im aktuellen Repo).
set -u

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="${1:-$(git rev-parse --show-toplevel 2>/dev/null || true)}"
SHA="${2:-HEAD}"

if [ -z "$REPO" ] || ! git -C "$REPO" rev-parse "$SHA" >/dev/null 2>&1; then
  echo "Usage: $0 [repo-path] [commit-ish]" >&2
  exit 2
fi

SHA="$(git -C "$REPO" rev-parse "$SHA")"
cd "$REPO" || exit 2
export HOOK_DIR
# shellcheck source=scan-lib.sh
. "${HOOK_DIR}/scan-lib.sh"

RED='\033[0;31m'
NC='\033[0m'
shopt -s nocasematch
load_scan_patterns

echo "repo=$REPO sha=$SHA" >&2
set +e
scan_commit_tree "$SHA"
rc=$?
set -e
if [ "$rc" -eq 0 ]; then
  echo "TOTAL_BLOCKED=0 (OK)"
else
  echo "TOTAL_BLOCKED>0 (siehe BLOCKIERT-Zeilen oben)"
fi
exit "$rc"
