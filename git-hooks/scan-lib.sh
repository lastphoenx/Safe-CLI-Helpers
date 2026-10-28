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

# RHS von password=/secret=/token=: kein Klartext-Secret, sondern Code/Typ/leer.
_secret_rhs_is_code_not_literal() {
  local v="$1"
  v="${v#"${v%%[![:space:]]*}"}"
  v="${v%"${v##*[![:space:]]}"}"
  v="${v%%#*}"
  v="${v%"${v##*[![:space:]]}"}"
  [ -z "$v" ] && return 0
  case "$v" in
    str|int|bool|float|bytes|None|Any|Path|Optional*|dict|list|tuple|Mapping|Sequence|Callable*)
      return 0 ;;
  esac
  [[ "$v" =~ ^[a-zA-Z_][a-zA-Z0-9_.]*\(\) ]] && return 0
  [[ "$v" =~ ^[a-zA-Z_][a-zA-Z0-9_.]*\(.*\) ]] && return 0
  [[ "$v" =~ ^os\.getenv\( ]] && return 0
  [[ "$v" =~ ^self\.[a-zA-Z_] ]] && return 0
  [[ "$v" =~ ^cfg\.[a-zA-Z_] ]] && return 0
  return 1
}

# Nur diese Werte rechts von secret-ähnlichen Keys — einheitliche Platzhalter (docs/git-hooks.md).
_secret_rhs_is_placeholder() {
  local v="$1"
  v="${v#"${v%%[![:space:]]*}"}"
  v="${v%"${v##*[![:space:]]}"}"
  v="${v%%#*}"
  v="${v%"${v##*[![:space:]]}"}"
  v="${v#\"}"; v="${v%\"}"
  v="${v#\'}"; v="${v%\'}"
  [ -z "$v" ] && return 0
  local lv="${v,,}"
  case "$lv" in
    changeme|placeholder|xxx|redacted|geheim|none|example) return 0 ;;
    dein_*|your_*|sk-dein*) return 0 ;;
    \<password\>|\<secret\>|\<token\>|\<api_key\>|\<app_password\>) return 0 ;;
    …|...|…) return 0 ;;
  esac
  [[ "$lv" =~ @example\.(com|org)$ ]] && return 0
  [[ "$lv" =~ ^[a-z0-9._-]+@example\.(com|org)$ ]] && return 0
  return 1
}

# Docker Compose / YAML: Wert ist ${ENV_NAME}, kein Klartext.
_secret_rhs_is_env_var_reference() {
  local v="$1"
  v="${v#"${v%%[![:space:]]*}"}"
  v="${v%"${v##*[![:space:]]}"}"
  [[ "$v" =~ ^\$\{[A-Za-z_][A-Za-z0-9_]*\}$ ]] && return 0
  return 1
}

_secret_assignment_rhs() {
  local keyval="$1"
  local val=""
  if [[ "$keyval" == *"="* ]]; then
    val="${keyval#*=}"
  else
    val="${keyval#*:}"
  fi
  val="${val#"${val%%[![:space:]]*}"}"
  val="${val%"${val##*[![:space:]]}"}"
  val="${val#`}"; val="${val%`}"
  echo "$val"
}

# Prüft eine hinzugefügte Zeile. Entfernte Zeilen derselben Datei im Diff
# dürfen dieselben Muster enthalten (Cleanup-Commit) — blockiert nur NEUE Einführung.
_check_added_line() {
  local file="$1"
  local line="$2"
  local removed="$3"
  local pattern keyval val lval

  # Secret-Zeilen: nie über Allowlist-Substring umgehen (PII-Allowlist gilt nur unten).
  # Markdown-Doku: keine Secret-Regex (Beispiele in Backticks); Keys in Code/.env bleiben geschützt.
  case "$file" in
    *.md|*.mdc) ;;
    *)
  if [[ "$line" =~ ([Pp][Aa][Ss][Ss]([Ww][Oo][Rr][Tt])|[Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]|[Ss][Ee][Cc][Rr][Ee][Tt]|[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]|[Cc][Ll][Ii][Ee][Nn][Tt][_-]?[Ss][Ee][Cc][Rr][Ee][Tt]|[Aa][Uu][Tt][Hh][_-]?[Tt][Oo][Kk][Ee][Nn]|[Aa][Cc][Cc][Ee][Ss][Ss][_-]?[Tt][Oo][Kk][Ee][Nn]|[Pp][Rr][Ii][Vv][Aa][Tt][Ee][_-]?[Kk][Ee][Yy])[[:space:]]*[:=][[:space:]]*[^[:space:]#]+ ]]; then
    keyval="${BASH_REMATCH[0]}"
    val="$(_secret_assignment_rhs "$keyval")"
    lval="${val,,}"
    _secret_rhs_is_code_not_literal "$lval" && return 0
    _secret_rhs_is_placeholder "$val" && return 0
    _secret_rhs_is_env_var_reference "$val" && return 0
    echo -e "${RED}BLOCKIERT${NC} ${file} — Secret-Zuweisung ohne erlaubten Platzhalter (DEIN_*, YOUR_*, leer, changeme, …)" >&2
    echo "  → ${line}" >&2
    return 1
  fi
  ;;
  esac

  if [[ "$line" == *"BEGIN PRIVATE KEY"* || "$line" == *"BEGIN RSA PRIVATE KEY"* || "$line" == *"BEGIN OPENSSH PRIVATE KEY"* ]]; then
    echo -e "${RED}BLOCKIERT${NC} ${file} — Private Key im Inhalt" >&2
    return 1
  fi

  # Homelab-PII (Namen, E-Mails, interne Hosts) ist im privaten doku-Repo erlaubt.
  _is_private_doku_repo && return 0

  for pattern in "${DENY_PATTERNS[@]}"; do
    if [[ "$line" == *"$pattern"* ]]; then
      _line_allowed "$line" && continue
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
    | grep -vE '(^|/)categories\.example\.txt$' \
    | grep -E '\.env($|\.|/)|(^|/)state/|(^|/)categories\.txt$|(^|/)categories\.private\.txt$|\.pem$|\.key$|(^|/)credentials(\.|$)|id_rsa($|\.|/)|\.p12$|\.pfx$|secrets\.json$' || true)
  if [ -n "$risky" ]; then
    echo -e "${RED}ABBRUCH: Sensible Dateien dürfen nicht committed werden (.env, categories.txt, Keys, state/, credentials).${NC}" >&2
    return 1
  fi
  return 0
}
