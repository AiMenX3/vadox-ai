"""
Vadox Security Fixer — behebt gefundene Sicherheitsprobleme
"""
import subprocess
import os
from pathlib import Path


def fix_defender() -> tuple[bool, str]:
    """Windows Defender Echtzeit-Schutz aktivieren."""
    try:
        r = subprocess.run(
            ["powershell", "-Command",
             "Set-MpPreference -DisableRealtimeMonitoring $false"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            return True, "Windows Defender Echtzeit-Schutz wurde aktiviert."
        return False, f"Fehler: {r.stderr.strip()[:120]}"
    except Exception as e:
        return False, f"Fehler: {e}"


def fix_firewall() -> tuple[bool, str]:
    """Windows Firewall für alle Profile aktivieren."""
    try:
        r = subprocess.run(
            ["netsh", "advfirewall", "set", "allprofiles", "state", "on"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            return True, "Windows Firewall wurde für alle Profile aktiviert."
        return False, f"Fehler: {r.stderr.strip()[:120]}"
    except Exception as e:
        return False, f"Fehler: {e}"


def fix_kill_process(pid: int, name: str) -> tuple[bool, str]:
    """Verdächtigen Prozess beenden."""
    try:
        import psutil
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=5)
        return True, f"Prozess '{name}' (PID {pid}) wurde beendet."
    except Exception as e:
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                           capture_output=True, timeout=8)
            return True, f"Prozess '{name}' (PID {pid}) wurde beendet."
        except Exception as e2:
            return False, f"Konnte Prozess nicht beenden: {e2}"


def fix_autostart(name: str, hive: str) -> tuple[bool, str]:
    """Autostart-Eintrag aus der Registry entfernen."""
    import winreg
    keys = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
        r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Run",
    ]
    hive_map = {
        "HKCU": winreg.HKEY_CURRENT_USER,
        "HKLM": winreg.HKEY_LOCAL_MACHINE,
    }
    root = hive_map.get(hive, winreg.HKEY_CURRENT_USER)
    for key_path in keys:
        try:
            key = winreg.OpenKey(root, key_path, 0, winreg.KEY_SET_VALUE)
            try:
                winreg.DeleteValue(key, name)
                winreg.CloseKey(key)
                return True, f"Autostart-Eintrag '{name}' wurde entfernt."
            except FileNotFoundError:
                winreg.CloseKey(key)
                continue
        except Exception:
            continue
    return False, f"Eintrag '{name}' nicht gefunden oder kein Zugriff."


def fix_delete_temp_file(path: str) -> tuple[bool, str]:
    """Ausführbare Datei aus TEMP-Ordner löschen."""
    try:
        f = Path(path)
        if f.exists():
            f.unlink()
            return True, f"Datei '{f.name}' wurde gelöscht."
        return False, "Datei existiert nicht mehr."
    except Exception as e:
        return False, f"Fehler beim Löschen: {e}"


def fix_network_connection(pid: int, remote: str) -> tuple[bool, str]:
    """Prozess hinter verdächtiger Verbindung beenden."""
    if pid:
        return fix_kill_process(pid, f"Prozess hinter {remote}")
    return False, "Kein Prozess-ID bekannt — Verbindung kann nicht beendet werden."
