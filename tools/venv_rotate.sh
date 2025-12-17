#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
KEEP=3
PYTHON_BIN="$(command -v python3 || true)"
REQ_FILE=""
DATE_TAG="$(date +%Y%m%d-%H%M)"

log() { printf "%s\n" "$*"; }
err() { printf "ERROR: %s\n" "$*" >&2; }
run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf "[DRY] %q " "$@"; printf "\n"
  else
    "$@"
  fi
}

usage() {
  cat <<USAGE
Usage: $0 [--dry-run] [--keep N] [--python /path/python3] [--req /path/requirements.txt] /opt/apps/<project>

Options:
  --dry-run            Nur anzeigen, nichts ausführen.
  --keep N             So viele venvs behalten (neueste zuerst). Default: $KEEP
  --python PATH        Python-Interpreter (Default: autodetect: $PYTHON_BIN)
  --req FILE           Requirements-Datei (Default: <project>/main/requirements.txt)

Beispiele:
  sudo $0 /opt/apps/entropywatcher
  sudo $0 --req /tmp/requirements.lock /opt/apps/pcloud-tools
  sudo $0 --keep 3 --python /usr/bin/python3 /opt/apps/safe-ops-cli
USAGE
}

if [[ $# -lt 1 ]]; then usage; exit 2; fi
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift;;
    --keep)    KEEP="${2:-}"; shift 2;;
    --python)  PYTHON_BIN="${2:-}"; shift 2;;
    --req)     REQ_FILE="${2:-}"; shift 2;;
    -h|--help) usage; exit 0;;
    *) ARGS+=("$1"); shift;;
  esac
done
set -- "${ARGS[@]:-}"

if [[ $# -ne 1 ]]; then usage; exit 2; fi

PROJ_ROOT="$(readlink -f "$1" || true)"
if [[ -z "$PROJ_ROOT" || ! -d "$PROJ_ROOT" ]]; then
  err "Project dir not found: $1"
  exit 2
fi

case "$PROJ_ROOT" in
  /opt/apps/*) : ;;
  *) err "Project root muss unter /opt/apps/ liegen (war: $PROJ_ROOT)"; exit 2;;
esac

if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
  err "python3 nicht gefunden. Mit --python PATH setzen."
  exit 2
fi

SYMLINK="$PROJ_ROOT/venv"
NEW_VENV="$PROJ_ROOT/venv-$DATE_TAG"

if [[ -z "$REQ_FILE" ]]; then
  REQ_FILE="$PROJ_ROOT/main/requirements.txt"
fi

DEFAULT_REQS=( "click>=8.1.7" "python-dotenv>=1.0.1" )

log "== venv-rotate for: $PROJ_ROOT"
log "-- python:   $PYTHON_BIN"
log "-- new venv: $NEW_VENV"
log "-- symlink:  $SYMLINK -> $(basename "$NEW_VENV")"
log "-- keep:     $KEEP"
if [[ -f "$REQ_FILE" ]]; then
  log "-- reqs:     $REQ_FILE"
else
  log "-- reqs:     (not found) -> using defaults: ${DEFAULT_REQS[*]}"
fi
echo

if [[ -d "$NEW_VENV" ]]; then
  log "✓ venv exists: $NEW_VENV"
else
  log "→ create venv…"
  run "$PYTHON_BIN" -m venv "$NEW_VENV"
  run "$NEW_VENV/bin/python" -m pip install -U pip setuptools wheel
fi

if [[ -f "$REQ_FILE" ]]; then
  log "→ install requirements.txt"
  run "$NEW_VENV/bin/python" -m pip install -r "$REQ_FILE"
else
  log "→ install default minimal requirements"
  run "$NEW_VENV/bin/python" -m pip install "${DEFAULT_REQS[@]}"
fi

log "→ sanity check"
run "$NEW_VENV/bin/python" -V || true

log "→ link: $SYMLINK -> $(basename "$NEW_VENV")"
run ln -sfn "$NEW_VENV" "$SYMLINK"

log "→ prune old venvs (keep $KEEP)"
shopt -s nullglob
pushd "$PROJ_ROOT" >/dev/null
VENVS=( $(ls -1dt venv-* 2>/dev/null || true) )
ACTIVE="$(readlink -f "$SYMLINK" || true)"
COUNT=0
for v in "${VENVS[@]}"; do
  ((COUNT++))
  if (( COUNT <= KEEP )); then
    continue
  fi
  if [[ -n "$ACTIVE" && "$(readlink -f "$v")" == "$ACTIVE" ]]; then
    continue
  fi
  log "   remove: $v"
  run rm -rf -- "$v"
done
popd >/dev/null
shopt -u nullglob

log "== done."
