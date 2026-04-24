# Safe-CLI-Helpers Documentation

Umfassende Dokumentation für alle Command-Line Helper Tools.

## 📚 Verfügbare Dokumentationen

### Virtual Environment Management

Professionelles Python venv-Management für Development und Production.

- **[venv_rotate.sh](venv_rotate.md)** - Production: Datierte venvs mit Rotation
- **[venv_switch.sh](venv_switch.md)** - Helper: Schnelles Projekt-Switching (cd + activate)
- **[setup_venv.sh / setup_venv.ps1](setup_venv.md)** - Development: Lokales `.venv` Setup

**Siehe auch:** [Komplett-Guide: pcloud-tools/docs/VENV_MANAGEMENT.md](../../pcloud-tools/docs/VENV_MANAGEMENT.md)

### Git Helpers

- **[sync_repos.sh](sync_repos.md)** - Bulk repo sync (Status + Auto-Pull)

*(Coming soon)*

- **cheatx.py** - Git cheatsheet
- **gix.py** - Git interactive helper

### File System Helpers

*(Coming soon)*

- **fsx.py** - File system explorer

---

## 🚀 Quick Start

### Installation

```bash
# Globale Verfügbarkeit (empfohlen)
sudo ln -s /opt/apps/Safe-CLI-Helpers/tools/venv_rotate.sh /usr/local/bin/
sudo ln -s /opt/apps/Safe-CLI-Helpers/tools/venv_switch.sh /usr/local/bin/

# Dann von überall nutzbar
sudo venv_rotate.sh /opt/apps/myproject
source venv_switch.sh myproject
```

### Typische Workflows

#### Development Setup

```bash
# 1. Repo klonen
git clone https://github.com/user/project.git
cd project

# 2. Lokale venv erstellen
./scripts/setup_venv.sh    # Linux
.\scripts\setup_venv.ps1    # Windows

# 3. Aktivieren
source .venv/bin/activate
```

#### Production Deployment

```bash
# 1. Neue venv mit Rotation erstellen
sudo venv_rotate.sh --keep 3 /opt/apps/myproject

# 2. Services neustarten (nutzen Symlink)
sudo systemctl restart myproject.service

# 3. Bei Problemen: Rollback
sudo ln -sfn /opt/apps/myproject/venv-previous /opt/apps/myproject/venv
sudo systemctl restart myproject.service
```

#### Quick Switching

```bash
# Zwischen Projekten wechseln (cd + activate)
source venv_switch.sh pcloud-tools
source venv_switch.sh entropywatcher

# Status
source venv_switch.sh --status

# Deaktivieren
source venv_switch.sh --deactivate
```

---

## 📖 Dokumentations-Übersicht

### Venv Tools

| Tool | Zweck | Platform | Docs |
|------|-------|----------|------|
| `venv_rotate.sh` | Production venv mit Rotation | Linux | [→](venv_rotate.md) |
| `venv_switch.sh` | cd + activate Helper | Linux | [→](venv_switch.md) |
| `setup_venv.sh` | Dev: Lokale .venv | Linux | [→](setup_venv.md) |
| `setup_venv.ps1` | Dev: Lokale .venv | Windows | [→](setup_venv.md) |

---

## 🔗 Cross-References

### Zentrale Dokumentation

Für umfassende venv-Workflows siehe:
- **[pcloud-tools/docs/VENV_MANAGEMENT.md](../../pcloud-tools/docs/VENV_MANAGEMENT.md)**

### Projekt-spezifische Docs

- **pcloud-tools:** `/scripts/README.md` - Script-Dokumentation
- **entropywatcher:** `/docs/` - Setup-Guides

---

## 🛠️ Contribution Guide

### Neue Tool-Dokumentation hinzufügen

1. Erstelle `docs/<tool-name>.md`
2. Folge der Template-Struktur (siehe existierende Docs)
3. Update `docs/README.md` (diese Datei)
4. Commit mit aussagekräftiger Message

### Dokumentations-Template

```markdown
# tool_name.sh

Kurzbeschreibung (1 Satz).

## Zweck

Was löst das Tool?

## Features

- ✅ Feature 1
- ✅ Feature 2

## Verwendung

### Basic

\`\`\`bash
./tool_name.sh [options]
\`\`\`

### Mit Optionen

\`\`\`bash
./tool_name.sh --option value
\`\`\`

## Optionen

| Option | Default | Beschreibung |
|--------|---------|--------------|
| `--opt` | value | Was macht es |

## Beispiele

\`\`\`bash
# Beispiel 1
./tool_name.sh --example

# Beispiel 2
./tool_name.sh --advanced
\`\`\`

## Troubleshooting

### Problem 1

**Lösung:** ...

## Siehe auch

- [related-tool](related-tool.md)
```

---

## 📝 Changelog

### 2026-04-24

- ✅ Initial docs erstellt
- ✅ venv_rotate.sh dokumentiert
- ✅ venv_switch.sh dokumentiert
- ✅ setup_venv.sh/ps1 dokumentiert
- ✅ README.md (diese Datei) erstellt

---

## 📧 Kontakt & Support

Bei Fragen oder Problemen:
- GitHub Issues: [Safe-CLI-Helpers](https://github.com/lastphoenx/Safe-CLI-Helpers)
- Siehe auch: [pcloud-tools Docs](../../pcloud-tools/docs/)
