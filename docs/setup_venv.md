# setup_venv.sh / setup_venv.ps1

Lokales Virtual Environment Setup für Development (Windows + Linux).

## Zweck

Schnelles Setup einer lokalen `.venv` für Entwicklung und Testing ohne sudo.

## Features

- ✅ Erstellt `.venv` im Projekt-Root
- ✅ Installiert Dependencies aus `requirements.txt`
- ✅ User-Level (kein sudo)
- ✅ Plattform-übergreifend (Windows + Linux)
- ✅ VS Code Integration
- ✅ Update-Modus (aktualisiert nur Dependencies)
- ✅ Funktionstests

## Verwendung

### Linux/macOS (`setup_venv.sh`)

```bash
# Basic Setup
./scripts/setup_venv.sh

# Aktivieren
source .venv/bin/activate

# Mit Optionen
./scripts/setup_venv.sh --force        # Venv neu erstellen
./scripts/setup_venv.sh --skip-test    # Tests überspringen
```

### Windows (`setup_venv.ps1`)

```powershell
# Basic Setup
.\scripts\setup_venv.ps1

# Aktivieren
.\.venv\Scripts\Activate.ps1

# Mit Optionen
.\scripts\setup_venv.ps1 -Force        # Venv neu erstellen
.\scripts\setup_venv.ps1 -SkipTest     # Tests überspringen
```

## Optionen

### Linux/macOS

| Option | Beschreibung |
|--------|--------------|
| `--force` | Überschreibt existierende venv |
| `--skip-test` | Überspringt Funktionstests |
| `-h, --help` | Hilfe anzeigen |

### Windows

| Parameter | Beschreibung |
|-----------|--------------|
| `-Force` | Überschreibt existierende venv |
| `-SkipTest` | Überspringt Funktionstests |

## Workflow

### Erstes Setup

```bash
# 1. Repo klonen
git clone https://github.com/user/project.git
cd project

# 2. Venv erstellen
./scripts/setup_venv.sh    # Linux
.\scripts\setup_venv.ps1    # Windows

# 3. Aktivieren
source .venv/bin/activate          # Linux
.\.venv\Scripts\Activate.ps1        # Windows

# 4. Entwickeln
python scripts/my_script.py
```

### Update Dependencies

```bash
# Existierende venv: nur Dependencies aktualisieren
./scripts/setup_venv.sh

# Komplett neu erstellen
./scripts/setup_venv.sh --force
```

## Verzeichnis-Struktur

```
project/
├── .venv/                    # Lokale venv (von setup_venv erstellt)
│   ├── bin/                  # Linux: Executables
│   │   ├── python
│   │   ├── activate
│   │   └── pip
│   ├── Scripts/              # Windows: Executables
│   │   ├── python.exe
│   │   ├── Activate.ps1
│   │   └── pip.exe
│   └── lib/
├── requirements.txt
└── scripts/
    ├── setup_venv.sh         # Linux Setup-Script
    └── setup_venv.ps1        # Windows Setup-Script
```

## Funktionstests

Das Script führt automatisch Tests durch:

### 1. Python-Version

```bash
python --version
```

### 2. Modul-Imports (falls pandas/openpyxl in requirements.txt)

```bash
python -c "import pandas, openpyxl; print('OK')"
```

### 3. Projekt-Skripte (falls vorhanden)

```bash
python scripts/analyze_manifest_duplicates.py --help
```

## Update-Modus

Bei existierender venv wird nur aktualisiert (nicht neu erstellt):

```bash
./scripts/setup_venv.sh
```

**Ausgabe:**
```
⚠ Venv existiert bereits: /path/to/project/.venv
ℹ Verwende --force zum Überschreiben
ℹ Aktualisiere Dependencies...
✓ Dependencies aktualisiert

Aktiviere venv mit:
  source .venv/bin/activate
```

## VS Code Integration

VS Code erkennt `.venv` automatisch:

1. Öffne Projekt in VS Code
2. Unten links: Python-Interpreter auswählen
3. Wähle `.venv/bin/python` (Linux) oder `.venv\Scripts\python.exe` (Windows)
4. ✅ Fertig! IntelliSense und Debugging nutzen venv

### Manuell konfigurieren

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
}
```

## Pipeline-Integration

### GitHub Actions

```yaml
- name: Setup Python venv
  run: |
    chmod +x scripts/setup_venv.sh
    ./scripts/setup_venv.sh --skip-test
    source .venv/bin/activate
    python --version
```

### GitLab CI

```yaml
setup_venv:
  script:
    - ./scripts/setup_venv.sh --skip-test
    - source .venv/bin/activate
    - python --version
```

## Unterschied zu venv_rotate.sh

| Aspekt | setup_venv.sh | venv_rotate.sh |
|--------|---------------|----------------|
| **Zweck** | Development | Production |
| **Ort** | `.venv` im Projekt | `/opt/apps/<proj>/venv-*` |
| **Permissions** | User | sudo (root) |
| **Rotation** | Nein | Ja (--keep N) |
| **Rollback** | Nein | Ja (Symlink) |
| **Windows** | ✅ Ja | ❌ Nein |
| **Platform** | Windows + Linux | Linux only |

## Best Practices

### Development

✅ **DO:**
- `.venv` in `.gitignore`
- `requirements.txt` committen
- Regelmäßig `pip freeze > requirements.txt`
- setup_venv.sh committen (wiederverwendbar)

❌ **DON'T:**
- Nicht `.venv` committen (zu groß, plattform-spezifisch)
- Nicht global pip packages nutzen (immer in venv)
- Nicht mit sudo ausführen (User-Level)

### Requirements.txt

```txt
# Gute Praxis: Pin major versions
pandas>=2.0.0,<3.0.0
openpyxl>=3.1.0

# Oder: Exakte Versions für Reproduzierbarkeit
pandas==2.2.1
openpyxl==3.1.2
```

## Troubleshooting

### "Python nicht gefunden"

**Windows:**
```powershell
# Check Python-Installation
python --version
Get-Command python

# Installieren: https://www.python.org/downloads/
```

**Linux:**
```bash
# Check Python-Installation
python3 --version
which python3

# Installieren
sudo apt install python3 python3-pip python3-venv  # Debian/Ubuntu
sudo yum install python3 python3-pip               # RHEL/CentOS
```

### "Venv-Erstellung fehlgeschlagen"

**Linux:**
```bash
# python3-venv package fehlt
sudo apt install python3-venv
```

**Windows:**
```powershell
# Python nicht im PATH
# → Python neu installieren mit "Add to PATH" Option
```

### "pip install failed"

```bash
# Proxy-Probleme
pip install --proxy http://proxy:port package

# SSL-Probleme
pip install --trusted-host pypi.org package

# Permissions (sollte nicht passieren in venv)
# → Prüfe dass venv aktiviert ist
which python  # Sollte .venv/bin/python zeigen
```

### PowerShell Execution Policy

**Problem:**
```powershell
.\scripts\setup_venv.ps1
# → Execution Policy Error
```

**Lösung:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Beispiel-Ausgabe

### Linux

```bash
$ ./scripts/setup_venv.sh
ℹ Projekt-Root: /home/user/pcloud-tools
ℹ Prüfe Python-Installation...
✓ Python gefunden: Python 3.11.2
ℹ Erstelle Virtual Environment...
✓ Virtual Environment erstellt: /home/user/pcloud-tools/.venv
ℹ Upgrade pip...
ℹ Installiere Dependencies aus requirements.txt...
✓ Dependencies installiert
ℹ Teste Installation...
✓ analyze_manifest_duplicates.py funktioniert
✓ pandas & openpyxl erfolgreich importiert
✓ Setup abgeschlossen!

Nächste Schritte:
  1. Aktiviere venv:  source .venv/bin/activate
  2. Teste Skript:    python scripts/analyze_manifest_duplicates.py --help

Tipp: VS Code erkennt die venv automatisch (Statusleiste unten links)
```

### Windows

```powershell
PS> .\scripts\setup_venv.ps1
ℹ Projekt-Root: C:\Users\user\pcloud-tools
ℹ Prüfe Python-Installation...
✓ Python gefunden: Python 3.11.2
ℹ Erstelle Virtual Environment...
✓ Virtual Environment erstellt: C:\Users\user\pcloud-tools\.venv
ℹ Upgrade pip...
ℹ Installiere Dependencies aus requirements.txt...
✓ Dependencies installiert
ℹ Teste Installation...
✓ analyze_manifest_duplicates.py funktioniert
✓ pandas & openpyxl erfolgreich importiert
✓ Setup abgeschlossen!

Nächste Schritte:
  1. Aktiviere venv:  .\.venv\Scripts\Activate.ps1
  2. Teste Skript:    python scripts\analyze_manifest_duplicates.py --help

Tipp: VS Code erkennt die venv automatisch (Statusleiste unten links)
```

## Siehe auch

- [venv_rotate.sh](venv_rotate.md) - Production venv mit Rotation
- [venv_switch.sh](venv_switch.md) - Schnelles Projekt-Switching
- [VENV_MANAGEMENT.md](../../pcloud-tools/docs/VENV_MANAGEMENT.md) - Umfassende Doku
