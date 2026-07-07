"""
Vadox IT-Security Scanner
Scannt den PC nach Bedrohungen, verdächtigen Prozessen, Malware-Indikatoren
"""
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime


# Bekannte Malware-Prozessnamen (häufige Beispiele)
SUSPICIOUS_PROCESSES = {
    "njrat", "darkcomet", "nanocore", "remcos", "asyncrat", "quasar",
    "netbus", "subseven", "poison ivy", "gh0st", "xworm", "dcrat",
    "redline", "vidar", "raccoon", "azorult", "formbook", "agent tesla",
    "crypter", "keylogger", "miner", "xmrig", "minergate",
    "mimikatz", "procdump", "psexec", "wce", "fgdump",
    "netcat", "ncat", "pwdump",
}

# Verdächtige Autostart-Pfade
AUTOSTART_KEYS = [
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
    r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Run",
]

# Bekannte sichere Prozesse die wir ignorieren
WHITELIST = {
    "system", "svchost", "explorer", "taskmgr", "cmd", "powershell",
    "python", "pythonw", "chrome", "firefox", "msedge", "notepad",
    "code", "devenv", "outlook", "winword", "excel", "teams",
    "discord", "steam", "nvidia", "amd", "intel", "vadox",
    "antimalware", "defender", "mrt", "securityhealthsystray",
}


def _check_defender_status() -> dict:
    """Windows Defender Status abfragen."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-MpComputerStatus | Select-Object -Property "
             "AntivirusEnabled,RealTimeProtectionEnabled,AntivirusSignatureLastUpdated,"
             "QuickScanAge | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            return {
                "ok":         True,
                "av_enabled": data.get("AntivirusEnabled", False),
                "realtime":   data.get("RealTimeProtectionEnabled", False),
                "last_update": str(data.get("AntivirusSignatureLastUpdated", "Unbekannt"))[:10],
                "last_scan":  data.get("QuickScanAge", -1),
            }
    except Exception:
        pass
    return {"ok": False, "av_enabled": False, "realtime": False}


def _check_firewall() -> dict:
    """Windows Firewall Status prüfen."""
    try:
        result = subprocess.run(
            ["netsh", "advfirewall", "show", "allprofiles", "state"],
            capture_output=True, text=True, timeout=8
        )
        text = result.stdout.lower()
        on  = text.count("on")
        off = text.count("off")
        return {"enabled": on > off, "detail": "Aktiv" if on > off else "Teilweise deaktiviert"}
    except Exception:
        return {"enabled": False, "detail": "Unbekannt"}


def _check_processes() -> list[dict]:
    """Laufende Prozesse auf verdächtige Namen prüfen."""
    import psutil
    suspicious = []
    for proc in psutil.process_iter(["pid", "name", "exe", "username"]):
        try:
            name = (proc.info["name"] or "").lower().replace(".exe", "")
            if name in WHITELIST:
                continue
            # Prüfen ob Name einem bekannten Malware-Namen ähnelt
            for bad in SUSPICIOUS_PROCESSES:
                if bad in name:
                    suspicious.append({
                        "pid":  proc.info["pid"],
                        "name": proc.info["name"],
                        "exe":  proc.info.get("exe") or "Unbekannt",
                        "risk": "HOCH",
                        "reason": f"Entspricht bekanntem Schadprogramm-Muster: {bad}",
                    })
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return suspicious


def _check_autostart() -> list[dict]:
    """Autostart-Einträge auf verdächtige Einträge prüfen."""
    import winreg
    suspicious = []
    for key_path in AUTOSTART_KEYS:
        for hive, hive_name in [(winreg.HKEY_CURRENT_USER, "HKCU"),
                                 (winreg.HKEY_LOCAL_MACHINE, "HKLM")]:
            try:
                key = winreg.OpenKey(hive, key_path)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        i += 1
                        val_lower = value.lower()
                        # Verdächtige Pfade
                        flags = []
                        if "\\temp\\" in val_lower or "\\tmp\\" in val_lower:
                            flags.append("Startet aus TEMP-Ordner")
                        if "\\appdata\\roaming\\" in val_lower and "microsoft" not in val_lower:
                            flags.append("Startet aus AppData/Roaming")
                        if ".vbs" in val_lower or ".bat" in val_lower or ".ps1" in val_lower:
                            flags.append("Script-Datei im Autostart")
                        if flags:
                            suspicious.append({
                                "name":   name,
                                "value":  value[:80],
                                "hive":   hive_name,
                                "risk":   "MITTEL",
                                "reason": " | ".join(flags),
                            })
                    except OSError:
                        break
                winreg.CloseKey(key)
            except Exception:
                continue
    return suspicious


def _check_network() -> list[dict]:
    """Aktive Netzwerkverbindungen auf verdächtige Ports prüfen."""
    import psutil
    suspicious_ports = {
        1337, 4444, 5555, 6666, 7777, 8888, 9999,
        31337, 12345, 54321, 65535, 1234, 4321,
    }
    suspicious = []
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.status == "ESTABLISHED" and conn.raddr:
                port = conn.raddr.port
                if port in suspicious_ports:
                    try:
                        proc = psutil.Process(conn.pid) if conn.pid else None
                        pname = proc.name() if proc else "Unbekannt"
                    except Exception:
                        pname = "Unbekannt"
                    suspicious.append({
                        "remote": f"{conn.raddr.ip}:{port}",
                        "process": pname,
                        "pid":    conn.pid,
                        "risk":   "MITTEL",
                        "reason": f"Verbindung über bekannten Backdoor-Port {port}",
                    })
    except Exception:
        pass
    return suspicious


def _check_temp_executables() -> list[dict]:
    """Ausführbare Dateien in TEMP-Ordnern suchen."""
    suspicious = []
    temp_dirs = [
        Path(os.environ.get("TEMP", "")),
        Path(os.environ.get("TMP", "")),
        Path.home() / "AppData/Local/Temp",
    ]
    for temp in temp_dirs:
        if not temp.exists():
            continue
        try:
            for f in temp.iterdir():
                if f.suffix.lower() in (".exe", ".dll", ".bat", ".vbs", ".ps1"):
                    size = f.stat().st_size
                    if size > 1024:  # Größer als 1KB
                        suspicious.append({
                            "path":   str(f),
                            "size":   f"{size // 1024} KB",
                            "risk":   "MITTEL",
                            "reason": "Ausführbare Datei im TEMP-Ordner",
                        })
        except Exception:
            continue
    return suspicious[:10]  # Max 10


# ── Haupt-Scan-Funktion ───────────────────────────────────────────────────────

def run_full_scan() -> dict:
    """Führt einen vollständigen Sicherheitsscan durch."""
    started = datetime.now()
    results = {
        "timestamp":    started.isoformat(),
        "defender":     _check_defender_status(),
        "firewall":     _check_firewall(),
        "processes":    _check_processes(),
        "autostart":    _check_autostart(),
        "network":      _check_network(),
        "temp_files":   _check_temp_executables(),
        "risk_level":   "SICHER",
        "issues":       [],
        "duration_s":   0,
    }

    # Risiko-Level bestimmen
    high = []
    medium = []

    if not results["defender"].get("realtime"):
        high.append("Windows Defender Echtzeit-Schutz ist DEAKTIVIERT")
    if not results["firewall"].get("enabled"):
        high.append("Windows Firewall ist DEAKTIVIERT")
    for p in results["processes"]:
        high.append(f"Verdächtiger Prozess: {p['name']} — {p['reason']}")
    for n in results["network"]:
        medium.append(f"Verdächtige Verbindung: {n['remote']} ({n['process']})")
    for a in results["autostart"]:
        medium.append(f"Verdächtiger Autostart: {a['name']} — {a['reason']}")
    for t in results["temp_files"]:
        medium.append(f"EXE in TEMP: {Path(t['path']).name}")

    results["issues"] = high + medium
    if high:
        results["risk_level"] = "HOCH"
    elif medium:
        results["risk_level"] = "MITTEL"

    results["duration_s"] = round((datetime.now() - started).total_seconds(), 1)
    return results


def quick_scan() -> str:
    """Schneller Scan für Chat-Antwort."""
    r = run_full_scan()
    level = r["risk_level"]
    issues = r["issues"]

    if level == "SICHER":
        return (f"Sicherheitsscan abgeschlossen. Keine Bedrohungen gefunden. "
                f"Windows Defender aktiv: {r['defender'].get('realtime', False)}. "
                f"Firewall aktiv: {r['firewall'].get('enabled', False)}. "
                f"Scan-Dauer: {r['duration_s']} Sekunden.")
    else:
        found = ". ".join(issues[:5])
        return (f"Sicherheitsscan: RISIKO-LEVEL {level}. "
                f"{len(issues)} Problem(e) gefunden: {found}. "
                f"Scan-Dauer: {r['duration_s']} Sekunden.")
