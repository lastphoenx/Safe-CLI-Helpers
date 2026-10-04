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

## Denylist (lokal, nicht im Repo)

Persönliche Muster stehen in **`git-hooks/denylist.txt`** — diese Datei ist **gitignored** und wird nicht gepusht.

```powershell
cd Safe-CLI-Helpers\git-hooks
copy denylist.example.txt denylist.txt
# denylist.txt lokal bearbeiten
```

Im Repo liegt nur `denylist.example.txt` (Platzhalter-Format, ohne echte Namen).

## Allowlist (öffentlich)

Nur **generische** Platzhalter in `allowlist.txt`, z. B. `example.com`, `PersonA`, `Max Muster`.
Zusätzlich: **öffentliche Freemail-/Provider-Domains** (`gmx.net`, `gmail.com`, …) für Code-Listen
(Scam-Erkennung, Tranco Shared Infrastructure) — keine persönlichen Adressen whitelisten.
Persönliches nie whitelisten — im Quelltext ersetzen.

## Ausnahme: privates `doku`-Repo

Nur wenn im **Git-Root** die Datei **`.private-homelab-doku-repo`** existiert (privates Homelab-Doku-Repo
unter `github_code/doku/`): **Denylist-PII wird nicht geprüft** (Namen, E-Mails, interne Host-Strings).

**Nicht** betroffen: Unterordner `doku/` oder `Doku/` in anderen Repos — deren Git-Root hat keinen Marker.

**Secrets, Private Keys und riskante Dateinamen** (.env, Keys) bleiben aktiv — auch im Homelab-`doku`-Repo.

Persönliche Denylist/Allowlist-Muster und Homelab-PII-Referenzen: nur im privaten `doku`-Repo
(siehe `doku/ops/safe-cli-homelab-hooks.md`), **nicht** in Safe-CLI-Helpers (öffentlich).

## Was blockiert wird

| Kategorie | Beispiele |
|-----------|-----------|
| **Dateinamen** | `.env`, `.pem`, `.key`, `state/`, `credentials`, `secrets.json` |
| **PII (denylist.txt, lokal)** | private Domains, Namen, interne Host-Strings |
| **Secrets im Text** | Klartext-Zuweisungen (Passwort, API-Key, Private Keys) |
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
