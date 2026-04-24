#!/usr/bin/env bash
# venv_switch.sh — Aktiviere/Deaktiviere Python venv und wechsle ins Projekt-Verzeichnis
#
# WICHTIG: Muss mit 'source' aufgerufen werden!
#
# Usage:
#   source venv_switch.sh --activate /opt/apps/pcloud-tools
#   source venv_switch.sh --activate pcloud-tools     # Kurzform (sucht unter /opt/apps/)
#   source venv_switch.sh pcloud-tools                # --activate ist optional
#   source venv_switch.sh --deactivate
#   source venv_switch.sh --status                    # Zeige aktive venv
#
# Features:
#   - Folgt venv-Symlink (erzeugt von venv_rotate.sh)
#   - cd ins Projekt-Verzeichnis
#   - Deaktiviert vorherige venv automatisch
#   - Zeigt aktive venv und Python-Version

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helpers
_vs_log_success() { echo -e "${GREEN}✓${NC} $1"; }
_vs_log_info() { echo -e "${CYAN}ℹ${NC} $1"; }
_vs_log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
_vs_log_error() { echo -e "${RED}✗${NC} $1"; }

# Check: Wurde mit 'source' aufgerufen?
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    _vs_log_error "Dieses Script muss mit 'source' aufgerufen werden!"
    echo "  Richtig:  source venv_switch.sh pcloud-tools"
    echo "  Falsch:   ./venv_switch.sh pcloud-tools"
    exit 1
fi

# Parse arguments
ACTION="activate"
PROJECT_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --activate)
            ACTION="activate"
            shift
            PROJECT_PATH="${1:-}"
            shift
            ;;
        --deactivate)
            ACTION="deactivate"
            shift
            ;;
        --status)
            ACTION="status"
            shift
            ;;
        -h|--help)
            cat <<HELP
Usage: source venv_switch.sh [OPTIONS] [PROJECT]

Options:
  --activate PATH    Aktiviere venv für Projekt (default action)
  --deactivate       Deaktiviere aktuelle venv
  --status           Zeige aktive venv
  -h, --help         Diese Hilfe

Beispiele:
  source venv_switch.sh pcloud-tools
  source venv_switch.sh --activate /opt/apps/entropywatcher
  source venv_switch.sh --deactivate
  source venv_switch.sh --status

Kurzformen (ohne /opt/apps/ Präfix):
  source venv_switch.sh pcloud-tools
  → sucht unter /opt/apps/pcloud-tools/venv
HELP
            return 0
            ;;
        *)
            # Positional argument = PROJECT_PATH
            if [[ -z "$PROJECT_PATH" ]]; then
                PROJECT_PATH="$1"
            fi
            shift
            ;;
    esac
done

# ===== ACTION: status =====
if [[ "$ACTION" == "status" ]]; then
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        _vs_log_success "Aktive venv: $VIRTUAL_ENV"
        python --version 2>&1 | sed 's/^/  /'
        
        # Projekt-Pfad: Entweder aus Variable oder aus VIRTUAL_ENV ableiten
        if [[ -n "${VIRTUAL_ENV_PROJECT:-}" ]]; then
            echo "  Projekt: $VIRTUAL_ENV_PROJECT"
        else
            # Leite Projekt-Pfad ab: /opt/apps/entropywatcher/venv-20260331-1756 → /opt/apps/entropywatcher
            DERIVED_PROJECT=$(dirname "$VIRTUAL_ENV")
            # Falls venv ein Symlink ist, zeige "abgeleitet"
            echo "  Projekt: $DERIVED_PROJECT (abgeleitet)"
        fi
    else
        _vs_log_info "Keine venv aktiv"
    fi
    return 0
fi

# ===== ACTION: deactivate =====
if [[ "$ACTION" == "deactivate" ]]; then
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        _vs_log_info "Deaktiviere venv: $(basename "$VIRTUAL_ENV")"
        if [[ "$(type -t deactivate)" == "function" ]]; then
            deactivate
        fi
        unset VIRTUAL_ENV_PROJECT
        _vs_log_success "Venv deaktiviert"
    else
        _vs_log_warn "Keine aktive venv zum Deaktivieren"
    fi
    return 0
fi

# ===== ACTION: activate =====

if [[ -z "$PROJECT_PATH" ]]; then
    _vs_log_error "Projekt-Pfad fehlt!"
    echo "  Verwendung: source venv_switch.sh pcloud-tools"
    return 1
fi

# Expandiere relative Pfade zu /opt/apps/
case "$PROJECT_PATH" in
    /*)
        # Absoluter Pfad
        PROJ_ROOT="$PROJECT_PATH"
        ;;
    *)
        # Relativer Pfad → unter /opt/apps/ suchen
        PROJ_ROOT="/opt/apps/$PROJECT_PATH"
        ;;
esac

# Prüfe ob Projekt-Root existiert
if [[ ! -d "$PROJ_ROOT" ]]; then
    _vs_log_error "Projekt-Verzeichnis nicht gefunden: $PROJ_ROOT"
    return 1
fi

# Prüfe venv-Symlink
VENV_LINK="$PROJ_ROOT/venv"
if [[ ! -L "$VENV_LINK" && ! -d "$VENV_LINK" ]]; then
    _vs_log_error "Kein venv gefunden: $VENV_LINK"
    echo "  Erstelle venv mit: sudo venv_rotate.sh $PROJ_ROOT"
    return 1
fi

# Folge Symlink zu echter venv
VENV_PATH="$(readlink -f "$VENV_LINK" 2>/dev/null || echo "$VENV_LINK")"

if [[ ! -f "$VENV_PATH/bin/activate" ]]; then
    _vs_log_error "Ungültige venv (kein bin/activate): $VENV_PATH"
    return 1
fi

# Deaktiviere alte venv falls aktiv
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    if [[ "$VIRTUAL_ENV" == "$VENV_PATH" ]]; then
        _vs_log_info "Venv ist bereits aktiv: $(basename "$VENV_PATH")"
        cd "$PROJ_ROOT" || return 1
        _vs_log_success "Verzeichnis: $PROJ_ROOT"
        return 0
    fi
    
    _vs_log_info "Deaktiviere vorherige venv: $(basename "$VIRTUAL_ENV")"
    if [[ "$(type -t deactivate)" == "function" ]]; then
        deactivate
    fi
fi

# Aktiviere neue venv
_vs_log_info "Aktiviere: $(basename "$VENV_PATH")"
# shellcheck disable=SC1090
source "$VENV_PATH/bin/activate"

# Speichere Projekt-Root für spätere Referenz
export VIRTUAL_ENV_PROJECT="$PROJ_ROOT"

# Wechsle ins Projekt-Verzeichnis
cd "$PROJ_ROOT" || return 1

# Success!
_vs_log_success "Venv aktiv: $(basename "$VENV_PATH")"
_vs_log_success "Verzeichnis: $PROJ_ROOT"
python --version 2>&1 | sed 's/^/  /'

return 0
