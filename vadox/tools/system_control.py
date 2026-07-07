"""
System-Steuerung — Lautstärke, Dateien, Prozesse, Power, Papierkorb usw.
Unterstützt Windows, macOS und Linux.
"""
import os
import subprocess
import shutil
import platform
from pathlib import Path
from datetime import datetime, timedelta

_PLATFORM = platform.system()  # "Windows", "Darwin", "Linux"


# ── Lautstärke ────────────────────────────────────────────────────────────────

def set_volume(level: int) -> str:
    try:
        level = max(0, min(100, int(level)))
        if _PLATFORM == "Windows":
            from pycaw.pycaw import AudioUtilities
            devices = AudioUtilities.GetSpeakers()
            devices.EndpointVolume.SetMasterVolumeLevelScalar(level / 100.0, None)
        elif _PLATFORM == "Darwin":
            subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
        else:
            subprocess.run(["amixer", "-q", "sset", "Master", f"{level}%"], check=True)
        return f"Lautstärke auf {level}% gesetzt."
    except Exception as e:
        return f"Lautstärke-Fehler: {e}"


def get_volume() -> str:
    try:
        if _PLATFORM == "Windows":
            from pycaw.pycaw import AudioUtilities
            devices = AudioUtilities.GetSpeakers()
            vol = devices.EndpointVolume
            level = int(vol.GetMasterVolumeLevelScalar() * 100)
            muted = vol.GetMute()
            status = " (Stummgeschaltet)" if muted else ""
            return f"Aktuelle Lautstärke: {level}%{status}"
        elif _PLATFORM == "Darwin":
            result = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                capture_output=True, text=True
            )
            return f"Aktuelle Lautstärke: {result.stdout.strip()}%"
        else:
            result = subprocess.run(["amixer", "sget", "Master"], capture_output=True, text=True)
            import re
            m = re.search(r"\[(\d+)%\]", result.stdout)
            return f"Aktuelle Lautstärke: {m.group(1) if m else '?'}%"
    except Exception as e:
        return f"Lautstärke-Fehler: {e}"


def volume_up(amount: int = 10) -> str:
    try:
        if _PLATFORM == "Windows":
            from pycaw.pycaw import AudioUtilities
            devices = AudioUtilities.GetSpeakers()
            vol = devices.EndpointVolume
            current = int(vol.GetMasterVolumeLevelScalar() * 100)
            new_level = min(100, current + int(amount))
            vol.SetMasterVolumeLevelScalar(new_level / 100.0, None)
            return f"Lautstärke erhöht: {current}% auf {new_level}%"
        elif _PLATFORM == "Darwin":
            subprocess.run(["osascript", "-e",
                f"set volume output volume (output volume of (get volume settings) + {amount})"], check=True)
            return f"Lautstärke um {amount}% erhöht."
        else:
            subprocess.run(["amixer", "-q", "sset", "Master", f"{amount}%+"], check=True)
            return f"Lautstärke um {amount}% erhöht."
    except Exception as e:
        return f"Lautstärke-Fehler: {e}"


def volume_down(amount: int = 10) -> str:
    try:
        if _PLATFORM == "Windows":
            from pycaw.pycaw import AudioUtilities
            devices = AudioUtilities.GetSpeakers()
            vol = devices.EndpointVolume
            current = int(vol.GetMasterVolumeLevelScalar() * 100)
            new_level = max(0, current - int(amount))
            vol.SetMasterVolumeLevelScalar(new_level / 100.0, None)
            return f"Lautstärke verringert: {current}% auf {new_level}%"
        elif _PLATFORM == "Darwin":
            subprocess.run(["osascript", "-e",
                f"set volume output volume (output volume of (get volume settings) - {amount})"], check=True)
            return f"Lautstärke um {amount}% verringert."
        else:
            subprocess.run(["amixer", "-q", "sset", "Master", f"{amount}%-"], check=True)
            return f"Lautstärke um {amount}% verringert."
    except Exception as e:
        return f"Lautstärke-Fehler: {e}"


def mute_volume() -> str:
    try:
        if _PLATFORM == "Windows":
            from pycaw.pycaw import AudioUtilities
            AudioUtilities.GetSpeakers().EndpointVolume.SetMute(1, None)
        elif _PLATFORM == "Darwin":
            subprocess.run(["osascript", "-e", "set volume with output muted"], check=True)
        else:
            subprocess.run(["amixer", "-q", "sset", "Master", "mute"], check=True)
        return "Ton stummgeschaltet."
    except Exception as e:
        return f"Stummschalten fehlgeschlagen: {e}"


def unmute_volume() -> str:
    try:
        if _PLATFORM == "Windows":
            from pycaw.pycaw import AudioUtilities
            AudioUtilities.GetSpeakers().EndpointVolume.SetMute(0, None)
        elif _PLATFORM == "Darwin":
            subprocess.run(["osascript", "-e", "set volume without output muted"], check=True)
        else:
            subprocess.run(["amixer", "-q", "sset", "Master", "unmute"], check=True)
        return "Stummschaltung aufgehoben."
    except Exception as e:
        return f"Fehler: {e}"


# ── Papierkorb ────────────────────────────────────────────────────────────────

def empty_recycle_bin() -> str:
    try:
        if _PLATFORM == "Windows":
            import ctypes
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x0007)
            if result == 0 or result == -2147418113:
                return "Papierkorb wurde geleert."
            return f"Papierkorb geleert (Code: {result})."
        elif _PLATFORM == "Darwin":
            subprocess.run(["osascript", "-e", 'tell application "Finder" to empty trash'], check=True)
            return "Papierkorb wurde geleert."
        else:
            trash = Path.home() / ".local" / "share" / "Trash" / "files"
            if trash.exists():
                shutil.rmtree(str(trash))
                trash.mkdir(parents=True, exist_ok=True)
            return "Papierkorb wurde geleert."
    except Exception as e:
        return f"Papierkorb konnte nicht geleert werden: {e}"


def get_recycle_bin_size() -> str:
    try:
        if _PLATFORM == "Windows":
            import ctypes
            class SHQUERYRBINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_ulong),
                    ("i64Size", ctypes.c_longlong),
                    ("i64NumItems", ctypes.c_longlong),
                ]
            info = SHQUERYRBINFO()
            info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
            ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info))
            return f"Papierkorb: {info.i64NumItems} Dateien, {info.i64Size/1024/1024:.1f} MB"
        elif _PLATFORM == "Darwin":
            trash = Path.home() / ".Trash"
        else:
            trash = Path.home() / ".local" / "share" / "Trash" / "files"
        count = sum(1 for _ in trash.iterdir()) if trash.exists() else 0
        size = sum(f.stat().st_size for f in trash.rglob("*") if f.is_file()) if trash.exists() else 0
        return f"Papierkorb: {count} Elemente, {size/1024/1024:.1f} MB"
    except Exception as e:
        return f"Papierkorb-Info Fehler: {e}"


def delete_old_files(folder: str = "Downloads", days: int = 30, dry_run: bool = False) -> str:
    try:
        folder_map = {
            "downloads": Path.home() / "Downloads",
            "desktop":   Path.home() / "Desktop",
            "dokumente": Path.home() / "Documents",
            "documents": Path.home() / "Documents",
            "bilder":    Path.home() / "Pictures",
            "pictures":  Path.home() / "Pictures",
            "videos":    Path.home() / "Videos",
            "musik":     Path.home() / "Music",
            "music":     Path.home() / "Music",
            "temp":      Path(os.environ.get("TEMP", "/tmp")) if _PLATFORM == "Windows" else Path("/tmp"),
        }
        folder_path = folder_map.get(folder.lower().strip(), Path(folder))
        if not folder_path.exists():
            return f"Ordner nicht gefunden: {folder_path}"

        cutoff = datetime.now() - timedelta(days=days)
        deleted, errors, total_size = [], [], 0
        for item in folder_path.iterdir():
            try:
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if mtime < cutoff:
                    size = item.stat().st_size if item.is_file() else 0
                    if not dry_run:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    deleted.append(item.name)
                    total_size += size
            except Exception as e:
                errors.append(f"{item.name}: {e}")

        size_mb = total_size / 1024 / 1024
        action = "Gefunden (Testmodus)" if dry_run else "Gelöscht"
        if not deleted:
            return f"Keine Dateien älter als {days} Tage in '{folder_path.name}' gefunden."
        result = f"{action}: {len(deleted)} Dateien ({size_mb:.1f} MB) aus '{folder_path.name}'\n"
        result += "\n".join(f"  • {f}" for f in deleted[:15])
        if len(deleted) > 15:
            result += f"\n  ... und {len(deleted)-15} weitere"
        if errors:
            result += f"\n\nFehler bei {len(errors)} Dateien."
        return result
    except Exception as e:
        return f"Fehler beim Löschen: {e}"


def get_large_files(folder: str = "Downloads", min_size_mb: int = 100) -> str:
    try:
        folder_map = {
            "downloads": Path.home() / "Downloads",
            "desktop":   Path.home() / "Desktop",
            "dokumente": Path.home() / "Documents",
        }
        folder_path = folder_map.get(folder.lower(), Path(folder))
        files = []
        for item in folder_path.rglob("*"):
            if item.is_file():
                try:
                    size_mb = item.stat().st_size / 1024 / 1024
                    if size_mb >= min_size_mb:
                        files.append((size_mb, item))
                except Exception:
                    pass
        if not files:
            return f"Keine Dateien über {min_size_mb} MB in '{folder_path.name}' gefunden."
        files.sort(reverse=True)
        lines = [f"Große Dateien in '{folder_path.name}' (>{min_size_mb} MB):"]
        for size_mb, f in files[:20]:
            lines.append(f"  • {f.name} — {size_mb:.0f} MB")
        return "\n".join(lines)
    except Exception as e:
        return f"Fehler: {e}"


# ── Prozesse ──────────────────────────────────────────────────────────────────

def list_running_apps() -> str:
    try:
        import psutil
        ignore = {
            "svchost.exe", "system", "registry", "smss.exe", "csrss.exe",
            "wininit.exe", "services.exe", "lsass.exe", "winlogon.exe",
            "fontdrvhost.exe", "dwm.exe", "launchd", "kernel_task",
        }
        apps = []
        for proc in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                name = proc.info["name"]
                mem  = proc.info["memory_info"].rss // 1024 // 1024
                if mem > 10 and name.lower() not in ignore:
                    apps.append((mem, name))
            except Exception:
                pass
        apps.sort(reverse=True)
        lines = ["Laufende Anwendungen (nach RAM-Nutzung):"]
        for mem, name in apps[:20]:
            lines.append(f"  • {name} — {mem} MB")
        return "\n".join(lines)
    except Exception as e:
        return f"Prozess-Liste Fehler: {e}"


def kill_application(app_name: str) -> str:
    try:
        import psutil
        killed = []
        name_lower = app_name.lower().replace(".exe", "")
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pname = proc.info["name"].lower().replace(".exe", "")
                if name_lower in pname or pname in name_lower:
                    proc.terminate()
                    killed.append(proc.info["name"])
            except Exception:
                pass
        if killed:
            return f"Beendet: {', '.join(set(killed))}"
        return f"Keine laufende Anwendung '{app_name}' gefunden."
    except Exception as e:
        return f"Fehler: {e}"


# ── Power-Verwaltung ──────────────────────────────────────────────────────────

def shutdown_pc(minutes: int = 0) -> str:
    try:
        if _PLATFORM == "Windows":
            seconds = minutes * 60 if minutes > 0 else 10
            subprocess.run(["shutdown", "/s", "/t", str(seconds)], check=True)
        elif _PLATFORM == "Darwin":
            delay = f"+{minutes}" if minutes > 0 else "now"
            subprocess.run(["sudo", "shutdown", "-h", delay], check=True)
        else:
            delay = f"+{minutes}" if minutes > 0 else "now"
            subprocess.run(["sudo", "shutdown", "-h", delay], check=True)
        msg = f"in {minutes} Minuten" if minutes > 0 else "gleich"
        return f"PC wird {msg} heruntergefahren."
    except Exception as e:
        return f"Herunterfahren fehlgeschlagen: {e}"


def restart_pc(minutes: int = 0) -> str:
    try:
        if _PLATFORM == "Windows":
            seconds = minutes * 60 if minutes > 0 else 10
            subprocess.run(["shutdown", "/r", "/t", str(seconds)], check=True)
        elif _PLATFORM == "Darwin":
            delay = f"+{minutes}" if minutes > 0 else "now"
            subprocess.run(["sudo", "shutdown", "-r", delay], check=True)
        else:
            delay = f"+{minutes}" if minutes > 0 else "now"
            subprocess.run(["sudo", "shutdown", "-r", delay], check=True)
        msg = f"in {minutes} Minuten" if minutes > 0 else "gleich"
        return f"PC wird {msg} neu gestartet."
    except Exception as e:
        return f"Neustart fehlgeschlagen: {e}"


def cancel_shutdown() -> str:
    try:
        if _PLATFORM == "Windows":
            subprocess.run(["shutdown", "/a"], check=True)
        else:
            subprocess.run(["sudo", "killall", "shutdown"], check=True)
        return "Geplantes Herunterfahren wurde abgebrochen."
    except Exception as e:
        return f"Fehler: {e}"


def sleep_pc() -> str:
    try:
        if _PLATFORM == "Windows":
            subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"])
        elif _PLATFORM == "Darwin":
            subprocess.run(["pmset", "sleepnow"], check=True)
        else:
            subprocess.run(["systemctl", "suspend"], check=True)
        return "PC wird in den Ruhezustand versetzt."
    except Exception as e:
        return f"Ruhezustand fehlgeschlagen: {e}"


def lock_screen() -> str:
    try:
        if _PLATFORM == "Windows":
            import ctypes
            ctypes.windll.user32.LockWorkStation()
        elif _PLATFORM == "Darwin":
            subprocess.run([
                "osascript", "-e",
                'tell application "System Events" to keystroke "q" using {command down, control down}'
            ], check=True)
        else:
            try:
                subprocess.run(["gnome-screensaver-command", "--lock"], check=True)
            except Exception:
                subprocess.run(["xdg-screensaver", "lock"], check=True)
        return "Bildschirm gesperrt."
    except Exception as e:
        return f"Sperren fehlgeschlagen: {e}"


# ── Zwischenablage ────────────────────────────────────────────────────────────

def get_clipboard() -> str:
    try:
        import pyperclip
        text = pyperclip.paste()
        if not text:
            return "Zwischenablage ist leer."
        return f"Zwischenablage: {text[:500]}"
    except Exception as e:
        return f"Fehler: {e}"


def set_clipboard(text: str) -> str:
    try:
        import pyperclip
        pyperclip.copy(text)
        return f"In Zwischenablage kopiert: {text[:100]}"
    except Exception as e:
        return f"Fehler: {e}"


# ── Bildschirm-Helligkeit ─────────────────────────────────────────────────────

def set_brightness(level: int) -> str:
    try:
        level = max(0, min(100, int(level)))
        if _PLATFORM == "Windows":
            result = subprocess.run(
                ["powershell", "-Command",
                 f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return f"Helligkeit auf {level}% gesetzt."
            return "Helligkeit konnte nicht gesetzt werden (nur bei Laptop-Displays verfügbar)."
        elif _PLATFORM == "Darwin":
            bright = level / 100.0
            subprocess.run(["osascript", "-e",
                f'tell application "System Events" to set brightness of displays to {bright}'], check=True)
            return f"Helligkeit auf {level}% gesetzt."
        else:
            try:
                subprocess.run(["brightnessctl", "set", f"{level}%"], check=True)
                return f"Helligkeit auf {level}% gesetzt."
            except Exception:
                return "brightnessctl nicht gefunden. Bitte installieren: sudo apt install brightnessctl"
    except Exception as e:
        return f"Fehler: {e}"


# ── Disk-Bereinigung ──────────────────────────────────────────────────────────

def clean_temp_files() -> str:
    try:
        if _PLATFORM == "Windows":
            temp_dirs = [
                Path(os.environ.get("TEMP", "")),
                Path(os.environ.get("TMP", "")),
                Path("C:/Windows/Temp"),
            ]
        elif _PLATFORM == "Darwin":
            temp_dirs = [Path("/private/tmp")]
        else:
            temp_dirs = [Path("/tmp")]

        deleted_count = 0
        freed_bytes   = 0
        for temp_dir in temp_dirs:
            if not temp_dir.exists():
                continue
            for item in temp_dir.iterdir():
                try:
                    size = item.stat().st_size if item.is_file() else 0
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                    deleted_count += 1
                    freed_bytes   += size
                except Exception:
                    pass

        freed_mb = freed_bytes / 1024 / 1024
        return f"Temp-Ordner bereinigt: {deleted_count} Dateien gelöscht, {freed_mb:.1f} MB freigegeben."
    except Exception as e:
        return f"Fehler: {e}"


def get_disk_usage() -> str:
    try:
        import psutil
        lines = ["Festplatten-Belegung:"]
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                total_gb = usage.total / 1024**3
                used_gb  = usage.used  / 1024**3
                free_gb  = usage.free  / 1024**3
                lines.append(
                    f"  • {part.mountpoint} — {used_gb:.0f} GB belegt / "
                    f"{free_gb:.0f} GB frei (gesamt {total_gb:.0f} GB)"
                )
            except Exception:
                pass
        return "\n".join(lines)
    except Exception as e:
        return f"Fehler: {e}"
