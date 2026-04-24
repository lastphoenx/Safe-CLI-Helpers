# venv_switch.sh

Schnelles Projekt-Switching: Aktiviert Python venv und wechselt ins Projekt-Verzeichnis in einem Befehl.

## Zweck

Produktivitäts-Helper für Entwickler, die häufig zwischen Projekten wechseln.

## Features

- ✅ `cd` + `activate` in einem Befehl
- ✅ Folgt venv-Symlink (zeigt auf neueste von venv_rotate.sh)
- ✅ Deaktiviert vorherige venv automatisch
- ✅ Kurzform ohne `/opt/apps/` Präfix
- ✅ Status-Anzeige (welche venv ist aktiv?)
- ✅ Farbige Ausgabe

## ⚠️ Wichtig: Muss mit `source` aufgerufen werden!

```bash
# ✅ Richtig
source venv_switch.sh pcloud-tools

# ❌ Falsch (cd funktioniert nicht)
./venv_switch.sh pcloud-tools
```

**Grund:** `cd` funktioniert nur im aktuellen Shell-Context, nicht in Sub-Shells.

## Verwendung

### Aktivieren (Kurzform)

```bash
# Sucht unter /opt/apps/
source venv_switch.sh pcloud-tools
source venv_switch.sh entropywatcher
source venv_switch.sh safe-ops-cli
```

### Aktivieren (Vollständiger Pfad)

```bash
source venv_switch.sh /opt/apps/pcloud-tools
source venv_switch.sh /home/user/myproject
```

### Status anzeigen

```bash
source venv_switch.sh --status
```

**Ausgabe:**
```
✓ Aktive venv: /opt/apps/pcloud-tools/venv-20260424-1530
  Python 3.11.2
  Projekt: /opt/apps/pcloud-tools
```

### Deaktivieren

```bash
source venv_switch.sh --deactivate
```

## Beispiel-Session

```bash
# Start: irgendwo im System
user@server:~$ pwd
/home/user

# In pcloud-tools wechseln + venv aktivieren
user@server:~$ source venv_switch.sh pcloud-tools
ℹ Aktiviere: venv-20260424-1530
✓ Venv aktiv: venv-20260424-1530
✓ Verzeichnis: /opt/apps/pcloud-tools
  Python 3.11.2

# Jetzt automatisch im richtigen Verzeichnis
(venv) user@server:/opt/apps/pcloud-tools$ pwd
/opt/apps/pcloud-tools

# Python aus venv verfügbar
(venv) user@server:/opt/apps/pcloud-tools$ which python
/opt/apps/pcloud-tools/venv/bin/python

# Zu anderem Projekt wechseln
(venv) user@server:/opt/apps/pcloud-tools$ source venv_switch.sh entropywatcher
ℹ Deaktiviere vorherige venv: venv-20260424-1530
ℹ Aktiviere: venv-20260420-1045
✓ Venv aktiv: venv-20260420-1045
✓ Verzeichnis: /opt/apps/entropywatcher
  Python 3.11.2

# Automatisch gewechselt
(venv) user@server:/opt/apps/entropywatcher$ pwd
/opt/apps/entropywatcher

# Venv deaktivieren
(venv) user@server:/opt/apps/entropywatcher$ source venv_switch.sh --deactivate
ℹ Deaktiviere venv: venv-20260420-1045
✓ Venv deaktiviert

# Normal ohne venv
user@server:/opt/apps/entropywatcher$
```

## Optionen

| Option | Beschreibung |
|--------|--------------|
| `PROJECT` | Projekt-Name (sucht in /opt/apps/) oder vollständiger Pfad |
| `--activate` | Explizit: Aktiviere venv (default) |
| `--deactivate` | Deaktiviere aktuelle venv |
| `--status` | Zeige aktive venv |
| `-h, --help` | Hilfe anzeigen |

## Pfad-Auflösung

### Kurzform (ohne `/opt/apps/`)

```bash
source venv_switch.sh pcloud-tools
# → /opt/apps/pcloud-tools/venv
```

### Absoluter Pfad

```bash
source venv_switch.sh /opt/apps/pcloud-tools
source venv_switch.sh /home/user/myproject
# → Nutzt Pfad direkt
```

## Symlink-Handling

Das Tool folgt dem `venv`-Symlink (erstellt von [venv_rotate.sh](venv_rotate.md)):

```bash
/opt/apps/pcloud-tools/
├── venv → venv-20260424-1530    # Symlink
├── venv-20260424-1530/          # Tatsächliche venv
└── venv-20260420-1045/          # Ältere Version

# venv_switch.sh folgt Symlink → nutzt venv-20260424-1530
```

**Vorteil:** Nach `venv_rotate.sh` nutzt du automatisch die neueste venv!

## Automatic Deactivation

Beim Wechsel zwischen Projekten wird die alte venv automatisch deaktiviert:

```bash
# Projekt 1: pcloud-tools
user@server:~$ source venv_switch.sh pcloud-tools
✓ Venv aktiv: venv-20260424-1530

# Projekt 2: entropywatcher (deaktiviert pcloud-tools automatisch)
(venv) user@server:/opt/apps/pcloud-tools$ source venv_switch.sh entropywatcher
ℹ Deaktiviere vorherige venv: venv-20260424-1530    # ← Automatisch!
✓ Venv aktiv: venv-20260420-1045
```

## Integration mit Shell

### Alias (empfohlen)

Füge in `~/.bashrc` oder `~/.zshrc` hinzu:

```bash
# Alias für venv_switch.sh
alias vs='source /usr/local/bin/venv_switch.sh'

# Dann einfach:
vs pcloud-tools
vs entropywatcher
vs --status
vs --deactivate
```

### Funktion (advanced)

```bash
# In ~/.bashrc
function vs() {
  source /usr/local/bin/venv_switch.sh "$@"
}

# Tab-Completion für Projekt-Namen
_vs_complete() {
  local projects=$(ls -1 /opt/apps/ 2>/dev/null)
  COMPREPLY=( $(compgen -W "$projects --status --deactivate --help" -- "${COMP_WORDS[COMP_CWORD]}") )
}
complete -F _vs_complete vs
```

## Exit/Return Codes

| Code | Bedeutung |
|------|-----------|
| `0` | Erfolg |
| `1` | Fehler (Projekt nicht gefunden, keine venv, etc.) |

## Fehlerbehandlung

### Projekt nicht gefunden

```bash
user@server:~$ source venv_switch.sh nonexistent
✗ Projekt-Verzeichnis nicht gefunden: /opt/apps/nonexistent
```

### Keine venv vorhanden

```bash
user@server:~$ source venv_switch.sh myproject
✗ Kein venv gefunden: /opt/apps/myproject/venv
  Erstelle venv mit: sudo venv_rotate.sh /opt/apps/myproject
```

### Bereits aktiv

```bash
(venv) user@server:/opt/apps/pcloud-tools$ source venv_switch.sh pcloud-tools
ℹ Venv ist bereits aktiv: venv-20260424-1530
✓ Verzeichnis: /opt/apps/pcloud-tools
```

## Environment Variables

Das Tool setzt folgende Variablen:

```bash
# Von Python venv (Standard)
VIRTUAL_ENV=/opt/apps/pcloud-tools/venv-20260424-1530
PATH=/opt/apps/pcloud-tools/venv-20260424-1530/bin:...

# Eigene Variable (für Referenz)
VIRTUAL_ENV_PROJECT=/opt/apps/pcloud-tools
```

### Nutzen von VIRTUAL_ENV_PROJECT

```bash
# In Skripten: Pfad zum Projekt
cd "$VIRTUAL_ENV_PROJECT/scripts"

# Zeige aktuelles Projekt
echo "Aktuelles Projekt: $VIRTUAL_ENV_PROJECT"
```

## Best Practices

### Workflow-Optimierung

```bash
# 1. Standard-Alias setzen
echo "alias vs='source venv_switch.sh'" >> ~/.bashrc
source ~/.bashrc

# 2. Schnell zwischen Projekten wechseln
vs pcloud-tools
# → arbeite im Projekt

vs entropywatcher
# → arbeit im anderen Projekt

vs --deactivate
# → zurück zu normaler Shell
```

### Mit venv_rotate.sh kombinieren

```bash
# 1. Neue venv erstellen
sudo venv_rotate.sh /opt/apps/pcloud-tools

# 2. Sofort in Projekt wechseln + neue venv nutzen
source venv_switch.sh pcloud-tools
# → Folgt Symlink, nutzt automatisch neue venv!

# 3. Test
python --version
python -c "import pandas; print(pandas.__version__)"
```

## Troubleshooting

### "Must be sourced"

**Problem:**
```bash
./venv_switch.sh pcloud-tools
✗ Dieses Script muss mit 'source' aufgerufen werden!
```

**Lösung:**
```bash
source venv_switch.sh pcloud-tools
```

### cd funktioniert nicht

**Problem:** Du bist nach `venv_switch.sh` nicht im Projekt-Verzeichnis.

**Ursache:** Script wurde ohne `source` aufgerufen.

**Lösung:** Immer mit `source` oder `.` aufrufen:
```bash
source venv_switch.sh pcloud-tools
. venv_switch.sh pcloud-tools  # Kurzform von 'source'
```

### Symlink-Fehler

**Problem:**
```bash
✗ Ungültige venv (kein bin/activate): /opt/apps/pcloud-tools/venv
```

**Lösung:** venv mit venv_rotate.sh neu erstellen:
```bash
sudo venv_rotate.sh /opt/apps/pcloud-tools
```

## Siehe auch

- [venv_rotate.sh](venv_rotate.md) - Production venv mit Rotation
- [setup_venv.sh](setup_venv.md) - Development venv Setup
- [VENV_MANAGEMENT.md](../../pcloud-tools/docs/VENV_MANAGEMENT.md) - Umfassende Doku
