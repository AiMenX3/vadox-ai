import os
import subprocess
import platform as _platform_mod
from pathlib import Path
from datetime import datetime

_PLATFORM = _platform_mod.system()


def take_screenshot(save_path: str = None) -> str:
    try:
        import pyautogui
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not save_path:
            desktop = Path.home() / "Desktop"
            save_path = str(desktop / f"screenshot_{ts}.png")
        img = pyautogui.screenshot()
        img.save(save_path)
        return f"Screenshot gespeichert: {save_path}"
    except Exception as e:
        return f"Screenshot fehlgeschlagen: {e}"


def _find_app(query: str) -> str | None:
    """
    Sucht eine Anwendung auf dem System.
    Gibt den Pfad zur EXE zurück oder None.
    """
    import glob

    q = query.lower().strip()
    # Wörter des Suchbegriffs — alle müssen im Dateinamen vorkommen
    words = [w for w in q.replace("-", " ").split() if len(w) > 1]

    # 1. Bekannte Windows-Systembefehle
    system_cmds = {
        "notepad": "notepad.exe", "notizblock": "notepad.exe",
        "rechner": "calc.exe", "calculator": "calc.exe", "taschenrechner": "calc.exe",
        "explorer": "explorer.exe", "datei-explorer": "explorer.exe",
        "paint": "mspaint.exe",
        "task manager": "taskmgr.exe", "taskmanager": "taskmgr.exe",
        "aufgaben-manager": "taskmgr.exe",
        "cmd": "cmd.exe", "eingabeaufforderung": "cmd.exe", "terminal": "cmd.exe",
        "powershell": "powershell.exe",
        "snipping tool": "SnippingTool.exe", "snip": "SnippingTool.exe",
        "control panel": "control.exe", "systemsteuerung": "control.exe",
        "regedit": "regedit.exe",
        "wordpad": "wordpad.exe",
    }
    if q in system_cmds:
        return system_cmds[q]
    for k, v in system_cmds.items():
        if q == k or all(w in k for w in words):
            return v

    # 2. Startmenü-Verknüpfungen durchsuchen (.lnk)
    lnk_dirs = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs"),
    ]
    best_lnk = None
    best_score = 0
    for lnk_dir in lnk_dirs:
        for lnk in lnk_dir.rglob("*.lnk"):
            name = lnk.stem.lower()
            score = sum(1 for w in words if w in name)
            if score == len(words) and score > best_score:
                best_score = score
                best_lnk = str(lnk)
            elif score > 0 and score > best_score and len(words) == 1:
                best_score = score
                best_lnk = str(lnk)
    if best_lnk:
        return best_lnk

    # 3. Typische Installations-Pfade nach EXE durchsuchen
    search_roots = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        str(Path.home() / "AppData/Local"),
        str(Path.home() / "AppData/Roaming"),
        r"C:\Games",
        r"D:\Games",
        r"D:\Program Files",
        r"D:\Program Files (x86)",
        r"E:\Games",
        r"E:\Program Files",
        str(Path.home() / "AppData/Local/Discord"),
        str(Path.home() / "AppData/Local/Programs"),
    ]

    candidates = []
    for root in search_roots:
        if not os.path.isdir(root):
            continue
        try:
            for dirpath, _, files in os.walk(root):
                for f in files:
                    if not f.lower().endswith(".exe"):
                        continue
                    fname = f.lower().replace(".exe", "").replace("-", " ").replace("_", " ")
                    score = sum(1 for w in words if w in fname)
                    if score > 0:
                        # Bonus wenn alle Wörter treffen
                        bonus = 10 if score == len(words) else 0
                        # Bonus wenn der Dateiname kurz ist (direkter Treffer)
                        length_penalty = len(fname)
                        candidates.append((bonus + score * 5 - length_penalty * 0.01,
                                           os.path.join(dirpath, f)))
        except PermissionError:
            continue

    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]

    return None


def _open_app_macos(app_name: str) -> str:
    """App auf macOS öffnen — nutzt 'open -a <App>'."""
    try:
        # Erst exakt versuchen
        result = subprocess.run(
            ["open", "-a", app_name], capture_output=True, text=True
        )
        if result.returncode == 0:
            return f"'{app_name}' wird gestartet."
        # Suche in /Applications
        apps_dir = Path("/Applications")
        q = app_name.lower()
        for app in apps_dir.glob("*.app"):
            if q in app.stem.lower():
                subprocess.Popen(["open", str(app)])
                return f"'{app.stem}' wird gestartet."
        # Suche in ~/Applications
        user_apps = Path.home() / "Applications"
        for app in user_apps.glob("*.app"):
            if q in app.stem.lower():
                subprocess.Popen(["open", str(app)])
                return f"'{app.stem}' wird gestartet."
        return f"Anwendung '{app_name}' nicht gefunden. Bitte prüfe ob sie in /Applications installiert ist."
    except Exception as e:
        return f"Anwendung konnte nicht geöffnet werden: {e}"


def _open_app_linux(app_name: str) -> str:
    """App auf Linux öffnen — versucht xdg-open und direkte Befehle."""
    try:
        result = subprocess.run(
            ["which", app_name.lower()], capture_output=True, text=True
        )
        if result.returncode == 0:
            subprocess.Popen([app_name.lower()])
            return f"'{app_name}' wird gestartet."
        # Über Desktop-Datei suchen
        desktop_dirs = [
            Path("/usr/share/applications"),
            Path.home() / ".local/share/applications",
        ]
        q = app_name.lower()
        for d in desktop_dirs:
            if not d.exists():
                continue
            for f in d.glob("*.desktop"):
                if q in f.stem.lower():
                    subprocess.Popen(["xdg-open", str(f)])
                    return f"'{f.stem}' wird gestartet."
        return f"Anwendung '{app_name}' nicht gefunden."
    except Exception as e:
        return f"Anwendung konnte nicht geöffnet werden: {e}"


def open_application(app_name: str) -> str:
    try:
        if _PLATFORM == "Darwin":
            return _open_app_macos(app_name)
        elif _PLATFORM == "Linux":
            return _open_app_linux(app_name)

        # Windows
        path = _find_app(app_name)
        if not path:
            return (f"Anwendung '{app_name}' wurde nicht gefunden. "
                    f"Bitte prüfe ob das Programm installiert ist.")
        if path.endswith(".lnk"):
            subprocess.Popen(["cmd", "/c", "start", "", path], shell=False)
        else:
            subprocess.Popen([path], shell=False)
        display = Path(path).stem
        return f"'{display}' wird gestartet."
    except Exception as e:
        return f"Anwendung konnte nicht geöffnet werden: {e}"


def open_url(url: str) -> str:
    try:
        import webbrowser
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return f"URL geöffnet: {url}"
    except Exception as e:
        return f"URL konnte nicht geöffnet werden: {e}"


def get_system_info() -> str:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        uptime_secs = int(__import__("time").time() - psutil.boot_time())
        h, rem = divmod(uptime_secs, 3600)
        m, s = divmod(rem, 60)
        return (
            f"CPU-Auslastung: {cpu} Prozent. "
            f"RAM: {mem.used // 1024 // 1024} MB von {mem.total // 1024 // 1024} MB belegt ({mem.percent} Prozent). "
            f"Festplatte: {disk.used // 1024 // 1024 // 1024} GB von {disk.total // 1024 // 1024 // 1024} GB belegt. "
            f"System läuft seit {h} Stunden und {m} Minuten."
        )
    except Exception as e:
        return f"Systeminfo nicht verfügbar: {e}"


def set_volume(level: int) -> str:
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        vol = max(0.0, min(1.0, level / 100.0))
        volume.SetMasterVolumeLevelScalar(vol, None)
        return f"Lautstärke auf {level} Prozent gesetzt."
    except Exception as e:
        return f"Lautstärke konnte nicht geändert werden: {e}"


def type_text(text: str) -> str:
    try:
        import pyautogui
        import time
        time.sleep(0.5)
        pyautogui.typewrite(text, interval=0.05)
        return f"Text eingegeben: {text}"
    except Exception as e:
        return f"Text eingabe fehlgeschlagen: {e}"
