# Gemeinsame Scan-Logik für pre-commit und pre-push (nur Diff-Zeilen, kein Vollscan).

# shellcheck source=cache-lib.sh
. "${HOOK_DIR}/cache-lib.sh"

load_scan_patterns() {
  local line
  _sync_list_cache
  DENY_PATTERNS=()
  ALLOW_PATTERNS=()
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [ -z "$line" ] && continue
    DENY_PATTERNS+=("$line")
  done < "${DENYLIST}"
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [ -z "$line" ] && continue
    ALLOW_PATTERNS+=("$line")
  done < "${ALLOWLIST}"
}

_line_allowed() {
  local line="$1" allow
  for allow in "${ALLOW_PATTERNS[@]}"; do
    [[ "$line" == *"$allow"* ]] && return 0
  done
  return 1
}

_removed_lines_contain_pattern() {
  local removed="$1"
  local pattern="$2"
  local rline
  while IFS= read -r rline || [ -n "$rline" ]; do
    [[ "$rline" == *"$pattern"* ]] && return 0
  done <<< "$removed"
  return 1
}

# Prüft eine hinzugefügte Zeile. Entfernte Zeilen derselben Datei im Diff
# dürfen dieselben Muster enthalten (Cleanup-Commit) — blockiert nur NEUE Einführung.
_check_added_line() {
  local file="$1"
  local line="$2"
  local removed="$3"
  local pattern val lval

  _line_allowed "$line" && return 0

  if [[ "$line" =~ ([Pp][Aa][Ss][Ss]([Ww][Oo][Rr][Tt])?|[Ss][Ee][Cc][Rr][Ee][Tt]|[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]|[Cc][Ll][Ii][Ee][Nn][Tt][_-]?[Ss][Ee][Cc][Rr][Ee][Tt]|[Aa][Uu][Tt][Hh][_-]?[Tt][Oo][Kk][Ee][Nn]|[Aa][Cc][Cc][Ee][Ss][Ss][_-]?[Tt][Oo][Kk][Ee][Nn]|[Pp][Rr][Ii][Vv][Aa][Tt][Ee][_-]?[Kk][Ee][Yy])[[:space:]]*[:=][[:space:]]*[^[:space:]#]+ ]]; then
    val="${BASH_REMATCH[0]}"
    val="${val#*=}"
    val="${val#"${val%%[![:space:]]*}"}"
    val="${val%%#*}"
    val="${val%"${val##*[![:space:]]}"}"
    val="${val#\"}"; val="${val%\"}"
    val="${val#\'}"; val="${val%\'}"
    lval="${val,,}"
    case "$lval" in
      dein_*|your_*|changeme|placeholder|example|xxx|redacted|geheim|""|*example.com*|*example.org*)
        return 0 ;;
    esac
    echo -e "${RED}BLOCKIERT${NC} ${file} — mögliches Passwort/Secret in Zuweisung" >&2
    echo "  → ${line}" >&2
    return 1
  fi

  if [[ "$line" == *"BEGIN PRIVATE KEY"* || "$line" == *"BEGIN RSA PRIVATE KEY"* || "$line" == *"BEGIN OPENSSH PRIVATE KEY"* ]]; then
    echo -e "${RED}BLOCKIERT${NC} ${file} — Private Key im Inhalt" >&2
    return 1
  fi

  for pattern in "${DENY_PATTERNS[@]}"; do
    if [[ "$line" == *"$pattern"* ]]; then
      if _removed_lines_contain_pattern "$removed" "$pattern"; then
        continue
      fi
      echo -e "${RED}BLOCKIERT${NC} ${file} — privater String «${pattern}» (neu eingeführt)" >&2
      echo "  → ${line}" >&2
      return 1
    fi
  done
  return 0
}

# Legacy alias
_check_line() {
  _check_added_line "$1" "$2" ""
}

# Scannt nur hinzugefügte Zeilen; gesammelte Entfernungen pro Datei werden berücksichtigt.
scan_unified_diff() {
  local diff="$1"
  local current="" line content blocked=0
  local removed_buf=""

  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      "+++ b/"*)
        current="${line#+++ b/}"
        removed_buf=""
        case "$current" in git-hooks/*|/dev/null) current="" ;; esac
        ;;
      "+++ "*) current="" ; removed_buf="" ;;
      "-"*)
        [ -z "$current" ] && continue
        content="${line#-}"
        removed_buf+="${content}"$'\n'
        ;;
      "+"*)
        [ -z "$current" ] && continue
        content="${line#+}"
        _check_added_line "$current" "$content" "$removed_buf" || blocked=1
        ;;
    esac
  done <<< "$diff"

  return "$blocked"
}

_check_risky_filenames() {
  local names="$1"
  [ -z "$names" ] && return 0
  local risky
  risky=$(echo "$names" | grep -vE '(^|/)\.env(\.[a-zA-Z0-9_-]+)?\.(example|sample|template)$' \
    | grep -E '\.env($|\.|/)|(^|/)state/|\.pem$|\.key$|(^|/)credentials(\.|$)|id_rsa($|\.|/)|\.p12$|\.pfx$|secrets\.json$' || true)
  if [ -n "$risky" ]; then
    echo -e "${RED}ABBRUCH: Sensible Dateien dürfen nicht committed werden (.env, Keys, state/, credentials).${NC}" >&2
    return 1
  fi
  return 0
}
