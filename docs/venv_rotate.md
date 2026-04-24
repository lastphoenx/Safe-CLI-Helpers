# venv_rotate.sh

Erstellt datierte Python Virtual Environments mit automatischer Rotation für Production-Deployments.

## Zweck

Zero-downtime Python-Updates mit Rollback-Fähigkeit durch datierte venvs und Symlink-basierte Aktivierung.

## Features

- ✅ Datierte venvs (`venv-YYYYmmdd-HHMM`)
- ✅ Symlink `venv` → neueste Version
- ✅ Automatische Rotation (behält N neueste)
- ✅ Rollback durch Symlink-Umhängen
- ✅ Zero-downtime für systemd Services
- ✅ Sanity-Checks (Python-Version)
- ✅ Default-Requirements bei fehlender requirements.txt

## Verwendung

### Basic

```bash
# Standard (behält 3 venvs)
sudo /opt/apps/venv_rotate.sh /opt/apps/pcloud-tools
```

### Mit Optionen

```bash
# Nur 2 venvs behalten
sudo /opt/apps/venv_rotate.sh --keep 2 /opt/apps/entropywatcher

# Custom requirements
sudo /opt/apps/venv_rotate.sh --req /tmp/requirements.lock /opt/apps/pcloud-tools

# Custom Python-Interpreter
sudo /opt/apps/venv_rotate.sh --python /usr/bin/python3.11 /opt/apps/safe-ops-cli

# Dry-run (testen ohne Änderungen)
sudo /opt/apps/venv_rotate.sh --dry-run /opt/apps/pcloud-tools

# Kombiniert
sudo /opt/apps/venv_rotate.sh --keep 3 --python /usr/bin/python3.11 --req requirements.txt /opt/apps/pcloud-tools
```

## Optionen

| Flag | Default | Beschreibung |
|------|---------|--------------|
| `--keep N` | `3` | So viele venvs behalten (neueste zuerst) |
| `--python PATH` | autodetect | Python-Interpreter Pfad |
| `--req FILE` | `main/requirements.txt` | Requirements-Datei |
| `--dry-run` | - | Nur anzeigen, nichts ausführen |

## Verzeichnis-Struktur

```
/opt/apps/pcloud-tools/
├── venv → venv-20260424-1530       # Symlink (aktuell)
├── venv-20260424-1530/             # Neueste
│   ├── bin/
│   │   ├── python
│   │   ├── activate
│   │   └── pip
│   ├── lib/
│   └── ...
├── venv-20260420-1045/             # Vorherige
└── venv-20260415-0900/             # Älteste (wird bei --keep 2 gelöscht)
```

## Workflow

### 1. Neue venv erstellen

```bash
sudo /opt/apps/venv_rotate.sh /opt/apps/pcloud-tools
```

**Schritte:**
1. Erstellt `venv-20260424-1530/`
2. Installiert pip, setuptools, wheel
3. Installiert requirements.txt
4. Prüft Python-Version
5. Setzt Symlink: `venv → venv-20260424-1530`
6. Löscht alte venvs (behält --keep N)

### 2. Services nutzen neue venv

Systemd Services folgen dem Symlink:

```ini
[Service]
ExecStart=/opt/apps/pcloud-tools/venv/bin/python /opt/apps/pcloud-tools/main/script.py
```

- ✅ Nächste Timer-Execution nutzt automatisch neue venv
- ✅ Laufende Services unberührt (bis Neustart)

### 3. Service-Update (optional)

```bash
sudo systemctl restart pcloud-backup.service
sudo systemctl restart telegram-commander.service
```

### 4. Bei Problemen: Rollback

```bash
# Symlink auf vorherige Version setzen
sudo ln -sfn /opt/apps/pcloud-tools/venv-20260420-1045 /opt/apps/pcloud-tools/venv

# Services neustarten
sudo systemctl restart pcloud-backup.service
```

## Sicherheitsfeatures

### Pfad-Validierung

```bash
# ✅ Erlaubt: Unter /opt/apps/
sudo venv_rotate.sh /opt/apps/pcloud-tools

# ❌ Abgelehnt: Außerhalb /opt/apps/
sudo venv_rotate.sh /home/user/project
# → ERROR: Project root muss unter /opt/apps/ liegen
```

### Aktive venv wird nie gelöscht

```bash
# Auch bei --keep 1 wird die aktive venv behalten
sudo venv_rotate.sh --keep 1 /opt/apps/pcloud-tools
```

## Requirements-Handling

### Standard: requirements.txt aus Repo

```bash
/opt/apps/pcloud-tools/
└── main/
    └── requirements.txt    # ← Standard-Location
```

### Custom Requirements-Datei

```bash
# Von anderem Pfad
sudo venv_rotate.sh --req /tmp/requirements.lock /opt/apps/pcloud-tools

# Aus Repo-Unterverzeichnis
sudo venv_rotate.sh --req /opt/apps/pcloud-tools/main/requirements-prod.txt /opt/apps/pcloud-tools
```

### Fallback: Default Requirements

Bei fehlender requirements.txt:

```bash
# Installiert Minimal-Set
DEFAULT_REQS=( "click>=8.1.7" "python-dotenv>=1.0.1" )
```

## Rotation-Logik

### Beispiel: --keep 3

```bash
# Vor Rotation
venv-20260424-1530/  # Neueste (aktiv)
venv-20260420-1045/
venv-20260415-0900/
venv-20260410-1200/  # Älteste
venv-20260405-0830/

# Nach Rotation (behält 3 neueste)
venv-20260424-1530/  # Behalten (neueste)
venv-20260420-1045/  # Behalten
venv-20260415-0900/  # Behalten
# venv-20260410-1200/ → GELÖSCHT
# venv-20260405-0830/ → GELÖSCHT
```

### Sortierung

- Sortiert nach Datum **absteigend** (neueste zuerst)
- Benutzt `ls -1dt` (modification time)
- Aktive venv wird **NIE** gelöscht (auch wenn außerhalb Top-N)

## Exit Codes

| Code | Bedeutung |
|------|-----------|
| `0` | Erfolg |
| `2` | Fehler (Projekt nicht gefunden, Python fehlt, etc.) |

## Beispiel-Session

```bash
pi@pi-nas:~$ sudo /opt/apps/venv_rotate.sh /opt/apps/pcloud-tools
== venv-rotate for: /opt/apps/pcloud-tools
-- python:   /usr/bin/python3
-- new venv: /opt/apps/pcloud-tools/venv-20260424-1530
-- symlink:  venv -> venv-20260424-1530
-- keep:     3
-- reqs:     /opt/apps/pcloud-tools/main/requirements.txt

→ create venv…
→ install requirements.txt
→ sanity check
Python 3.11.2
→ link: venv -> venv-20260424-1530
→ prune old venvs (keep 3)
   remove: venv-20260410-1200
   remove: venv-20260405-0830
== done.
```

## Integration mit systemd

### Service Definition

```ini
[Unit]
Description=pCloud Backup Service
After=network.target

[Service]
Type=oneshot
# Nutzt Symlink → automatische Updates bei venv_rotate
ExecStart=/opt/apps/pcloud-tools/venv/bin/python \
          /opt/apps/pcloud-tools/main/scripts/backup.py
User=root
Group=root

[Install]
WantedBy=multi-user.target
```

### Nach venv_rotate: Service-Update

```bash
# Option 1: Manuell neustarten
sudo systemctl restart pcloud-backup.service

# Option 2: Timer lässt Service automatisch neue venv nutzen
# (bei nächster Ausführung)
```

## Best Practices

### Deployment

✅ **DO:**
- Teste neue venv vor Service-Neustart
- Behalte mindestens 2-3 venvs (--keep 3)
- Nutze --dry-run zum Testen
- Dokumentiere Custom-Requirements

❌ **DON'T:**
- Nicht `--keep 1` in Production (keine Rollback-Option!)
- Nicht manuelle venv-Ordner löschen (benutze Rotation)
- Nicht alte venvs direkt referenzieren (nutze Symlink)

### Testing nach Update

```bash
# 1. venv erstellen
sudo venv_rotate.sh /opt/apps/pcloud-tools

# 2. Teste Python-Version
/opt/apps/pcloud-tools/venv/bin/python --version

# 3. Teste Imports
/opt/apps/pcloud-tools/venv/bin/python -c "import pandas; print(pandas.__version__)"

# 4. Teste Hauptskript
/opt/apps/pcloud-tools/venv/bin/python /opt/apps/pcloud-tools/main/scripts/backup.py --help

# 5. Service neustarten (wenn Tests OK)
sudo systemctl restart pcloud-backup.service
```

## Troubleshooting

### "python3 nicht gefunden"

```bash
# Check Python-Installation
which python3
apt list --installed | grep python3

# Explizit setzen
sudo venv_rotate.sh --python /usr/bin/python3.11 /opt/apps/pcloud-tools
```

### "Project dir not found"

```bash
# Prüfe Pfad
ls -la /opt/apps/pcloud-tools

# Oder mit readlink
readlink -f /opt/apps/pcloud-tools
```

### "pip install failed"

```bash
# Check requirements.txt
cat /opt/apps/pcloud-tools/main/requirements.txt

# Manuell testen
/opt/apps/pcloud-tools/venv-20260424-1530/bin/pip install -r requirements.txt
```

### Alte venv wird nicht gelöscht

**Grund:** venv ist noch aktiv (Symlink zeigt darauf).

```bash
# Check aktive venv
readlink -f /opt/apps/pcloud-tools/venv

# Rotation läuft erst nach neuem venv_rotate.sh
```

## Siehe auch

- [venv_switch.sh](venv_switch.md) - Schnelles Projekt-Switching
- [setup_venv.sh](setup_venv.md) - Development venv Setup
- [VENV_MANAGEMENT.md](../../pcloud-tools/docs/VENV_MANAGEMENT.md) - Umfassende Doku
