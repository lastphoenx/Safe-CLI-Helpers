#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gitx.py – sicheres Git-CLI für Alltag (Branches, Push/Pull, Release, Schutz-Hooks)
- click-basierte Unterkommandos
- Bestätigungen vor "gefährlichen" Aktionen (push/merge/reset)
- Anzeige von Fetch- & Push-URLs (Deploy-Key vs. User-Key)
- Feature-/Release-Workflow
- Pre-commit-Hook gegen .env/Secrets

Beispiele:
  python gitx.py info
  python gitx.py add -A -m "feat: xyz"
  python gitx.py feature start av-scan-interval
  python gitx.py feature publish
  python gitx.py feature merge --to main
  python gitx.py release cut --tag v0.2.0
  python gitx.py pull
  python gitx.py push
  python gitx.py protect install
"""

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

import click

# ------------------------- examples ----------------------
EXAMPLES_GITX = r"""
Beispiele (sicherer Flow mit Feature/Main/Release):

# Überblick
python gitx.py info
python gitx.py remote show

# Remotes (Fetch=Deploy-Key, Push=User-Key)
python gitx.py remote set --fetch git@github-entropy:USER/REPO.git --push git@github-user:USER/REPO.git
python gitx.py remote show

# Änderungen committen
python gitx.py add -A -m "feat: intervall konfigurierbar"
python gitx.py add -p -m "fix: randfall"

# Feature-Branch
python gitx.py feature start av-scan-interval        # von main abzweigen
# ... arbeiten ...
python gitx.py feature publish                        # Branch ins Remote

# Integration in main
python gitx.py feature merge --to main                # Merge-Commit, pusht

# Release/Prod aktualisieren
python gitx.py release cut                            # main -> release
python gitx.py release cut --tag v0.2.0               # + Tag setzen

# Sync
python gitx.py pull                                   # ff-only
python gitx.py push                                   # zeigt Push-URL & ahead/behind
python gitx.py push --set-upstream                    # beim ersten Push

# Schutz
python gitx.py protect install                        # Secret-Precommit-Hook
"""

def _print_examples_and_exit_gitx():
    print(EXAMPLES_GITX.strip())
    raise SystemExit(0)



# --------------------------- helpers ---------------------------

def run(cmd: List[str], repo: Path, check=True, capture=True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(repo), check=check,
        text=True, capture_output=capture
    )

def sh(cmd: str, repo: Path) -> str:
    """run shell-like one-liner (space-splitting) and return stdout"""
    out = run(cmd.split(), repo).stdout.strip()
    return out

def ensure_repo(repo: Path):
    try:
        root = sh("git rev-parse --show-toplevel", repo)
    except subprocess.CalledProcessError:
        click.echo(click.style(f"✖ Kein Git-Repo unter {repo}", fg="red"))
        sys.exit(2)
    return Path(root)

def current_branch(repo: Path) -> str:
    try:
        return sh("git rev-parse --abbrev-ref HEAD", repo)
    except subprocess.CalledProcessError:
        return "(detached)"

def remotes(repo: Path):
    out = sh("git remote -v", repo)
    fetch = push = None
    for line in out.splitlines():
        name, url, kind = line.split()
        if name == "origin" and kind == "(fetch)":
            fetch = url
        if name == "origin" and kind == "(push)":
            push = url
    return fetch, push

def ahead_behind(repo: Path):
    try:
        sh("git fetch --quiet", repo)
        branch = current_branch(repo)
        ahead = sh(f"git rev-list --left-right --count origin/{branch}...{branch}", repo)
        left, right = ahead.split()
        # left: wie viele Commits hat origin/<branch> voraus (wir hinterher)
        # right: wie viele Commits sind lokal voraus
        return int(left), int(right)
    except Exception:
        return None, None

def confirm_or_exit(msg: str, assume_yes: bool):
    if assume_yes:
        return
    if not click.confirm(click.style(msg, fg="yellow"), default=False):
        click.echo("Abgebrochen.")
        sys.exit(1)

def show_status(repo: Path):
    root = ensure_repo(repo)
    br = current_branch(repo)
    fetch, push = remotes(repo)
    left, right = ahead_behind(repo)
    click.echo(click.style(f"Repo: {root}", bold=True))
    click.echo(f"Branch: {br}")
    click.echo(f"Remote (fetch): {fetch or '-'}")
    click.echo(f"Remote (push):  {push or '-'}")
    if left is not None:
        click.echo(f"Ahead/Behind vs origin/{br}: +{right} / -{left}")
    unstaged = run(["git","status","--short"], repo, capture=True).stdout
    if unstaged.strip():
        click.echo("\nÄnderungen:")
        click.echo(unstaged)
    else:
        click.echo("\nKeine lokalen Änderungen.")

# --------------------------- CLI root ---------------------------
@click.group(
    context_settings=dict(help_option_names=["-h", "--help"]),
    invoke_without_command=True,  # <— erlaubt Aufruf ohne Subcommand
)
@click.option(
    "--examples",
    is_flag=True,
    help="Beispielaufrufe anzeigen und beenden."
)
@click.option(
    "--repo",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Pfad zum Git-Repo (Default: aktuelles Verzeichnis)."
)
@click.option(
    "-y", "--yes",
    is_flag=True,
    help="Nicht nachfragen (auto-yes)."
)
@click.pass_context
def cli(ctx, examples, repo: Path, yes: bool):
    """
    Sicheres Git-CLI für deinen täglichen Flow (Branches, Push/Pull, Release).
    """
    # Wenn nur --examples übergeben wurde: direkt Beispiele zeigen und sauber beenden
    if examples and (ctx.invoked_subcommand is None):
        _print_examples_and_exit_gitx()

    # Ab hier: normaler Setup-Pfad (wenn ein Subcommand kommt)
    root = ensure_repo(repo)  # wirft klare Fehlermeldung, falls kein Git-Repo
    ctx.ensure_object(dict)
    ctx.obj["repo"] = root
    ctx.obj["yes"] = yes

    # Falls jemand *ohne* Subcommand und *ohne* --examples aufruft:
    if ctx.invoked_subcommand is None:
        # Statt „Missing command“: Hilfe zeigen und normal beenden
        click.echo(ctx.get_help())
        raise SystemExit(0)

# --------------------------- info / status ---------------------------

@cli.command()
@click.pass_context
def info(ctx):
    """Zeigt Repo-Root, Branch, Remotes und Status."""
    show_status(ctx.obj["repo"])

# --------------------------- add & commit ---------------------------

@cli.command()
@click.option("-A", "--all", "all_", is_flag=True, help="Alle neuen/geänderten Dateien stagen.")
@click.option("-p", "--patch", is_flag=True, help="Interaktives Staging (git add -p).")
@click.option("-m", "--message", required=True, help="Commit-Message.")
@click.pass_context
def add(ctx, all_, patch, message):
    """Dateien stagen & committen (inkl. Interaktivmodus)."""
    repo: Path = ctx.obj["repo"]
    if patch:
        subprocess.run(["git","add","-p"], cwd=repo)
    if all_:
        run(["git","add","-A"], repo)
    # wenn weder -p noch -A, dann nur commit (falls schon gestaged)
    run(["git","commit","-m",message], repo, check=True, capture=False)
    click.echo(click.style("✓ Commit erstellt.", fg="green"))

# --------------------------- pull / push ---------------------------

@cli.command()
@click.option("--ff-only/--no-ff-only", default=True, help="Nur Fast-Forward zulassen (Default).")
@click.pass_context
def pull(ctx, ff_only):
    """Sicheres Pull für den aktuellen Branch (zeigt vorher Remote-URL)."""
    repo: Path = ctx.obj["repo"]
    br = current_branch(repo)
    fetch, _ = remotes(repo)
    click.echo(f"Ziehe von {fetch or 'origin'} auf Branch {br} …")
    cmd = ["git","pull"]
    if ff_only:
        cmd.append("--ff-only")
    run(cmd, repo, check=True, capture=False)
    click.echo(click.style("✓ Pull ok.", fg="green"))

@cli.command()
@click.option("--set-upstream", is_flag=True, help="Upstream für aktuellen Branch setzen (git push -u).")
@click.pass_context
def push(ctx, set_upstream):
    """Push für den aktuellen Branch (zeigt vorher Push-URL und Ahead/Behind)."""
    repo: Path = ctx.obj["repo"]
    yes: bool = ctx.obj["yes"]
    br = current_branch(repo)
    _, push_url = remotes(repo)
    left, right = ahead_behind(repo)
    click.echo(f"Push-URL: {push_url}")
    click.echo(f"Branch: {br}  (lokal voraus: {right or 0}, remote voraus: {left or 0})")
    confirm_or_exit(f"Wirklich pushen nach {push_url} auf {br}?", yes)
    cmd = ["git","push"]
    if set_upstream:
        cmd.extend(["-u","origin", br])
    run(cmd, repo, check=True, capture=False)
    click.echo(click.style("✓ Push ok.", fg="green"))

# --------------------------- feature workflow ---------------------------

@cli.group()
def feature():
    """Feature-Branches: start/publish/merge."""
    pass

@feature.command("start")
@click.argument("name")
@click.option("--from-branch", default="main", help="Aus welchem Branch starten (Default: main).")
@click.pass_context
def feature_start(ctx, name, from_branch):
    """Neuen Feature-Branch erstellen & wechseln."""
    repo: Path = ctx.obj["repo"]
    run(["git","switch", from_branch], repo, capture=False)
    run(["git","pull","--ff-only"], repo, capture=False)
    run(["git","switch","-c", f"feature/{name}"], repo, capture=False)
    click.echo(click.style(f"✓ Neuer Branch feature/{name}", fg="green"))

@feature.command("publish")
@click.pass_context
def feature_publish(ctx):
    """Aktuellen Feature-Branch zum Remote pushen (mit Upstream)."""
    repo: Path = ctx.obj["repo"]
    br = current_branch(repo)
    if not br.startswith("feature/"):
        click.echo(click.style("✖ Nicht auf einem feature/*-Branch.", fg="red")); sys.exit(2)
    run(["git","push","-u","origin", br], repo, capture=False)
    click.echo(click.style(f"✓ Branch {br} veröffentlicht.", fg="green"))

@feature.command("merge")
@click.option("--to", "target", default="main", help="Ziel-Branch (Default: main).")
@click.option("--no-ff", is_flag=True, default=True, help="Merge-Commit erzwingen (Default).")
@click.pass_context
def feature_merge(ctx, target, no_ff):
    """Aktuellen Feature-Branch in Ziel-Branch integrieren."""
    repo: Path = ctx.obj["repo"]
    yes: bool = ctx.obj["yes"]
    br = current_branch(repo)
    if not br.startswith("feature/"):
        click.echo(click.style("✖ Nicht auf einem feature/*-Branch.", fg="red")); sys.exit(2)
    run(["git","fetch"], repo)
    run(["git","switch", target], repo, capture=False)
    run(["git","pull","--ff-only"], repo, capture=False)
    confirm_or_exit(f"{br} in {target} mergen?", yes)
    cmd = ["git","merge"]
    if no_ff:
        cmd.append("--no-ff")
    cmd.append(br)
    run(cmd, repo, capture=False)
    run(["git","push"], repo, capture=False)
    click.echo(click.style(f"✓ {br} → {target} gemerged & gepusht.", fg="green"))

# --------------------------- release workflow ---------------------------

@cli.group()
def release():
    """Release-/Prod-Workflow."""
    pass

@release.command("cut")
@click.option("--from-branch", default="main", help="Quelle (Default: main).")
@click.option("--to-branch", default="release", help="Ziel/Prod-Branch (Default: release).")
@click.option("--tag", help="Optionaler Tag (z. B. v0.2.0) nach Merge.")
@click.pass_context
def release_cut(ctx, from_branch, to_branch, tag):
    """Änderungen aus main in release übernehmen + optional taggen."""
    repo: Path = ctx.obj["repo"]
    yes: bool = ctx.obj["yes"]
    run(["git","fetch"], repo)
    run(["git","switch", to_branch], repo, capture=False)
    run(["git","pull","--ff-only"], repo, capture=False)
    confirm_or_exit(f"{from_branch} → {to_branch} mergen?", yes)
    run(["git","merge","--no-ff", from_branch], repo, capture=False)
    run(["git","push"], repo, capture=False)
    if tag:
        confirm_or_exit(f"Tag {tag} auf aktuellen Commit setzen & pushen?", yes)
        run(["git","tag","-a", tag, "-m", f"{tag}"], repo, capture=False)
        run(["git","push","--tags"], repo, capture=False)
    click.echo(click.style(f"✓ Release aktualisiert ({from_branch} → {to_branch})", fg="green"))

# --------------------------- remotes einstellen ---------------------------

@cli.group()
def remote():
    """Fetch-/Push-URLs konfigurieren (Deploy-Key vs User-Key)."""
    pass

@remote.command("show")
@click.pass_context
def remote_show(ctx):
    """Zeigt origin-Fetch & origin-Push URL."""
    repo: Path = ctx.obj["repo"]
    show_status(repo)

@remote.command("set")
@click.option("--fetch", "fetch_url", required=True, help="z. B. git@github-entropy:user/repo.git")
@click.option("--push",  "push_url",  required=True, help="z. B. git@github-user:user/repo.git")
@click.pass_context
def remote_set(ctx, fetch_url, push_url):
    """Setzt getrennte URLs für fetch (ro) und push (rw)."""
    repo: Path = ctx.obj["repo"]
    yes: bool = ctx.obj["yes"]
    click.echo(f"Fetch: {fetch_url}\nPush:  {push_url}")
    confirm_or_exit("Übernehmen?", yes)
    run(["git","remote","set-url","origin", fetch_url], repo)
    run(["git","remote","set-url","--push","origin", push_url], repo)
    click.echo(click.style("✓ Remotes gesetzt.", fg="green"))

# --------------------------- pre-commit hook ---------------------------

@cli.group()
def protect():
    """Schutz-Hooks: verhindern, dass .env/Keys committed werden."""
    pass

HOOK_CONTENT = """#!/usr/bin/env bash
set -e
names="$(git diff --cached --name-only)"
if echo "$names" | grep -E '\\.env($|\\.|/)|(^|/)state/|\\.pem$|\\.key$' >/dev/null; then
  echo 'ABBRUCH: .env/state/Keys dürfen nicht committed werden.' >&2
  exit 1
fi
"""

@protect.command("install")
@click.pass_context
def protect_install(ctx):
    """Installiert einen pre-commit Hook gegen Secrets."""
    repo: Path = ctx.obj["repo"]
    hooks = repo / ".git" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    path = hooks / "pre-commit"
    path.write_text(HOOK_CONTENT)
    os.chmod(path, 0o755)
    click.echo(click.style(f"✓ Hook installiert: {path}", fg="green"))

@protect.command("uninstall")
@click.pass_context
def protect_uninstall(ctx):
    """Entfernt den pre-commit Hook."""
    repo: Path = ctx.obj["repo"]
    path = repo / ".git" / "hooks" / "pre-commit"
    if path.exists():
        path.unlink()
        click.echo(click.style("✓ Hook entfernt.", fg="green"))
    else:
        click.echo("Kein Hook vorhanden.")

# --------------------------- examples ---------------------------

@cli.command("examples")
def examples_gitx():
    """Beispiele & Kochbuch anzeigen und beenden."""
    _print_examples_and_exit_gitx()


# --------------------------- entry ---------------------------

if __name__ == "__main__":
    cli()

