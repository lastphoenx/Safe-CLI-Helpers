# Lokaler Cache für Denylist/Allowlist (schneller als OneDrive bei jedem Commit).
# Windows: %LOCALAPPDATA%\safe-cli-git-hooks
# Linux/macOS: ~/.cache/safe-cli-git-hooks

_sync_list_cache() {
  local name src dst
  if [ -n "${LOCALAPPDATA:-}" ] && [ -d "$LOCALAPPDATA" ]; then
    CACHE_DIR="${LOCALAPPDATA}/safe-cli-git-hooks"
  else
    CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/safe-cli-git-hooks"
  fi
  mkdir -p "$CACHE_DIR"

  for name in denylist.txt allowlist.txt; do
    src="${HOOK_DIR}/${name}"
    dst="${CACHE_DIR}/${name}"
    if [ ! -f "$dst" ] || [ "$src" -nt "$dst" ]; then
      cp "$src" "$dst"
    fi
  done

  DENYLIST="${CACHE_DIR}/denylist.txt"
  ALLOWLIST="${CACHE_DIR}/allowlist.txt"
}
