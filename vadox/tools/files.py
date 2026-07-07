import os
import shutil
import glob
from pathlib import Path
from datetime import datetime


def search_files(name: str, search_path: str = None) -> str:
    try:
        base = search_path or str(Path.home())
        pattern = f"**/*{name}*"
        matches = []
        for p in Path(base).rglob(f"*{name}*"):
            matches.append(str(p))
            if len(matches) >= 20:
                break
        if not matches:
            return f"Keine Dateien mit '{name}' gefunden."
        return f"Gefundene Dateien: " + ", ".join(matches)
    except Exception as e:
        return f"Suche fehlgeschlagen: {e}"


def list_directory(path: str = None) -> str:
    try:
        target = path or str(Path.home() / "Desktop")
        items = os.listdir(target)
        files = []
        folders = []
        for item in items:
            full = os.path.join(target, item)
            if os.path.isdir(full):
                folders.append(f"[Ordner] {item}")
            else:
                size = os.path.getsize(full)
                files.append(f"[Datei] {item} ({size} Bytes)")
        result = folders + files
        return f"Inhalt von {target}: " + ", ".join(result[:30])
    except Exception as e:
        return f"Verzeichnis konnte nicht gelesen werden: {e}"


def read_file(path: str) -> str:
    try:
        p = Path(path)
        if not p.exists():
            return f"Datei '{path}' existiert nicht."
        if p.stat().st_size > 50_000:
            return f"Datei zu groß zum Lesen (über 50KB)."
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"Datei konnte nicht gelesen werden: {e}"


def create_file(path: str, content: str = "") -> str:
    try:
        p = Path(path)
        # Relativer Pfad oder nur Dateiname → Desktop
        if not p.is_absolute():
            p = Path.home() / "Desktop" / p
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        # Datei im Dateimanager anzeigen
        try:
            import subprocess, platform as _pl
            if _pl.system() == "Windows":
                subprocess.Popen(["explorer", "/select,", str(p)])
            elif _pl.system() == "Darwin":
                subprocess.Popen(["open", "-R", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p.parent)])
        except Exception:
            pass
        return f"Datei erstellt und gespeichert: {p}\nGröße: {p.stat().st_size} Bytes"
    except Exception as e:
        return f"Datei konnte nicht erstellt werden: {e}"


def delete_file(path: str) -> str:
    try:
        p = Path(path)
        if not p.exists():
            return f"Datei '{path}' existiert nicht."
        if p.is_dir():
            shutil.rmtree(str(p))
            return f"Ordner gelöscht: {path}"
        else:
            p.unlink()
            return f"Datei gelöscht: {path}"
    except Exception as e:
        return f"Löschen fehlgeschlagen: {e}"


def move_file(src: str, dst: str) -> str:
    try:
        shutil.move(src, dst)
        return f"Verschoben: {src} nach {dst}"
    except Exception as e:
        return f"Verschieben fehlgeschlagen: {e}"


def get_file_info(path: str) -> str:
    try:
        p = Path(path)
        if not p.exists():
            return f"'{path}' existiert nicht."
        stat = p.stat()
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
        size = stat.st_size
        return (
            f"Datei: {p.name}, Größe: {size} Bytes, "
            f"Zuletzt geändert: {modified}, Pfad: {str(p.resolve())}"
        )
    except Exception as e:
        return f"Dateiinfo fehlgeschlagen: {e}"
