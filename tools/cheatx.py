#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, math, textwrap, shutil
from typing import List, Dict, Iterable, Tuple
import click

# ---------------------- Datenbasis ----------------------
# Spalten: group, cmd, desc, options, args, examples (Mehrzeilig erlaubt)
ROWS: List[Dict[str, str]] = [
    # Dateiverwaltung (dv)
    {"group":"dv","cmd":"ls","desc":"Verzeichnisinhalte auflisten",
     "options":"-l (Details), -a (hidden), -R (rekursiv)","args":"[VERZ]",
     "examples":"ls -la /etc\nls -R /var/log"},
    {"group":"dv","cmd":"cd","desc":"In Verzeichnisse wechseln","options":"–","args":"VERZ",
     "examples":"cd /opt && pwd"},
    {"group":"dv","cmd":"pwd","desc":"Aktuellen Pfad ausgeben","options":"–","args":"–",
     "examples":"pwd"},
    {"group":"dv","cmd":"touch","desc":"Datei anlegen/zeitstempel setzen","options":"–","args":"DATEI",
     "examples":"touch foo.txt"},
    {"group":"dv","cmd":"mkdir","desc":"Verzeichnis anlegen","options":"-p (Eltern)","args":"VERZ",
     "examples":"mkdir -p /srv/app/logs"},
    {"group":"dv","cmd":"rm","desc":"Datei/Ordner löschen","options":"-r (rekursiv), -f (force)","args":"ZIEL…",
     "examples":"rm -f file\nrm -r dir/"},
    {"group":"dv","cmd":"rmdir","desc":"Leeres Verzeichnis löschen","options":"–","args":"VERZ",
     "examples":"rmdir emptydir"},
    {"group":"dv","cmd":"mv","desc":"Verschieben/Umbenennen","options":"-f (force), -i (ask)","args":"SRC… DST",
     "examples":"mv a.txt b.txt\nmv file /tmp/"},
    {"group":"dv","cmd":"cp","desc":"Kopieren","options":"-a (archiv), -r (rekursiv)","args":"SRC… DST",
     "examples":"cp -a dir/ backup/"},
    {"group":"dv","cmd":"ln","desc":"(Sym-)Link erstellen","options":"-s (symlink), -f (force)","args":"TARGET LINK",
     "examples":"ln -s /opt/app/current /usr/local/bin/app"},
    {"group":"dv","cmd":"cat","desc":"Dateien ausgeben/concat","options":"-n (Nrn)","args":"DATEI…",
     "examples":"cat /etc/hosts"},
    {"group":"dv","cmd":"find","desc":"Dateien finden","options":"-name, -type f/d, -mtime","args":"PFAD [EXPR]",
     "examples":"find /var/log -type f -name '*.log'"},
    {"group":"dv","cmd":"grep","desc":"Texte durchsuchen (Regex)","options":"-i (CI), -r (rek), -E (ERE)","args":"PATTERN [DATEI…]",
     "examples":"grep -R \"ERROR\" /var/log"},
    {"group":"dv","cmd":"diff","desc":"Unterschiede (Text)","options":"-u (Unified)","args":"A B",
     "examples":"diff -u a.conf b.conf"},
    {"group":"dv","cmd":"cmp","desc":"Byte-Vergleich","options":"-l (list)","args":"A B",
     "examples":"cmp a.bin b.bin"},
    {"group":"dv","cmd":"wc","desc":"Zeilen/Wörter/Bytes zählen","options":"-l (lines), -w (words), -c (bytes)","args":"DATEI…",
     "examples":"wc -l /etc/passwd"},
    {"group":"dv","cmd":"tar","desc":"Archive packen/entpacken","options":"-czf (tgz), -xzf (extract)","args":"…",
     "examples":"tar -czf backup.tgz /srv/data\ntar -xzf backup.tgz -C /restore"},
    {"group":"dv","cmd":"zip/unzip","desc":"ZIP packen/entpacken","options":"zip -r, unzip -l","args":"…",
     "examples":"zip -r data.zip data/\nunzip data.zip -d out/"},
    # Benutzer/Gruppen (bv)
    {"group":"bv","cmd":"adduser","desc":"Benutzer anlegen (interaktiv)","options":"--disabled-password …","args":"NAME",
     "examples":"sudo adduser deploy"},
    {"group":"bv","cmd":"passwd","desc":"Passwort setzen/ändern","options":"-l lock, -u unlock","args":"[NAME]",
     "examples":"sudo passwd user"},
    {"group":"bv","cmd":"groupadd","desc":"Gruppe anlegen","options":"-f (ok wenn exist.)","args":"GRUPPE",
     "examples":"sudo groupadd admins"},
    {"group":"bv","cmd":"chgrp","desc":"Gruppe eines Pfads setzen","options":"-R (rekursiv)","args":"GRUPPE DATEI…",
     "examples":"sudo chgrp -R www-data /srv/www"},
    # Rechte (rv)
    {"group":"rv","cmd":"chmod","desc":"Rechte setzen (oktal/symbolisch)","options":"-R (rek)","args":"MODE DATEI…",
     "examples":"chmod 0644 file\nchmod -R u+rwX,g+rX dir/"},
    {"group":"rv","cmd":"chown","desc":"Besitzer/Gruppe setzen","options":"-R (rek)","args":"USER[:GRP] DATEI…",
     "examples":"sudo chown -R pi:pi /opt/data"},
    {"group":"rv","cmd":"chattr/lsattr","desc":"Immutable/Attribute","options":"+i (immutable)","args":"DATEI",
     "examples":"sudo chattr +i critical.conf\nlsattr critical.conf"},
    # Verzeichnis/Navigation (vs)
    {"group":"vs","cmd":"tree","desc":"Baumansicht (falls installiert)","options":"-a, -L N","args":"[PFAD]",
     "examples":"tree -L 2 /opt"},
    {"group":"vs","cmd":"clear","desc":"Terminal löschen","options":"–","args":"–",
     "examples":"clear"},
    # Systeminfo (sys)
    {"group":"sys","cmd":"uname","desc":"Kernel/Systeminfo","options":"-a (alles), -r (release)","args":"–",
     "examples":"uname -a\nuname -r"},
    {"group":"sys","cmd":"hostname","desc":"Hostname/FQDN","options":"-f (FQDN), -I (IPs)","args":"[NAME]",
     "examples":"hostname -f\nhostname -I"},
    {"group":"sys","cmd":"uptime","desc":"Betriebszeit/Load","options":"-p (pretty)","args":"–",
     "examples":"uptime -p"},
    {"group":"sys","cmd":"lscpu","desc":"CPU-Infos","options":"-e (extended), -p (parse)","args":"–",
     "examples":"lscpu -e"},
    {"group":"sys","cmd":"lshw","desc":"Hardware-Infos","options":"-short, -class","args":"–",
     "examples":"sudo lshw -short"},
    {"group":"sys","cmd":"crontab","desc":"Benutzer-Crontab bearbeiten/anzeigen","options":"-e (edit), -l (list)","args":"—",
     "examples":"crontab -l\ncrontab -e"},
    {"group":"proc","cmd":"systemd timer","desc":"Geplante systemd-Timer","options":"list-timers, status","args":"—",
     "examples":"systemctl list-timers\nsystemctl status my.timer"},
    {"group":"sys","cmd":"journalctl","desc":"Logs anzeigen (systemd)","options":"-u UNIT, -f (follow), -b (since boot)","args":"—",
     "examples":"journalctl -u entropywatcher-os.service -b -r"},
    # Netzwerk (net)
    {"group":"net","cmd":"ip","desc":"Netzwerk konfigurieren/anzeigen","options":"addr, link, route","args":"…",
     "examples":"ip addr\nip route"},
    {"group":"net","cmd":"ping","desc":"Latenz testen","options":"-c N (count)","args":"HOST",
     "examples":"ping -c 4 1.1.1.1"},
    {"group":"net","cmd":"traceroute","desc":"Pfad verfolgen","options":"-n (no DNS)","args":"HOST",
     "examples":"traceroute -n 8.8.8.8"},
    {"group":"net","cmd":"dig","desc":"DNS-Abfragen","options":"+short","args":"NAME [TYPE]",
     "examples":"dig +short A example.com"},
    {"group":"net","cmd":"ssh","desc":"Secure Shell","options":"-i KEY, -p PORT","args":"user@host [cmd]",
     "examples":"ssh -i ~/.ssh/id_ed25519 user@host"},
    {"group":"net","cmd":"wget","desc":"Download","options":"-O, -q","args":"URL",
     "examples":"wget -O out.bin https://…"},
    {"group":"net","cmd":"ftp/sftp","desc":"Dateitransfer","options":"—","args":"host",
     "examples":"sftp user@host"},
    # Pakete (pkg)
    {"group":"pkg","cmd":"apt update","desc":"Paketquellen aktualisieren","options":"-y (auto-yes)","args":"—",
     "examples":"sudo apt update"},
    {"group":"pkg","cmd":"apt full-upgrade","desc":"Vollständiges Upgrade (inkl. Abhängigkeitswechsel)","options":"-y","args":"—",
     "examples":"sudo apt update && sudo apt full-upgrade -y"},
    {"group":"pkg","cmd":"apt autoremove","desc":"Ungenutzte Pakete entfernen","options":"-y","args":"—",
     "examples":"sudo apt autoremove -y"},
    {"group":"pkg","cmd":"apt autoclean","desc":"Alte Paketdateien bereinigen","options":"—","args":"—",
     "examples":"sudo apt autoclean"},
    {"group":"pkg","cmd":"apt list --upgradable","desc":"Anstehende Updates anzeigen","options":"—","args":"—",
     "examples":"apt list --upgradable"},
    {"group":"pkg","cmd":"yum/dnf","desc":"Pakete (RHEL)","options":"install, remove","args":"…",
     "examples":"sudo dnf install htop"},
    {"group":"pkg","cmd":"pacman","desc":"Pakete (Arch)","options":"-S, -R, -Sy","args":"…",
     "examples":"sudo pacman -S htop"},
    # Storage/FS (stor)
    {"group":"stor","cmd":"lsblk","desc":"Blockgeräte/Partitionen anzeigen","options":"-f (FS-Infos), -o (Spalten)","args":"—",
     "examples":"lsblk -f"},
    {"group":"stor","cmd":"blkid","desc":"UUID/Label von Geräten","options":"—","args":"[DEVICE]",
     "examples":"sudo blkid"},
    {"group":"stor","cmd":"df","desc":"Freier/Belegter Speicher","options":"-h (human), -T (FS-Typ)","args":"[PFAD]",
     "examples":"df -h\ndf -h /"},
    {"group":"stor","cmd":"du","desc":"Belegung je Verzeichnis","options":"-h (human), -x (1 FS), --max-depth N","args":"[PFAD]",
     "examples":"du -xh --max-depth 1 /var | sort -h"},
    {"group":"stor","cmd":"mount/umount","desc":"Dateisysteme ein-/aushängen","options":"-t TYPE, -o OPTS","args":"DEVICE MOUNT",
     "examples":"sudo mount -o ro /dev/sdb1 /mnt/usb\nsudo umount /mnt/usb"},
    {"group":"stor","cmd":"fstab (Datei)","desc":"Persistente Mounts (Konfig)","options":"—","args":"→ /etc/fstab",
     "examples":"sudo nano /etc/fstab"},
]

GROUPS = {
    "dv":"Dateiverwaltung",
    "bv":"Benutzer/Gruppen",
    "rv":"Rechte",
    "vs":"Navigation",
    "sys":"System",
    "net":"Netz",
    "pkg":"Pakete",
    "proc":"Prozesse",
    "stor":"Storage/FS",
}
GROUP_ABBR = {k:k for k in GROUPS}  # Kurzlabel in Tabelle

# ---------------------- Ausgabe ----------------------
def term_width(default=100) -> int:
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return default

def filter_rows(groups: Iterable[str], search: str) -> List[Dict[str,str]]:
    sel = [r for r in ROWS if (not groups or r["group"] in groups)]
    if search:
        rx = re.compile(search, re.I)
        sel = [r for r in sel if rx.search(r["cmd"]) or rx.search(r["desc"]) or rx.search(r["examples"])]
    return sel

def dynamic_widths(total: int, compact: bool, wide: bool) -> Dict[str,int]:
    if wide:
        desc_w, opt_w = 56, 36
    elif compact:
        desc_w, opt_w = 34, 26
    else:
        desc_w, opt_w = 42, 30
    w = {
        "group": 4,
        "cmd":   16,
        "desc":  desc_w,
        "opt":   opt_w,
        "args":  10,
        "ex":    0,
    }
    used = sum(v for k,v in w.items() if k != "ex") + 5
    w["ex"] = max(0, total - used)
    return w

def wrap(text: str, width: int) -> List[str]:
    if width <= 0:
        return [text]
    return textwrap.wrap(text, width=width, replace_whitespace=False, drop_whitespace=False) or [""]

def fmt_table(rows: List[Dict[str,str]], *, width:int, examples_lines:int, show_examples:bool, compact:bool, wide:bool) -> str:
    col = dynamic_widths(width, compact, wide)
    hdr = f'{"Gr":<{col["group"]}} {"Befehl":<{col["cmd"]}} {"Beschreibung":<{col["desc"]}} {"Optionen":<{col["opt"]}} {"Arg":<{col["args"]}}'
    if show_examples and col["ex"]>10:
        hdr += f' {"Beispiele":<{col["ex"]}}'
    sep = "-"*len(hdr)
    out = [hdr, sep]
    for r in rows:
        ex_lines = r["examples"].splitlines() if r["examples"] else []
        if examples_lines > 0:
            ex_lines = ex_lines[:examples_lines]
        ex_text = " • ".join(ex_lines) if ex_lines else ""
        parts = [
            wrap(GROUP_ABBR.get(r["group"], r["group"]), col["group"]),
            wrap(r["cmd"], col["cmd"]),
            wrap(r["desc"], col["desc"]),
            wrap(r["options"], col["opt"]),
            wrap(r["args"], col["args"]),
        ]
        max_lines = max(len(p) for p in parts)
        ex_wrapped = wrap(ex_text, col["ex"]) if (show_examples and col["ex"]>10) else []
        max_lines = max(max_lines, len(ex_wrapped))
        for i in range(max_lines):
            line = f'{(parts[0][i] if i < len(parts[0]) else ""):<{col["group"]}} ' \
                   f'{(parts[1][i] if i < len(parts[1]) else ""):<{col["cmd"]}} ' \
                   f'{(parts[2][i] if i < len(parts[2]) else ""):<{col["desc"]}} ' \
                   f'{(parts[3][i] if i < len(parts[3]) else ""):<{col["opt"]}} ' \
                   f'{(parts[4][i] if i < len(parts[4]) else ""):<{col["args"]}}'
            if show_examples and col["ex"]>10:
                line += f' {(ex_wrapped[i] if i < len(ex_wrapped) else ""):<{col["ex"]}}'
            out.append(line)
    return "\n".join(out)

def fmt_md(rows: List[Dict[str,str]], examples_lines:int, show_examples:bool) -> str:
    cols = ["Gr","Befehl","Beschreibung","Optionen","Arg"]
    if show_examples: cols.append("Beispiele")
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"]*len(cols)) + "|"]
    for r in rows:
        ex = r["examples"].splitlines()[:examples_lines] if show_examples else []
        ex_text = "<br>".join(ex)
        base = [GROUP_ABBR.get(r["group"],r["group"]), f'`{r["cmd"]}`', r["desc"], r["options"], r["args"]]
        if show_examples: base.append(ex_text)
        out.append("| " + " | ".join(base) + " |")
    return "\n".join(out)

def paginate(rows: List[Dict[str,str]], page: int, per_page: int) -> Tuple[List[Dict[str,str]], int, int]:
    total = len(rows)
    pages = max(1, math.ceil(total / max(1, per_page)))
    p = max(1, min(page, pages))
    start = (p-1)*per_page
    return rows[start:start+per_page], p, pages

# ---------------------- CLI ----------------------
@click.group(context_settings=dict(help_option_names=["-h","--help"]))
@click.option("--examples", is_flag=True, help="Beispiele/Kochbuch anzeigen und beenden.")
@click.pass_context
def cli(ctx, examples):
    if examples:
        print(EXAMPLES.strip()); raise SystemExit(0)

@cli.command("show")
@click.option("--dv", is_flag=True, help="Dateiverwaltung")
@click.option("--bv", is_flag=True, help="Benutzer/Gruppen")
@click.option("--rv", is_flag=True, help="Rechte")
@click.option("--vs", is_flag=True, help="Navigation")
@click.option("--sys", "sys_", is_flag=True, help="System")
@click.option("--net", is_flag=True, help="Netz")
@click.option("--pkg", is_flag=True, help="Pakete")
@click.option("--proc", is_flag=True, help="Prozesse")
@click.option("--stor", is_flag=True, help="Storage/Speicher")
@click.option("--all", "all_", is_flag=True, help="Alle Gruppen")
@click.option("--search", "-s", type=str, default="", help="Regex in Befehl/Beschreibung/Beispielen")
@click.option("--format", "fmt", type=click.Choice(["table","md","plain"]), default="table", help="Ausgabeformat")
@click.option("--page", type=int, default=1, help="Seite")
@click.option("--per-page", type=int, default=20, help="Zeilen pro Seite")
@click.option("--no-examples", is_flag=True, help="Beispiele ausblenden")
@click.option("--examples-lines", type=int, default=1, help="Wie viele Beispielzeilen pro Eintrag")
@click.option("--compact", is_flag=True, help="Kompakter Tabellenmodus")
@click.option("--wide", is_flag=True, help="Breitere Spalten (mehr Platz für Beschreibung/Optionen)")
def show(dv,bv,rv,vs,sys_,net,pkg,proc,stor,all_,search,fmt,page,per_page,no_examples,examples_lines,compact,wide):
    """Befehle strukturiert anzeigen (gruppiert, paginiert, kompakt/wide)."""
    groups = []
    if all_ or not any([dv,bv,rv,vs,sys_,net,pkg,proc,stor]):
        groups = list(GROUPS.keys())
    else:
        if dv: groups.append("dv")
        if bv: groups.append("bv")
        if rv: groups.append("rv")
        if vs: groups.append("vs")
        if sys_: groups.append("sys")
        if net: groups.append("net")
        if pkg: groups.append("pkg")
        if proc: groups.append("proc")
        if stor: groups.append("stor")

    rows = filter_rows(groups, search)
    page_rows, cur, pages = paginate(rows, page, per_page)
    width = term_width()

    if fmt == "md":
        out = fmt_md(page_rows, examples_lines, not no_examples)
    elif fmt == "plain":
        out = "\n".join(f'{r["cmd"]}: {r["desc"]}' for r in page_rows)
    else:
        out = fmt_table(page_rows, width=width, examples_lines=examples_lines,
                        show_examples=(not no_examples), compact=compact, wide=wide)

    click.echo(out)
    click.echo(click.style(f"\nSeite {cur}/{pages} • Treffer: {len(rows)} • Gruppen: {', '.join(groups) or 'alle'} • Breite: {width}", fg="blue"))

@cli.command("groups")
def groups():
    """Nur Gruppenübersicht zeigen."""
    for k,v in GROUPS.items():
        print(f"--{k:<5}  {v}")

@cli.command("examples")
def examples():
    """Beispiele anzeigen und beenden."""
    print(EXAMPLES.strip())

EXAMPLES = r"""
Beispiele:

# Alles, kompakt, 2 Beispielzeilen pro Eintrag
cheatx.py show --all --compact --examples-lines 2

# Nur Dateiverwaltung + Rechte, Tabelle (wide)
cheatx.py show --dv --rv --wide

# Als Markdown (README-ready)
cheatx.py show --dv --format md

# Suche nach 'zip' (regex), 10 pro Seite, Seite 2
cheatx.py show --all -s zip --per-page 10 --page 2

# Gruppenübersicht
cheatx.py groups
"""

if __name__ == "__main__":
    cli()
