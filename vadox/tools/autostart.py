"""
Autostart — Vadox automatisch beim System-Start starten.
Windows: Registry HKCU/Software/Microsoft/Windows/CurrentVersion/Run
macOS:   LaunchAgent Plist unter ~/Library/LaunchAgents/
Linux:   ~/.config/autostart/<name>.desktop
"""
import sys
import os
import platform
from pathlib import Path

APP_NAME  = "Vadox"
PLIST_ID  = "ai.vadox.app"


def _get_startup_command() -> list:
    """Ermittelt den Startbefehl — EXE-Bundle oder Python-Script."""
    if getattr(sys, 'frozen', False):
        return [sys.executable]
    main_py = str(Path(__file__).parents[2] / "main.py")
    return [sys.executable, main_py]


# ─────────────────────────── Windows ─────────────────────────────────────────

def _win_enable() -> str:
    try:
        import winreg
        reg_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        cmd = " ".join(f'"{c}"' for c in _get_startup_command())
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        return f"Vadox startet jetzt automatisch mit Windows.\nBefehl: {cmd}"
    except Exception as e:
        return f"Autostart konnte nicht aktiviert werden: {e}"


def _win_disable() -> str:
    try:
        import winreg
        reg_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        return "Vadox wurde aus dem Windows-Autostart entfernt."
    except FileNotFoundError:
        return "Vadox war nicht im Autostart."
    except Exception as e:
        return f"Fehler: {e}"


def _win_is_enabled() -> bool:
    try:
        import winreg
        reg_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


# ─────────────────────────── macOS ───────────────────────────────────────────

def _plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{PLIST_ID}.plist"


def _mac_enable() -> str:
    try:
        cmd = _get_startup_command()
        program_args = "\n".join(f"        <string>{c}</string>" for c in cmd)
        log_dir = Path.home() / ".vadox"
        log_dir.mkdir(parents=True, exist_ok=True)
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_ID}</string>
    <key>ProgramArguments</key>
    <array>
{program_args}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>{log_dir}/vadox.log</string>
    <key>StandardErrorPath</key>
    <string>{log_dir}/vadox_err.log</string>
</dict>
</plist>"""
        p = _plist_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(plist, encoding="utf-8")
        os.system(f"launchctl load '{p}'")
        return f"Vadox startet jetzt automatisch mit macOS.\nPlist: {p}"
    except Exception as e:
        return f"Autostart konnte nicht aktiviert werden: {e}"


def _mac_disable() -> str:
    try:
        p = _plist_path()
        if p.exists():
            os.system(f"launchctl unload '{p}'")
            p.unlink()
            return "Vadox wurde aus dem macOS-Autostart entfernt."
        return "Vadox war nicht im Autostart."
    except Exception as e:
        return f"Fehler: {e}"


def _mac_is_enabled() -> bool:
    return _plist_path().exists()


# ─────────────────────────── Linux ───────────────────────────────────────────

def _desktop_path() -> Path:
    return Path.home() / ".config" / "autostart" / f"{APP_NAME.lower()}.desktop"


def _linux_enable() -> str:
    try:
        cmd = " ".join(_get_startup_command())
        desktop = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={APP_NAME}\n"
            f"Exec={cmd}\n"
            "Hidden=false\n"
            "NoDisplay=false\n"
            "X-GNOME-Autostart-enabled=true\n"
        )
        p = _desktop_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(desktop, encoding="utf-8")
        return f"Vadox startet jetzt automatisch mit Linux.\nDatei: {p}"
    except Exception as e:
        return f"Autostart konnte nicht aktiviert werden: {e}"


def _linux_disable() -> str:
    try:
        p = _desktop_path()
        if p.exists():
            p.unlink()
            return "Vadox wurde aus dem Linux-Autostart entfernt."
        return "Vadox war nicht im Autostart."
    except Exception as e:
        return f"Fehler: {e}"


def _linux_is_enabled() -> bool:
    return _desktop_path().exists()


# ─────────────────────────── Öffentliche API ─────────────────────────────────

def enable_autostart() -> str:
    p = platform.system()
    if p == "Windows":
        return _win_enable()
    elif p == "Darwin":
        return _mac_enable()
    else:
        return _linux_enable()


def disable_autostart() -> str:
    p = platform.system()
    if p == "Windows":
        return _win_disable()
    elif p == "Darwin":
        return _mac_disable()
    else:
        return _linux_disable()


def is_autostart_enabled() -> bool:
    p = platform.system()
    if p == "Windows":
        return _win_is_enabled()
    elif p == "Darwin":
        return _mac_is_enabled()
    else:
        return _linux_is_enabled()


def get_autostart_status() -> str:
    if is_autostart_enabled():
        return "Vadox Autostart: AKTIV"
    return "Vadox Autostart: INAKTIV"
