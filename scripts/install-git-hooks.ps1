#Requires -Version 5.1
<#
.SYNOPSIS
  Aktiviert zentrale Git-Hooks (PII/Secrets) für alle Repos unter github_code.

.DESCRIPTION
  Setzt pro Repo: git config core.hooksPath -> Safe-CLI-Helpers/git-hooks
  Einmal ausführen nach Clone/Update. Optional -Root anpassen.

.EXAMPLE
  .\install-git-hooks.ps1
  .\install-git-hooks.ps1 -Root "C:\Users\me\github_code"
#>
param(
    [string]$Root = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
)

$HooksDir = Join-Path (Split-Path $PSScriptRoot -Parent) "git-hooks"
$HooksDirUnix = ($HooksDir -replace '\\', '/')

if (-not (Test-Path (Join-Path $HooksDir "pre-commit"))) {
    Write-Error "Hooks nicht gefunden: $HooksDir"
    exit 1
}

if (-not (Test-Path (Join-Path $HooksDir "denylist.txt"))) {
    $example = Join-Path $HooksDir "denylist.example.txt"
    if (Test-Path $example) {
        Copy-Item $example (Join-Path $HooksDir "denylist.txt")
        Write-Host "  -> denylist.txt aus denylist.example.txt erstellt — bitte lokal anpassen." -ForegroundColor Yellow
    }
}

Write-Host "Hooks-Verzeichnis: $HooksDir"
Write-Host "Scanne Repos unter: $Root"
Write-Host ""

$installed = 0
$skipped = 0

Get-ChildItem -Path $Root -Directory | ForEach-Object {
    $gitDir = Join-Path $_.FullName ".git"
    if (-not (Test-Path $gitDir)) { return }

    $name = $_.Name
    Push-Location $_.FullName
    try {
        git config core.hooksPath $HooksDirUnix
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK  $name"
            $installed++
        } else {
            Write-Host "  FAIL $name" -ForegroundColor Red
            $skipped++
        }
    } finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "Fertig: $installed Repos mit Hooks, $skipped Fehler."
Write-Host ""
Write-Host "Optional: Gitleaks installieren für erweiterten Secret-Scan:"
Write-Host "  winget install Gitleaks.Gitleaks"
Write-Host ""
Write-Host "Einzelnes Repo:  python tools/gix.py protect install"
Write-Host "Deaktivieren:    python tools/gix.py protect uninstall"
