#Requires -Version 5.1
<#
.SYNOPSIS
  Prüft alle Git-Repos unter github_code auf Denylist-Treffer (HEAD/worktree).

.DESCRIPTION
  Nutzt git-hooks/denylist.txt (lokal, gitignored) und allowlist.txt.
  Entspricht der Hook-Logik: Allowlist-Zeilen gelten als OK.
  Optional: nur geänderte Dateien (--Staged / --Diff).

.EXAMPLE
  .\tools\scan-repos.ps1
  .\tools\scan-repos.ps1 -Root "C:\Users\me\github_code" -Verbose
#>
param(
    [string]$Root = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
    [switch]$Staged,
    [switch]$Diff,
    [switch]$Verbose
)

$HooksDir = Join-Path (Split-Path $PSScriptRoot -Parent) "git-hooks"
$DenyFile = Join-Path $HooksDir "denylist.txt"
if (-not (Test-Path $DenyFile)) {
    $DenyFile = Join-Path $HooksDir "denylist.local.txt"
}
if (-not (Test-Path $DenyFile)) {
    Write-Error "Keine lokale Denylist: git-hooks/denylist.txt fehlt. cp denylist.example.txt denylist.txt"
    exit 2
}
$AllowFile = Join-Path $HooksDir "allowlist.txt"

function Read-Patterns([string]$Path) {
    if (-not (Test-Path $Path)) { return @() }
    Get-Content $Path | ForEach-Object {
        $line = ($_ -split '#', 2)[0].Trim()
        if ($line) { $line }
    }
}

$deny = Read-Patterns $DenyFile
$allow = Read-Patterns $AllowFile
if ($deny.Count -eq 0) {
    Write-Error "Denylist leer: $DenyFile"
    exit 2
}

function Test-LineAllowed([string]$Line) {
    foreach ($a in $allow) {
        if ($Line -like "*$a*") { return $true }
    }
    return $false
}

function Test-LineDenied([string]$Line) {
    if (Test-LineAllowed $Line) { return $null }
    foreach ($p in $deny) {
        if ($Line -like "*$p*") { return $p }
    }
    return $null
}

$skipDir = '(\\\.git\\|\\node_modules\\|\\\.venv\\|\\dist\\|\\build\\)'
$totalHits = 0
$reposScanned = 0

function Scan-OneRepo {
    param([string]$RepoPath, [string]$RepoName)
    $script:reposScanned++
    Push-Location $RepoPath
    try {
        if ($Staged) {
            $files = git diff --cached --name-only --diff-filter=ACM 2>$null
        } elseif ($Diff) {
            $files = git diff --name-only --diff-filter=ACM 2>$null
        } else {
            $files = git ls-files 2>$null
        }
        foreach ($rel in $files) {
            if ($rel -match $skipDir) { continue }
            if ($rel -match '(^|/)git-hooks/denylist') { continue }
            $full = Join-Path $RepoPath $rel
            if (-not (Test-Path $full -PathType Leaf)) { continue }
            try {
                $bytes = [System.IO.File]::ReadAllBytes($full)
                if ($bytes -contains 0) { continue }
                $text = [System.Text.Encoding]::UTF8.GetString($bytes)
            } catch { continue }
            $n = 0
            foreach ($line in ($text -split "`n")) {
                $n++
                $hit = Test-LineDenied $line
                if ($hit) {
                    Write-Host "${RepoName}:${rel}:${n}: «${hit}»" -ForegroundColor Red
                    if ($Verbose) { Write-Host "  $line" }
                    $script:totalHits++
                }
            }
        }
    } finally {
        Pop-Location
    }
}

if (Test-Path (Join-Path $Root ".git")) {
    Scan-OneRepo -RepoPath $Root -RepoName (Split-Path $Root -Leaf)
} else {
    Get-ChildItem -Path $Root -Directory | ForEach-Object {
        if ($_.Name -eq 'doku') { return }
        $gitDir = Join-Path $_.FullName ".git"
        if (-not (Test-Path $gitDir)) { return }
        Scan-OneRepo -RepoPath $_.FullName -RepoName $_.Name
    }
}

Write-Host ""
Write-Host "Repos: $reposScanned | Treffer: $totalHits | Denylist: $DenyFile"
if ($totalHits -gt 0) { exit 1 }
exit 0
