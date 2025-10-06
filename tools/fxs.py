#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deb_commands.py – sicheres Datei-/Ordner-Tool (Debian/Unix)

⚙️ Grundprinzip
- Standardmäßig ist **DRY-RUN aktiv** (es passiert nichts Reales).
- Wirklich ausführen nur mit **-x / --execute**.
- Rückfragen überspringen mit **-y / --yes**.
- Pro Aktion bestätigen (zusätzliche Bremse) mit **-i / --interactive**.
- Konflikte am Ziel werden gebremst: ohne `--force`/`--backup` wird NICHT überschrieben.

📦 Befehle
  ls       – Auflisten (mit -l Details, -a versteckte, -R rekursiv)
  cp       – Kopieren (Mehrfachquellen → Ziel muss Ordner sein)
  mv       – Verschieben (dito)
  rm       – Löschen (Datei/Ordner/leer/rekursiv/Trash)
  mkdir    – Ordner anlegen (-p wie mkdir -p)
  chmod    – Rechte setzen (oktal: 0755, 0644, …)
  chown    – Besitzer/Gruppe setzen (root nötig)
  ln       – Symlink erstellen (LINKPATH -> TARGET)

🧪 Beispiele
  deb_commands.py ls /opt -l -a
  deb_commands.py cp -n src.txt /tmp/ziel.txt          # nur anzeigen (Default)
  deb_commands.py cp -x -y src.txt /tmp/ziel.txt       # wirklich kopieren, ohne Rückfragen
  deb_commands.py mv -x -i data/ /srv/data             # echt, mit Bestätigung pro Aktion
  deb_commands.py mv -x --backup foo.txt bar.txt dir/  # Konflikt? erst Backup *.bak.<ts>
  deb_commands.py rm -x --recursive cache/             # Ordner rekursiv löschen
  deb_commands.py rm -x --trash *.log                  # in den Benutzer-Trash verschieben
  deb_commands.py ln -x -f /opt/app/current /opt/app/releases/2025-10-06
"""

import os
import pwd, grp
import shutil
import stat as pystat
import sys
import time
from pathlib import Path
from typing import Iterable, List

import click

# ------------------------- examples ----------------------
EXAMPLES_FSX = r"""
. 
. 

#Tolle Mögichkeit:
alias fsx='/usr/bin/python /opt/meine_tools/deb_commands.py'
alias fsx!='/usr/bin/python /opt/meine_tools/deb_commands.py --execute'
# Nutzung:
fsx mv SRC DST          # trocken
fsx! mv SRC DST -y      # scharf + ohne Rückfragen


#Wirkung:

- Default (ohne Flags): nur [DRY]-Ausgabe.
- Mit -x: echte Ausführung, aber ohne Extra-Rückfrage (wie jetzt), außer bei Konflikten.
- Mit -x -i: echte Ausführung mit Extra-Rückfrage bei jeder Aktion.
- Mit -x -i -y: echte Ausführung, keine Rückfragen (du weißt genau, was du tust).


Beispiele (DRY-RUN ist Standard; echte Ausführung nur mit -x/--execute):

# Auflisten
deb_commands.py ls                          # aktuelles Verzeichnis, basic
deb_commands.py ls /opt -l -a               # Details + versteckte
deb_commands.py ls /var/log -l -R           # rekursiv

# Kopieren
deb_commands.py cp src.txt /tmp/ziel.txt            # nur anzeigen (DRY)
deb_commands.py cp -x src.txt /tmp/ziel.txt         # wirklich kopieren
deb_commands.py cp -x -y --force src.txt /tmp/ziel.txt
deb_commands.py cp -x --backup foo.txt bar.txt dir/ # Konflikte sichern

# Verschieben
deb_commands.py mv /tmp/a.txt /srv/data/            # DRY
deb_commands.py mv -x -i /tmp/a.txt /srv/data/      # echt, mit Nachfrage pro Aktion
deb_commands.py mv -x -y --force data/ /srv/data    # Ordner ersetzen

# Löschen
deb_commands.py rm *.log                            # DRY
deb_commands.py rm -x -i --file-only *.log         # echte Löschung, jede Datei bestätigen
deb_commands.py rm -x --recursive cache/            # Ordner rekursiv löschen
deb_commands.py rm -x --trash *.log                 # in Trash verschieben

# Ordner & Rechte
deb_commands.py mkdir foo bar/baz               # DRY
deb_commands.py mkdir -x -p /opt/app/{data,logs}
deb_commands.py chmod -x 0755 script.sh         # Rechte setzen
deb_commands.py chown -x -u www-data -g www-data /var/www/html

# Symlink
deb_commands.py ln -x -f /opt/app/current /opt/app/releases/2025-10-06

############################ weitere Beispiele #########################

# 1) Standard: sicherer Probelauf (DRY)
deb_commands.py mv /opt/meine_tools/test.py /opt/entropywatcher/

# 2) ECHT verschieben, mit Rückfragen bei Konflikt
deb_commands.py mv -x /opt/meine_tools/test.py /opt/entropywatcher/

# 3) ECHT verschieben, pro Aktion bestätigen
deb_commands.py mv -x -i /opt/meine_tools/test.py /opt/entropywatcher/

# 4) ECHT verschieben, ohne irgendeine Nachfrage (bewusst!)
deb_commands.py mv -x -y /opt/meine_tools/test.py /opt/entropywatcher/

# 5) Konflikt: existierendes Ziel sichern statt überschreiben (DRY)
deb_commands.py mv -n --backup /opt/meine_tools/test.py /opt/entropywatcher/

# 6) Wirklich kopieren & existierendes Ziel ersetzen (Force), ohne Nachfragen
deb_commands.py cp -x -y --force src.txt dest.txt



"""

def _print_examples_and_exit_fsx():
    print(EXAMPLES_FSX.strip())
    raise SystemExit(0)





# --------------------------- Hilfsfunktionen ---------------------------

def human_size(n: int) -> str:
    for unit in ("B","K","M","G","T","P"):
        if n < 1024 or unit == "P":
            return f"{n:.0f}{unit}"
        n /= 1024

def list_paths(patterns: Iterable[str]) -> List[Path]:
    """Erweitert Wildcards, normalisiert Pfade, dedupliziert Reihenfolge-beibehaltend."""
    out, seen = [], set()
    for p in patterns:
        P = Path(p).expanduser()
        items = [x for x in P.parent.glob(P.name)] if any(c in p for c in "*?[]") else [P]
        for it in items:
            if it not in seen:
                seen.add(it)
                out.append(it)
    return out

def confirm(msg: str, yes: bool) -> bool:
    return True if yes else click.confirm(click.style(msg, fg="yellow"), default=False)

def backup_path(p: Path) -> Path:
    return p.with_name(p.name + f".bak.{time.strftime('%Y%m%d-%H%M%S')}")

def do(action: str, func, *args, **kwargs):
    """Führt eine Aktion aus – oder zeigt sie im DRY-RUN nur an."""
    ctx = click.get_current_context()
    dry = ctx.obj.get("dry", True)
    if dry:
        click.echo(click.style(f"[DRY] {action}", fg="blue"))
    else:
        func(*args, **kwargs)
        click.echo(click.style(f"✓ {action}", fg="green"))

def conflict_handle(dst: Path, *, force: bool, backup: bool, yes: bool):
    """
    Zielkonflikte behandeln – respektiert DRY-RUN.
    - --backup: verschiebt das existierende Ziel zu *.bak.<ts>
    - --force:  entfernt das existierende Ziel
    - sonst:    bricht ab
    """
    ctx = click.get_current_context()
    dry = ctx.obj.get("dry", True)
    if not (dst.exists() or dst.is_symlink()):
        return
    if backup:
        bk = backup_path(dst)
        if not confirm(f"Konflikt: {dst} existiert. Backup -> {bk}?", yes):
            raise click.ClickException("Abgebrochen (Backup).")
        if dry:
            click.echo(click.style(f"[DRY] mv {dst} -> {bk}", fg="blue"))
        else:
            shutil.move(str(dst), str(bk))
    elif force:
        if not confirm(f"Konflikt: {dst} existiert. Überschreiben?", yes):
            raise click.ClickException("Abgebrochen (force).")
        if dry:
            if dst.is_dir() and not dst.is_symlink():
                click.echo(click.style(f"[DRY] rm -r {dst}", fg="blue"))
            else:
                click.echo(click.style(f"[DRY] rm {dst}", fg="blue"))
        else:
            if dst.is_dir() and not dst.is_symlink():
                shutil.rmtree(dst)
            else:
                dst.unlink(missing_ok=True)
    else:
        raise click.ClickException(f"Ziel existiert bereits: {dst} (nutze --force oder --backup).")

def confirm_each(action_desc: str, yes: bool):
    """Zusatzbremse: pro Aktion bestätigen, falls --interactive und Execute."""
    ctx = click.get_current_context()
    dry  = ctx.obj.get("dry", True)
    inter = ctx.obj.get("interactive", False)
    if dry or not inter:
        return
    if not confirm(action_desc, yes):
        raise click.ClickException("Abgebrochen.")

def echo_mode():
    """Aktuellen Modus (DRY-RUN/EXECUTE) ausgeben."""
    ctx = click.get_current_context()
    dry = ctx.obj.get("dry", True)
    txt = "DRY-RUN" if dry else "EXECUTE"
    color = "blue" if dry else "red"
    click.echo(click.style(f"[MODE] {txt}", fg=color, bold=True))

# --------------------------- Globale CLI-Optionen ---------------------------

def common_exec_options(f):
    """Einheitliche Flags für Subcommands: -n/-x/-y/-i (per Namen gebunden)."""
    f = click.option("-i","--interactive", is_flag=True,
                     help="Bei JEDER Operation bestätigen (nur im Execute-Modus).")(f)
    f = click.option("-y","--yes", is_flag=True,
                     help="Rückfragen automatisch mit JA beantworten.")(f)
    f = click.option("-x","--execute", is_flag=True,
                     help="Wirklich ausführen. (Ohne dieses Flag: DRY-RUN)")(f)
    f = click.option("-n","--dry-run", is_flag=True,
                     help="Nur anzeigen, nichts ändern. (Default)")(f)
    return f

@click.group(
    context_settings=dict(help_option_names=["-h","--help"]),
    invoke_without_command=True,
)
@click.option("--examples", is_flag=True, help="Beispielaufrufe anzeigen und beenden.")
@click.option("--execute/--dry-run", default=False, help="Global: ausführen oder nur anzeigen (Default: DRY-RUN).")
@click.pass_context
def cli(ctx, examples, execute):
    """
    Sicheres Datei-/Ordner-Tool. Default = DRY-RUN.
    Scharf schalten mit -x/--execute. Rückfragen mit -y überspringen.
    Zusatzbremse mit -i/--interactive.
    """

    # Beispiele anzeigen & beenden
    if examples and (ctx.invoked_subcommand is None):
        _print_examples_and_exit_fsx()

    # Kontext vorbereiten
    ctx.ensure_object(dict)
    ctx.obj["dry"] = not execute
    ctx.obj.setdefault("interactive", False)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        raise SystemExit(0)


def resolve_mode(local_execute: bool, local_dry: bool, interactive: bool):
    """Subcommand-Flags (-x/-n/-i) überschreiben globale Voreinstellung."""
    ctx = click.get_current_context()
    mode = ctx.obj.get("dry", True)
    if local_execute:
        mode = False
    if local_dry:
        mode = True
    ctx.obj["dry"] = mode
    ctx.obj["interactive"] = interactive

# --------------------------- ls ---------------------------

@cli.command()
@click.argument("paths", nargs=-1)
@click.option("-a","--all", is_flag=True, help="Versteckte Dateien anzeigen.")
@click.option("-l","--long", "long_", is_flag=True, help="Details (Rechte, Besitzer, Größe, Zeit).")
@click.option("-R","--recursive", is_flag=True, help="Rekursiv listen.")
def ls(paths, all, long_, recursive):
    """Dateien/Ordner auflisten (nur lesend)."""
    def show(p: Path):
        if not p.exists() and not p.is_symlink():
            click.echo(click.style(f"✖ nicht gefunden: {p}", fg="red"))
            return
        if p.is_dir() and not p.is_symlink():
            click.echo(click.style(f"{p}:", bold=True))
            entries = sorted(p.iterdir(), key=lambda x: x.name.lower())
            for e in entries:
                if not all and e.name.startswith("."):
                    continue
                print_entry(e, long_)
            if recursive:
                for e in entries:
                    if e.is_dir() and not e.is_symlink():
                        show(e)
        else:
            print_entry(p, long_)

    def print_entry(e: Path, long_: bool):
        if not long_:
            click.echo(e.name)
            return
        try:
            st = e.lstat()
            mode = pystat.filemode(st.st_mode)
            user = pwd.getpwuid(st.st_uid).pw_name
            group = grp.getgrgid(st.st_gid).gr_name
            size = human_size(st.st_size)
            mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
            name = e.name + (f" -> {os.readlink(e)}" if e.is_symlink() else "")
            click.echo(f"{mode} {user}:{group:8s} {size:>6s} {mtime}  {name}")
        except FileNotFoundError:
            click.echo(f"???????? {e.name} (dangling symlink?)")

    if not paths:
        paths = ("",)
    for p in paths:
        show(Path(p) if p else Path.cwd())

# --------------------------- mkdir ---------------------------

@cli.command()
@common_exec_options
@click.argument("dirs", nargs=-1, required=True)
@click.option("-p", is_flag=True, help="Elternpfade mit anlegen (wie mkdir -p).")
def mkdir(dry_run, execute, yes, interactive, dirs, p):
    """Ordner erstellen. Default: DRY-RUN. Echt mit -x/--execute."""
    resolve_mode(execute, dry_run, interactive)
    echo_mode()
    for d in dirs:
        path = Path(d).expanduser()
        if path.exists():
            raise click.ClickException(f"Existiert bereits: {path}")
        confirm_each(f"Ordner anlegen: {path} ?", yes)
        do(f"mkdir {path}", path.mkdir, parents=p, exist_ok=False)

# --------------------------- cp ---------------------------

@cli.command(name="cp")
@common_exec_options
@click.option("--force", is_flag=True, help="Existierendes Ziel überschreiben.")
@click.option("--backup", is_flag=True, help="Bei Konflikt altes Ziel nach *.bak.<ts> verschieben.")
@click.argument("sources", nargs=-1, required=True)
@click.argument("target", required=True)
def cp_cmd(dry_run, execute, yes, interactive, force, backup, sources, target):
    """Kopieren. Mehrere Quellen → Ziel muss Ordner sein. Default: DRY-RUN."""
    resolve_mode(execute, dry_run, interactive)
    echo_mode()
    srcs = list_paths(sources)
    if not srcs:
        raise click.ClickException("Keine Quelle gefunden.")
    dst = Path(target).expanduser()
    multi = len(srcs) > 1 or (dst.exists() and dst.is_dir())
    if multi and not dst.exists():
        raise click.ClickException("Mehrere Quellen → Zielordner muss existieren.")
    for s in srcs:
        if not s.exists():
            click.echo(click.style(f"✖ Quelle fehlt: {s}", fg="red"))
            continue
        d = (dst / s.name) if multi else dst
        if d.exists() or d.is_symlink():
            conflict_handle(d, force=force, backup=backup, yes=yes)
        if s.is_dir() and not s.is_symlink():
            confirm_each(f"Ordner kopieren: {s} → {d} ?", yes)
            do(f"cp -a {s} -> {d}", shutil.copytree, s, d)
        else:
            if not d.parent.exists():
                raise click.ClickException(f"Zielordner existiert nicht: {d.parent}")
            confirm_each(f"Datei kopieren: {s} → {d} ?", yes)
            do(f"cp {s} -> {d}", shutil.copy2, s, d)

# --------------------------- mv ---------------------------

@cli.command(name="mv")
@common_exec_options
@click.option("--force", is_flag=True, help="Existierendes Ziel überschreiben.")
@click.option("--backup", is_flag=True, help="Bei Konflikt altes Ziel nach *.bak.<ts> verschieben.")
@click.argument("sources", nargs=-1, required=True)
@click.argument("target", required=True)
def mv_cmd(dry_run, execute, yes, interactive, force, backup, sources, target):
    """Verschieben. Mehrere Quellen → Ziel muss Ordner sein. Default: DRY-RUN."""
    resolve_mode(execute, dry_run, interactive)
    echo_mode()
    srcs = list_paths(sources)
    if not srcs:
        raise click.ClickException("Keine Quelle gefunden.")
    dst = Path(target).expanduser()
    multi = len(srcs) > 1 or (dst.exists() and dst.is_dir())
    if multi and not dst.exists():
        raise click.ClickException("Mehrere Quellen → Zielordner muss existieren.")
    for s in srcs:
        if not s.exists():
            click.echo(click.style(f"✖ Quelle fehlt: {s}", fg="red"))
            continue
        d = (dst / s.name) if multi else dst
        if d.exists() or d.is_symlink():
            conflict_handle(d, force=force, backup=backup, yes=yes)
        if not d.parent.exists():
            raise click.ClickException(f"Zielordner existiert nicht: {d.parent}")
        confirm_each(f"Verschieben: {s} → {d} ?", yes)
        do(f"mv {s} -> {d}", shutil.move, str(s), str(d))

# --------------------------- rm ---------------------------

@cli.command(name="rm")
@common_exec_options
@click.argument("paths", nargs=-1, required=True)
@click.option("--file-only", is_flag=True, help="Nur Dateien löschen (Ordner überspringen).")
@click.option("--dir-only", is_flag=True, help="Nur Ordner löschen (keine Dateien).")
@click.option("--empty-only", is_flag=True, help="Ordner nur löschen, wenn leer.")
@click.option("--recursive", "-r", is_flag=True, help="Ordner rekursiv löschen.")
@click.option("--trash", is_flag=True, help="Statt löschen in ~/.local/share/Trash/files verschieben.")
def rm_cmd(dry_run, execute, yes, interactive, paths, file_only, dir_only, empty_only, recursive, trash):
    """Löschen (sicher). Default: DRY-RUN. Echt mit -x/--execute."""
    resolve_mode(execute, dry_run, interactive)
    echo_mode()
    if file_only and dir_only:
        raise click.ClickException("--file-only und --dir-only schließen sich aus.")
    items = list_paths(paths)
    if not items:
        raise click.ClickException("Keine Zielpfade gefunden.")
    if not confirm(f"{len(items)} Einträge löschen?", yes):
        raise click.ClickException("Abgebrochen.")

    trash_dir = Path.home() / ".local/share/Trash/files"
    if trash and not trash_dir.exists():
        trash_dir.mkdir(parents=True, exist_ok=True)

    for p in items:
        if not p.exists() and not p.is_symlink():
            click.echo(click.style(f"⊝ fehlt: {p}", fg="yellow"))
            continue
        if file_only and p.is_dir() and not p.is_symlink():
            click.echo(f"skip dir: {p}")
            continue
        if dir_only and (p.is_file() or p.is_symlink()):
            click.echo(f"skip file: {p}")
            continue
        if empty_only and p.is_dir() and not p.is_symlink():
            if any(p.iterdir()):
                click.echo(f"skip non-empty: {p}")
                continue

        if trash:
            confirm_each(f"In Trash verschieben: {p} ?", yes)
            do(f"trash {p}", shutil.move, str(p), str(trash_dir / p.name))
        else:
            if p.is_dir() and not p.is_symlink():
                if not recursive and not empty_only:
                    raise click.ClickException(f"{p} ist ein Ordner – nutze --recursive oder --empty-only.")
                if empty_only:
                    confirm_each(f"Ordner entfernen (leer): {p} ?", yes)
                    do(f"rmdir {p}", p.rmdir)
                else:
                    confirm_each(f"Ordner rekursiv löschen: {p} ?", yes)
                    do(f"rm -r {p}", shutil.rmtree, p)
            else:
                confirm_each(f"Datei löschen: {p} ?", yes)
                do(f"rm {p}", p.unlink)

# --------------------------- chmod ---------------------------

@cli.command()
@common_exec_options
@click.argument("mode", metavar="MODE")
@click.argument("paths", nargs=-1, required=True)
def chmod(dry_run, execute, yes, interactive, mode, paths):
    """Rechte setzen (MODE oktral, z. B. 0755 oder 0644). Default: DRY-RUN."""
    resolve_mode(execute, dry_run, interactive)
    echo_mode()
    try:
        m = int(mode, 8)
    except ValueError:
        raise click.ClickException("MODE muss oktal sein, z. B. 0755 oder 644.")
    for p in list_paths(paths):
        if not p.exists() and not p.is_symlink():
            click.echo(click.style(f"✖ fehlt: {p}", fg="red"))
            continue
        confirm_each(f"chmod {mode} {p} ?", yes)
        do(f"chmod {mode} {p}", os.chmod, p, m)

# --------------------------- chown ---------------------------

@cli.command()
@common_exec_options
@click.option("--user", "-u", type=str, help="Besitzer (Name oder UID).")
@click.option("--group","-g", type=str, help="Gruppe (Name oder GID).")
@click.argument("paths", nargs=-1, required=True)
def chown(dry_run, execute, yes, interactive, user, group, paths):
    """Besitzer/Gruppe setzen (root nötig). Default: DRY-RUN."""
    resolve_mode(execute, dry_run, interactive)
    echo_mode()
    if user is None and group is None:
        raise click.ClickException("Bitte --user und/oder --group angeben.")
    uid = -1 if user is None else (int(user) if user.isdigit() else pwd.getpwnam(user).pw_uid)
    gid = -1 if group is None else (int(group) if group.isdigit() else grp.getgrnam(group).gr_gid)
    for p in list_paths(paths):
        if not p.exists() and not p.is_symlink():
            click.echo(click.style(f"✖ fehlt: {p}", fg="red"))
            continue
        confirm_each(f"chown {user or '-'}:{group or '-'} {p} ?", yes)
        do(f"chown {user or '-'}:{group or '-'} {p}", os.chown, p, uid, gid)

# --------------------------- ln (Symlink) ---------------------------

@cli.command(name="ln")
@common_exec_options
@click.option("-f","--force", is_flag=True, help="Existierendes LINKPATH überschreiben.")
@click.argument("target", metavar="TARGET")
@click.argument("linkpath", metavar="LINKPATH")
def ln_cmd(dry_run, execute, yes, interactive, force, target, linkpath):
    """Symlink erstellen: LINKPATH -> TARGET. Default: DRY-RUN."""
    resolve_mode(execute, dry_run, interactive)
    echo_mode()
    t = Path(target).expanduser()
    l = Path(linkpath).expanduser()
    if l.exists() or l.is_symlink():
        conflict_handle(l, force=force, backup=False, yes=yes)

    def _mk():
        if l.exists() or l.is_symlink():
            try:
                if l.is_dir() and not l.is_symlink():
                    shutil.rmtree(l)
                else:
                    l.unlink()
            except FileNotFoundError:
                pass
        l.symlink_to(t, target_is_directory=t.is_dir())

    confirm_each(f"Symlink: {l} -> {t} ?", yes)
    do(f"ln -s {t} {l}", _mk)

# --------------------------- examples ---------------------------

@cli.command("examples")
def examples_fsx():
    """Beispiele & Kochbuch anzeigen und beenden."""
    _print_examples_and_exit_fsx()



# --------------------------- entry ---------------------------

if __name__ == "__main__":
    try:
        cli()
    except click.ClickException as e:
        click.echo(click.style(f"Fehler: {e}", fg="red"), err=True)
        sys.exit(2)
