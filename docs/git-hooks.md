# Git-Hooks: PII- und Secret-Schutz

Zentrale Pre-commit-/Pre-push-Hooks für alle Repos unter `github_code`.

## Ziel

**Verhindern, dass neue Geheimnisse und private Homelab-Daten in Git (und damit GitHub) landen.**

| Schützen | Nicht blockieren |
|----------|------------------|
| Echte Passwörter, Tokens, API-Keys in **Zuweisungen** | Code: `app_token: str`, `nc_app_token()` |
| Dateien `.env`, `categories.txt`, Keys, `state/` | `.env.example` mit **leerem** Wert oder **`DEIN_*` / `YOUR_*` Platzhalter** |
| Neue Denylist-PII in **öffentlichen** Repos | Beispiel-PII (`PersonA`, `example.com`) in Doku/Code |

Hooks prüfen **nur neu hinzugefügte Zeilen** (Diff). History wird nicht automatisch bereinigt.

## Schnellstart

```powershell
cd Safe-CLI-Helpers
.\scripts\install-git-hooks.ps1
```

Oder einzelnes Repo:

```bash
python tools/gix.py protect install
```

## Denylist (lokal, nicht im Repo)

Persönliche Muster stehen in **`git-hooks/denylist.txt`** — diese Datei ist **gitignored** und wird nicht gepusht.

```powershell
cd Safe-CLI-Helpers\git-hooks
copy denylist.example.txt denylist.txt
# denylist.txt lokal bearbeiten
```

Im Repo liegt nur `denylist.example.txt` (Platzhalter-Format, ohne echte Namen).

## Allowlist (öffentlich)

Nur **PII-Denylist**: wenn eine Zeile wegen `denylist.txt` blockiert würde, aber einen **generischen** Beispiel-String enthält (`example.com`, `PersonA`, …) → erlaubt.

**Nicht** für Secret-Zeilen: `PASSWORD=…` wird **nur** erlaubt wenn der **Wert** ein Standard-Platzhalter ist (siehe unten) — nie weil irgendwo im File ein Allowlist-Substring vorkommt.

## Secret-Platzhalter (einheitlich)

In `.env.example` und Doku **rechts vom `=`** nur:

| Erlaubt | Beispiel |
|---------|----------|
| leer | `PHOTOTAG_NC_APP_PASSWORD=` |
| `DEIN_*` / `YOUR_*` | `DEIN_TOKEN`, `YOUR_PASSWORD` |
| feste Wörter | `changeme`, `placeholder`, `xxx`, `redacted` |
| Winkel | `<password>`, `<secret>`, `<token>` |
| Beispiel-Mail | `user@example.com` |
| Compose-Referenz | `${POSTGRES_PASSWORD}` (nur Variable, kein Wert) |

Alles andere (`=a3rEF_a1_saP3`) → **Block**. Kein Whitelisten von **Variablennamen** oder Key-Präfixen in `allowlist.txt`.

**Docker Compose:** `environment: POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}` — erlaubt über **Referenz-Regex**, nicht über Allowlist-Substring.

Code-Zuweisungen: Typen, Funktionsaufrufe, `os.getenv(...)` — keine Klartext-Literale.

**Cursor Auto-review** ist getrennt (Freigabe für Agent-Push auf `main`) — nicht dieser Hook.

## Ausnahme: privates `doku`-Repo

`install-git-hooks.ps1` **setzt keine Hooks** im Repo mit **`.private-homelab-doku-repo`** im Git-Root
(`github_code/doku/`) — Homelab-PII darf dort committed werden, ohne Denylist-Konflikte.

**Alle anderen** Repos unter `github_code/` (z. B. `phototag`, `telegram-bot`) **müssen** Hooks haben.
Nach neuem Clone: Skript erneut ausführen (nicht automatisch).

**Nicht** betroffen: Unterordner `doku/` in anderen Repos — deren Git-Root hat keinen Marker; dort greifen Hooks normal.

Zusätzlich blockiert der Hook **`categories.txt`** (nur `categories.example.txt` erlaubt) in öffentlichen App-Repos.

Persönliche Denylist/Allowlist-Muster und Homelab-PII-Referenzen: nur im privaten `doku`-Repo
(siehe `doku/ops/safe-cli-homelab-hooks.md`), **nicht** in Safe-CLI-Helpers (öffentlich).

## Was blockiert wird

| Kategorie | Beispiele |
|-----------|-----------|
| **Dateinamen** | `.env`, `.pem`, `.key`, `state/`, `credentials`, `secrets.json` |
| **PII (denylist.txt, lokal)** | private Domains, Namen, interne Host-Strings |
| **Secrets im Text** | Klartext-Zuweisungen ohne Standard-Platzhalter (siehe «Secret-Platzhalter») |
| **Gitleaks** (optional) | AWS-Keys, Tokens, weitere bekannte Secret-Patterns |

## Cleanup-Commits

Der Hook prüft nur **hinzugefügte** Zeilen (`+`). Entfernte Zeilen (`-`) blockieren nicht.
Wird ein Muster in derselben Datei entfernt und nicht neu eingeführt, ist der Commit erlaubt
(kein Block nur weil alte sensible Zeilen im Diff stehen).

## Repos prüfen (Audit)

**Pre-commit-Hook:** blockiert neue Leaks in geänderten Zeilen.

**AGENTS.md in öffentlichen Repos** (IPs, CT-Nummern, `doku/pve2`):

```powershell
cd Safe-CLI-Helpers
.\tools\scan-agents-public.ps1 -Repo paperless-ngx-classifier
.\tools\scan-agents-public.ps1   # alle Repos unter github_code
```

Policy: privates `doku/ops/AGENTS-public-repos-policy.md`

**Voller Denylist-Scan** (kann viele False Positives — Provider-Beispiele, Ortsnamen in Tests):

```powershell
cd Safe-CLI-Helpers
.\tools\scan-repos.ps1
.\tools\scan-repos.ps1 -Diff          # nur unstaged Änderungen
.\tools\scan-repos.ps1 -Staged        # nur Index
```

**Critical-Audit vor Push** (persönliche Muster, Gate): nur lokal in der **privaten Homelab-Doku** —
`doku/ops/privacy-audit.ps1` und Ablauf in `doku/ops/privacy-cleanup-playbook.md` (nicht ins öffentliche Repo kopieren).

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
- Listen werden nach `%LOCALAPPDATA%\safe-cli-git-hooks\` gespiegelt (nur bei Änderung neu kopiert).
- Öffentliche Repos zusätzlich mit GitHub Secret Scanning / Gitleaks CI absichern.
