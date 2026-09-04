# Git-Hooks: PII- und Secret-Schutz

Zentrale Pre-commit-/Pre-push-Hooks für alle Repos unter `github_code`.
Blockiert private Strings, Klartext-Secrets und riskante Dateien **bevor** sie committed werden.

## Schnellstart

```powershell
cd Safe-CLI-Helpers
.\scripts\install-git-hooks.ps1
```

Oder einzelnes Repo:

```bash
python tools/gix.py protect install
```

## Was blockiert wird

| Kategorie | Beispiele |
|-----------|-----------|
| **Dateinamen** | `.env`, `.pem`, `.key`, `state/`, `credentials`, `secrets.json` |
| **PII (denylist.txt)** | private E-Mail-Domains, Orte, Vornamen, Nachnamen, interne Host-/Domain-Strings (siehe `denylist.txt`) |
| **Secrets im Text** | Klartext-Zuweisungen (Passwort, API-Key, Private Keys) |
| **Gitleaks** (optional) | AWS-Keys, Tokens, weitere bekannte Secret-Patterns |

## Allowlist

Platzhalter in `allowlist.txt` sind erlaubt, z.B. `dein.name@example.com`, `DEIN_APP_PASSWORT`, `example.com`.

Denylist/Allowlist bei Bedarf anpassen — gilt für **alle** Repos mit installiertem Hook.

Listen werden beim ersten Lauf nach `%LOCALAPPDATA%\safe-cli-git-hooks\` gespiegelt (nur bei Änderung neu kopiert) — schneller als OneDrive bei jedem Commit.

## Gitleaks (empfohlen)

```powershell
winget install Gitleaks.Gitleaks
```

Ohne Gitleaks laufen Denylist + Secret-Regex trotzdem. **pre-commit/pre-push** prüfen nur geänderte Zeilen (Diff) — typisch unter 1 Sekunde.

Gitleaks beim Push nur opt-in (kann sonst sehr langsam sein):

```powershell
$env:GITLEAKS_PRE_PUSH = "1"   # nur wenn gewünscht
git push
```

## Deaktivieren

```bash
python tools/gix.py protect uninstall   # ein Repo
git config --unset core.hooksPath         # manuell
```

**Nicht empfohlen:** `git commit --no-verify` umgeht den Hook.

## Hinweise

- Hooks schützen nur **neue** Commits. Bestehende History bleibt unverändert.
- Sehr generische Vornamen in der Denylist können False Positives erzeugen — Zeile anpassen oder Allowlist erweitern.
- Öffentliche Repos zusätzlich mit GitHub Secret Scanning / Gitleaks CI absichern.
