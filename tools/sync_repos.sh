#!/bin/bash
#
# sync_repos.sh - Synchronisiere alle kritischen Repos mit GitHub
#
# Usage:
#   bash sync_repos.sh           # Status + Pull (wenn behind)
#   bash sync_repos.sh --status  # Nur Status anzeigen
#   bash sync_repos.sh --dry-run # Test ohne Änderungen
#

DRY_RUN=0
STATUS_ONLY=0
FAILED=0

declare -A REPOS=(
    [entropywatcher]="/opt/apps/entropywatcher/main"
    [pcloud-tools]="/opt/apps/pcloud-tools/main"
    [rtb]="/opt/apps/rtb"
    [safe-ops-cli]="/opt/apps/safe-ops-cli/main"
)

log() { printf "%s [sync-repos] %s\n" "$(date '+%F %T')" "$*" >&2; }
error() { log "✗ ERROR: $*"; }
success() { log "✓ $*"; }
info() { log "ℹ $*"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --status) STATUS_ONLY=1; shift ;;
        --dry-run) DRY_RUN=1; shift ;;
        *) error "Unbekannter Parameter: $1"; exit 1 ;;
    esac
done

log "════════════════════════════════════════════════════════════════════"
log "Repository Sync ($(date '+%F %T'))"
log "════════════════════════════════════════════════════════════════════"

for repo_name in "${!REPOS[@]}"; do
    repo_path="${REPOS[$repo_name]}"
    
    info ""
    info "─────────────────────────────────────────────────────────────────"
    info "Repo: $repo_name"
    info "Path: $repo_path"
    
    if [[ ! -d "$repo_path/.git" ]]; then
        error "$repo_name: Keine .git Verzeichnis! ($repo_path)"
        ((FAILED++))
        continue
    fi
    
    if [[ ! -w "$repo_path" ]]; then
        error "$repo_name: Keine Schreibberechtigung"
        ((FAILED++))
        continue
    fi
    
    (
        cd "$repo_path" || { error "cd fehlgeschlagen"; exit 1; }
        
        BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
        LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
        
        # Git fetch - Ausgabe filtern aber Exit-Code prüfen
        FETCH_OUTPUT=$(git fetch origin 2>&1)
        FETCH_EXIT=$?
        if [[ $FETCH_EXIT -ne 0 ]]; then
            error "$repo_name: git fetch fehlgeschlagen (Netzwerk/Auth/SSH-Key)"
            echo "$FETCH_OUTPUT" | grep -v "^hint:" >&2
            exit 1
        fi
        
        REMOTE=$(git rev-parse "origin/$BRANCH" 2>/dev/null || echo "unknown")
        
        if [[ "$REMOTE" == "unknown" ]]; then
            error "$repo_name: Remote-Branch '$BRANCH' nicht verfügbar nach fetch"
            exit 1
        fi
        
        if [[ "$LOCAL" == "$REMOTE" ]]; then
            success "$repo_name: Bereits aktuell"
            exit 0
        elif git merge-base --is-ancestor "$REMOTE" "$LOCAL" 2>/dev/null; then
            info "$repo_name: Local AHEAD von Remote (lokale Commits nicht gepusht)"
            exit 0
        elif git merge-base --is-ancestor "$LOCAL" "$REMOTE" 2>/dev/null; then
            info "$repo_name: Remote AHEAD - Update verfügbar"
            
            if [[ $STATUS_ONLY -eq 1 ]]; then
                git log "$LOCAL..$REMOTE" --oneline | head -3
                exit 0
            elif [[ $DRY_RUN -eq 1 ]]; then
                info "[DRY-RUN] Würde pullen:"
                git log "$LOCAL..$REMOTE" --oneline | head -3
                exit 0
            else
                info "Pulling..."
                if git pull origin "$BRANCH"; then
                    success "$repo_name: Erfolgreich gepullt"
                    exit 0
                else
                    error "$repo_name: Pull fehlgeschlagen"
                    exit 1
                fi
            fi
        else
            error "$repo_name: Branches haben sich divergiert (merge nötig)"
            exit 1
        fi
    )
    
    SUBSHELL_CODE=$?
    if [[ $SUBSHELL_CODE -ne 0 ]]; then
        ((FAILED++))
    fi
done

log ""
log "════════════════════════════════════════════════════════════════════"
log "Summary"
log "════════════════════════════════════════════════════════════════════"

if [[ $STATUS_ONLY -eq 1 ]]; then
    info "Status-Check abgeschlossen"
elif [[ $DRY_RUN -eq 1 ]]; then
    info "DRY-RUN abgeschlossen (keine Änderungen)"
else
    info "Repos verarbeitet"
fi

if [[ $FAILED -gt 0 ]]; then
    error "$FAILED Repo(s) mit Fehlern"
    exit 1
fi
