#Requires -Version 5.1
<#
.SYNOPSIS
  Prueft AGENTS.md und .cursor/rules auf echte Leaks (IPs, Domains) - nicht CT-Nummern oder doku-Pfade.

.DESCRIPTION
  Fuer oeffentliche GitHub-Repos. Blockiert keine Commits automatisch - manuell oder in CI nutzen.
  Ergaenzt Denylist-Hooks (lokale denylist.txt).

.EXAMPLE
  .\tools\scan-agents-public.ps1 -Repo paperless-ngx-classifier
  .\tools\scan-agents-public.ps1 -Root C:\...\github_code   # alle Repos
#>
param(
    [string]$Root = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
    [string]$Repo = ""
)

$Patterns = @(
    @{ Name = "RFC1918 192.168"; Regex = '192\.168\.\d' },
    @{ Name = "RFC1918 10.x";    Regex = '\b10\.\d{1,3}\.\d' },
    @{ Name = "private domain";  Regex = ('sant' + 'inel\.li') }
)

$TargetFiles = @('AGENTS.md')
$CursorGlob  = '.cursor/rules/*.mdc'

function Test-Repo([string]$RepoPath, [string]$RepoName) {
    $hits = @()
    $files = @()
    foreach ($f in $TargetFiles) {
        $p = Join-Path $RepoPath $f
        if (Test-Path $p) { $files += $p }
    }
    $cursorDir = Join-Path $RepoPath '.cursor/rules'
    if (Test-Path $cursorDir) {
        $files += Get-ChildItem -Path $cursorDir -Filter '*.mdc' -File | ForEach-Object { $_.FullName }
    }
    if ($files.Count -eq 0) { return $hits }

    foreach ($file in $files) {
        $rel = $file.Substring($RepoPath.Length).TrimStart('\', '/')
        $lineNum = 0
        foreach ($line in Get-Content -LiteralPath $file -Encoding UTF8) {
            $lineNum++
            foreach ($pat in $Patterns) {
                if ($line -match $pat.Regex) {
                    $hits += [PSCustomObject]@{
                        Repo    = $RepoName
                        File    = $rel
                        Line    = $lineNum
                        Rule    = $pat.Name
                        Content = $line.Trim()
                    }
                }
            }
        }
    }
    return $hits
}

$allHits = @()
if ($Repo) {
    $repoPath = Join-Path $Root $Repo
    if (-not (Test-Path (Join-Path $repoPath '.git'))) {
        Write-Error "Kein Git-Repo: $repoPath"
        exit 2
    }
    $allHits += Test-Repo $repoPath $Repo
} else {
    Get-ChildItem -Path $Root -Directory | ForEach-Object {
        if (-not (Test-Path (Join-Path $_.FullName '.git'))) { return }
        $allHits += Test-Repo $_.FullName $_.Name
    }
}

if ($allHits.Count -eq 0) {
    Write-Host "OK - keine typischen Private-Daten in AGENTS.md / .cursor/rules gefunden."
    exit 0
}

Write-Host "TREFFER ($($allHits.Count)) - vor Push in oeffentliches Repo pruefen:" -ForegroundColor Yellow
$allHits | Format-Table -AutoSize Repo, File, Line, Rule -Wrap
Write-Host ""
Write-Host "Policy: doku/ops/AGENTS-public-repos-policy.md" -ForegroundColor Cyan
exit 1
