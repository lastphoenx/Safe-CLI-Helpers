# Lokaler Cache für Denylist/Allowlist (schneller als OneDrive bei jedem Commit).
# Windows: %LOCALAPPDATA%\safe-cli-git-hooks
# Linux/macOS: ~/.cache/safe-cli-git-hooks

_resolve_denylist_source() {
  if [ -f "${HOOK_DIR}/denylist.txt" ]; then
    echo "${HOOK_DIR}/denylist.txt"
  elif [ -f "${HOOK_DIR}/denylist.local.txt" ]; then
    echo "${HOOK_DIR}/denylist.local.txt"
  else
    echo "${HOOK_DIR}/denylist.example.txt"
  fi
}

_sync_list_cache() {
  local name src dst deny_src
  if [ -n "${LOCALAPPDATA:-}" ] && [ -d "$LOCALAPPDATA" ]; then
    CACHE_DIR="${LOCALAPPDATA}/safe-cli-git-hooks"
  else
    CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/safe-cli-git-hooks"
  fi
  mkdir -p "$CACHE_DIR"

  deny_src="$(_resolve_denylist_source)"
  if [ "$deny_src" = "${HOOK_DIR}/denylist.example.txt" ]; then
    echo -e "${YEL:-}Hinweis:${NC:-} denylist.txt fehlt — nutze denylist.example.txt. Bitte cp denylist.example.txt denylist.txt und anpassen." >&2
  fi

  src="$deny_src"
  dst="${CACHE_DIR}/denylist.txt"
  if [ ! -f "$dst" ] || [ "$src" -nt "$dst" ]; then
    cp "$src" "$dst"
  fi

  src="${HOOK_DIR}/allowlist.txt"
  dst="${CACHE_DIR}/allowlist.txt"
  if [ -f "$src" ] && { [ ! -f "$dst" ] || [ "$src" -nt "$dst" ]; }; then
    cp "$src" "$dst"
  fi

  DENYLIST="${CACHE_DIR}/denylist.txt"
  ALLOWLIST="${CACHE_DIR}/allowlist.txt"
}
