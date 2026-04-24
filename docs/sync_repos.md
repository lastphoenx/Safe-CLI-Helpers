# sync_repos.sh

Synchronisiert mehrere Git-Repositories gleichzeitig mit GitHub/Remote.

## Zweck

Bulk-Synchronisation kritischer Repos für schnelle Updates aller Projekte auf einmal.

## Features

- ✅ Multi-Repo Synchronisation in einem Durchlauf
- ✅ Status-Only Mode (kein Pull, nur Anzeige)
- ✅ Dry-Run Mode (Test ohne Änderungen)
- ✅ Intelligente Divergence-Erkennung
- ✅ Detailliertes Logging mit Timestamps
- ✅ Branch-Tracking
- ✅ Error-Handling pro Repo

## Verwendung

### Basic Sync

```bash
# Status prüfen + Pull bei Updates
./sync_repos.sh
```

### Status-Only (kein Pull)

```bash
# Nur anzeigen welche Repos Updates haben
./sync_repos.sh --status
```

### Dry-Run (Test-Modus)

```bash
# Zeige was passieren würde ohne zu ändern
./sync_repos.sh --dry-run
```

## Konfigurierte Repositories

Standard-Konfiguration in Script:

```bash
REPOS=(
    [entropywatcher]="/opt/apps/entropywatcher/main"
    [pcloud-tools]="/opt/apps/pcloud-tools/main"
    [rtb]="/opt/apps/rtb"
    [safe-ops-cli]="/opt/apps/safe-ops-cli/main"
)
```

**Anpassen:** Edit `sync_repos.sh` und füge/entferne Repos hinzu.

## Repo-Status-Codes

| Status | Bedeutung | Action |
|--------|-----------|--------|
| **OK** | Bereits aktuell | Nichts zu tun |
| **AHEAD** | Lokale Commits nicht gepusht | Warnung (kein Pull) |
| **PULLED** | Updates gepullt | Erfolgreich aktualisiert |
| **ERROR** | Fehler aufgetreten | Check Logs |

## Szenarien

### 1. Alle Repos aktuell

```bash
$ ./sync_repos.sh
[sync-repos] ════════════════════════════════════════════════════════════════════
[sync-repos] Repository Sync (2026-04-24 15:30:22)
[sync-repos] ════════════════════════════════════════════════════════════════════

[sync-repos] ───────────────────────────────────────────────────────────────────
[sync-repos] Repo: pcloud-tools
[sync-repos] Path: /opt/apps/pcloud-tools/main
[sync-repos] Branch: main
[sync-repos] ✓ pcloud-tools: Bereits aktuell (Branch: main)

[sync-repos] ───────────────────────────────────────────────────────────────────
[sync-repos] Repo: entropywatcher
[sync-repos] Path: /opt/apps/entropywatcher/main
[sync-repos] Branch: main
[sync-repos] ✓ entropywatcher: Bereits aktuell (Branch: main)

[sync-repos] ════════════════════════════════════════════════════════════════════
[sync-repos] Summary
[sync-repos] ════════════════════════════════════════════════════════════════════
[sync-repos] ℹ Repos verarbeitet (4 total, 0 Fehler)
```

### 2. Updates verfügbar (Auto-Pull)

```bash
$ ./sync_repos.sh
[sync-repos] Repo: pcloud-tools
[sync-repos] ℹ pcloud-tools: Remote AHEAD - Update verfügbar
[sync-repos] ℹ Pulling... (3 neue Commit(s))
[sync-repos] ✓ pcloud-tools: Erfolgreich gepullt (3 Commits, Branch: main)
[sync-repos]   ## main...origin/main
[sync-repos]   M  scripts/backup.py
[sync-repos]   ?? new_file.txt
```

### 3. Lokale Commits nicht gepusht (AHEAD)

```bash
$ ./sync_repos.sh
[sync-repos] Repo: rtb
[sync-repos] ℹ rtb: Local AHEAD von Remote (lokale Commits nicht gepusht, Branch: main)
# → Kein Pull durchgeführt, manuelle Aktion nötig
```

### 4. Divergence (Merge nötig)

```bash
$ ./sync_repos.sh
[sync-repos] Repo: safe-ops-cli
[sync-repos] ✗ ERROR: safe-ops-cli: Branches haben sich divergiert (merge nötig)
# → Manueller Merge erforderlich
```

## Status-Only Mode

Nur anzeigen ohne zu pullen:

```bash
$ ./sync_repos.sh --status
[sync-repos] Repo: pcloud-tools
[sync-repos] ℹ pcloud-tools: Remote AHEAD - Update verfügbar
f4d5449 Add venv management tools
e8c2103 Fix backup-pipeline error handling
a1b2c3d Update documentation
# → Zeigt verfügbare Commits, aber pullt nicht
```

**Use Case:** Schnell prüfen ob Updates verfügbar sind.

## Dry-Run Mode

Test ohne Änderungen:

```bash
$ ./sync_repos.sh --dry-run
[sync-repos] Repo: pcloud-tools
[sync-repos] ℹ [DRY-RUN] Würde 3 Commit(s) pullen:
f4d5449 Add venv management tools
e8c2103 Fix backup-pipeline error handling
a1b2c3d Update documentation
# → Zeigt was passieren würde, ändert aber nichts
```

**Use Case:** Sicherstellen dass keine unerwarteten Änderungen passieren.

## Workflow

### Daily Sync aller Projekte

```bash
# Morgens: Alle Repos aktualisieren
./sync_repos.sh

# → Alle Projekte auf neuestem Stand
```

### Pre-Deployment Check

```bash
# Vor größeren Änderungen: Status prüfen
./sync_repos.sh --status

# Wenn alles OK: Pull durchführen
./sync_repos.sh
```

### Automation via Cron

```bash
# Täglich um 6:00 Uhr
0 6 * * * /opt/apps/Safe-CLI-Helpers/tools/sync_repos.sh >> /var/log/sync_repos.log 2>&1
```

## Fehlerbehandlung

### Network/Auth Fehler

```bash
[sync-repos] ✗ ERROR: pcloud-tools: git fetch fehlgeschlagen (Netzwerk/Auth/SSH-Key)
fatal: Could not read from remote repository.
```

**Lösung:**
```bash
# SSH-Key prüfen
ssh -T git@github.com

# Oder HTTPS-Credentials
git config credential.helper store
```

### Keine Schreibberechtigung

```bash
[sync-repos] ✗ ERROR: pcloud-tools: Keine Schreibberechtigung
```

**Lösung:**
```bash
# Permissions korrigieren
sudo chown -R user:user /opt/apps/pcloud-tools
```

### Branch divergiert

```bash
[sync-repos] ✗ ERROR: rtb: Branches haben sich divergiert (merge nötig)
```

**Lösung:**
```bash
# Manueller Merge
cd /opt/apps/rtb
git status
git merge origin/main
# oder
git rebase origin/main
```

## Eigene Repos hinzufügen

Edit `sync_repos.sh`:

```bash
declare -A REPOS=(
    [entropywatcher]="/opt/apps/entropywatcher/main"
    [pcloud-tools]="/opt/apps/pcloud-tools/main"
    [rtb]="/opt/apps/rtb"
    [safe-ops-cli]="/opt/apps/safe-ops-cli/main"
    
    # Eigene Repos hinzufügen
    [myproject]="/home/user/myproject"
    [website]="/var/www/site"
)
```

## Exit Codes

| Code | Bedeutung |
|------|-----------|
| `0` | Alle Repos erfolgreich synchronisiert |
| `1` | Mindestens ein Repo mit Fehler |

**Verwendung in Scripts:**

```bash
if ./sync_repos.sh; then
    echo "Alle Repos aktuell"
else
    echo "Fehler bei Synchronisation"
    # → Benachrichtigung senden
fi
```

## Best Practices

### Daily Workflow

```bash
# 1. Status prüfen
./sync_repos.sh --status

# 2. Wenn Updates: Pull durchführen
./sync_repos.sh

# 3. Nach Pull: Services neustarten (falls nötig)
sudo systemctl restart myservice.service
```

### Vor größeren Änderungen

```bash
# 1. Alle Repos auf neuesten Stand bringen
./sync_repos.sh

# 2. Dann eigene Änderungen machen
cd /opt/apps/pcloud-tools/main
git checkout -b feature/my-changes
# ... arbeiten ...
```

### Automation

✅ **DO:**
- Logs nach `/var/log/` schreiben
- Fehler-Benachrichtigung via E-Mail/Telegram
- Status-Only für häufige Checks
- Dry-Run vor Production-Updates

❌ **DON'T:**
- Nicht während laufender Deployments
- Nicht ohne Backup-Strategie
- Nicht bei instabiler Netzwerkverbindung

## Monitoring Integration

### Mit Telegram-Benachrichtigung

```bash
#!/bin/bash
# sync_repos_monitored.sh

LOG_FILE="/tmp/sync_repos_$$.log"

if ! /opt/apps/Safe-CLI-Helpers/tools/sync_repos.sh > "$LOG_FILE" 2>&1; then
    # Fehler: Telegram-Benachrichtigung senden
    /opt/apps/pcloud-tools/main/scripts/send_telegram.sh \
        "🔄 Repo-Sync fehlgeschlagen" \
        "$(cat "$LOG_FILE")"
fi

rm -f "$LOG_FILE"
```

### Mit Status-JSON

```bash
#!/bin/bash
# sync_repos_to_json.sh

OUTPUT="/opt/apps/monitoring/repos_status.json"

/opt/apps/Safe-CLI-Helpers/tools/sync_repos.sh --status | \
    python3 -c '
import sys, json
status = {"repos": [], "timestamp": "$(date -Iseconds)"}
# ... Parse Log-Output zu JSON ...
print(json.dumps(status))
' > "$OUTPUT"
```

## Vergleich mit git-fetch-all

| Aspekt | sync_repos.sh | git fetch --all |
|--------|---------------|-----------------|
| **Multi-Repo** | ✅ Ja | ❌ Nur aktuelles Repo |
| **Auto-Pull** | ✅ Ja | ❌ Nur Fetch |
| **Status** | ✅ Detailliert | ❌ Minimal |
| **Logging** | ✅ Strukturiert | ❌ Basic |
| **Dry-Run** | ✅ Ja | ❌ Nein |

## Troubleshooting

### "Keine .git Verzeichnis"

**Ursache:** Repo-Pfad falsch konfiguriert.

**Lösung:**
```bash
# Prüfe Pfad
ls -la /opt/apps/pcloud-tools/main/.git

# Korrigiere in sync_repos.sh
[pcloud-tools]="/opt/apps/pcloud-tools/main"  # Richtig
[pcloud-tools]="/opt/apps/pcloud-tools"       # Falsch (wenn .git in main/)
```

### "Remote-Branch nicht verfügbar"

**Ursache:** Branch wurde remote umbenannt/gelöscht.

**Lösung:**
```bash
cd /opt/apps/pcloud-tools/main
git branch -a                    # Alle Branches anzeigen
git checkout main                # Zu Haupt-Branch wechseln
```

### Script hängt bei git fetch

**Ursache:** Netzwerk-Timeout oder SSH-Key Passphrase-Prompt.

**Lösung:**
```bash
# SSH-Agent starten (für key ohne Passphrase-Prompt)
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa

# Oder: Git Timeout setzen
git config --global http.timeout 10
```

## Siehe auch

- [venv_rotate.sh](venv_rotate.md) - Nach Repo-Sync: venv aktualisieren
- [venv_switch.sh](venv_switch.md) - Schnell zwischen aktualisierten Repos wechseln
- Git Docs: [git-fetch](https://git-scm.com/docs/git-fetch), [git-pull](https://git-scm.com/docs/git-pull)
