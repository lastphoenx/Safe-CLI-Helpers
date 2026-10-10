# Gemeinsame Scan-Logik für pre-commit und pre-push (nur Diff-Zeilen, kein Vollscan).

# shellcheck source=cache-lib.sh
. "${HOOK_DIR}/cache-lib.sh"

# Privates Homelab-Doku-Repo: PII-Denylist aus, Secrets/Keys bleiben aktiv.
# Nur wenn Git-Root die Marker-Datei .private-homelab-doku-repo enthält —
# nicht bei Ordnern «doku/»/«Doku/» in anderen Repos (deren Git-Root hat keinen Marker).
_is_private_doku_repo() {
  local root=""
  root="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  [ -f "${root}/.private-homelab-doku-repo" ]
}

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

  # Nur Passwort/Passwort-Keys — nicht «2-Pass:», «Pass 1:», «Base-Pass:» (ohne «wort»)
  if [[ "$line" =~ ([Pp][Aa][Ss][Ss]([Ww][Oo][Rr][Tt])|[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]|[Ss][Ee][Cc][Rr][Ee][Tt]|[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]|[Cc][Ll][Ii][Ee][Nn][Tt][_-]?[Ss][Ee][Cc][Rr][Ee][Tt]|[Aa][Uu][Tt][Hh][_-]?[Tt][Oo][Kk][Ee][Nn]|[Aa][Cc][Cc][Ee][Ss][Ss][_-]?[Tt][Oo][Kk][Ee][Nn]|[Pp][Rr][Ii][Vv][Aa][Tt][Ee][_-]?[Kk][Ee][Yy])[[:space:]]*[:=][[:space:]]*[^[:space:]#]+ ]]; then
    val="${BASH_REMATCH[0]}"
    val="${val#*=}"
    val="${val#"${val%%[![:space:]]*}"}"
    val="${val%%#*}"
    val="${val%"${val##*[![:space:]]}"}"
    val="${val#\"}"; val="${val%\"}"
    val="${val#\'}"; val="${val%\'}"
    lval="${val,,}"
    case "$lval" in
      none|dein_*|your_*|changeme|placeholder|example|xxx|redacted|geheim|""|*example.com*|*example.org*|sk-dein*|*dein-key*)
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

  # Homelab-PII (Namen, E-Mails, interne Hosts) ist im privaten doku-Repo erlaubt.
  _is_private_doku_repo && return 0

  for pattern in "${DENY_PATTERNS[@]}"; do
    if [[ "$line" == *"$pattern"* ]]; then
      # Denylist «Basel» vs. baseline / align-baseline (kein Ortsname)
      if [[ "${pattern,,}" == "basel" && ( "$line" == *"baseline"* || "$line" == *"align-baseline"* ) ]]; then
        continue
      fi
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

# Scannt hinzugefügte Zeilen aus Unified-Diff (stdin oder $1). Kein Voll-Diff in RAM.
_scan_unified_diff_loop() {
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
  done

  return "$blocked"
}

scan_unified_diff() {
  local diff="${1-}"
  if [ -n "$diff" ]; then
    _scan_unified_diff_loop <<< "$diff"
  else
    _scan_unified_diff_loop
  fi
}

# Alle Dateien eines Commits (Initial-Push / einzelner SHA) — ohne 5MB-$()-Blob.
scan_commit_tree() {
  local sha="$1"
  local blocked=0
  local f content
  while IFS= read -r f || [ -n "$f" ]; do
    [ -z "$f" ] && continue
    case "$f" in git-hooks/*) continue ;; esac
    while IFS= read -r content || [ -n "$content" ]; do
      _check_added_line "$f" "$content" "" || blocked=1
    done < <(git show "$sha:$f" 2>/dev/null || true)
  done < <(git diff-tree --no-commit-id --name-only -r "$sha" 2>/dev/null || true)
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
