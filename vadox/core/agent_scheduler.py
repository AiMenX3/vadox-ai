"""
Vadox Autonomer Agent-Modus
Führt Aufgaben automatisch im Hintergrund aus.
"""
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable


AGENTS_PATH = Path.home() / ".vadox" / "agents.json"

# Callback: wird aufgerufen wenn ein Agent ein Ergebnis hat
# Signature: on_result(agent_id, agent_name, result_text)
_result_callback: Callable | None = None
_agents: dict = {}
_lock = threading.Lock()
_running = False
_thread: threading.Thread | None = None


# ── Eingebaute Agent-Definitionen ────────────────────────────────────────────

BUILTIN_AGENTS = {
    "morning_briefing": {
        "id":          "morning_briefing",
        "name":        "Morgen-Briefing",
        "description": "Täglich um die gewählte Uhrzeit: Wetter, E-Mails & Termine zusammenfassen",
        "icon":        "🌅",
        "interval":    "daily",
        "time":        "08:00",
        "enabled":     False,
        "last_run":    None,
        "task":        "morning_briefing",
    },
    "email_monitor": {
        "id":          "email_monitor",
        "name":        "E-Mail Wächter",
        "description": "Prüft alle X Minuten auf neue E-Mails und meldet ungelesene",
        "icon":        "📧",
        "interval":    "minutes",
        "minutes":     30,
        "enabled":     False,
        "last_run":    None,
        "task":        "email_monitor",
    },
    "daily_report": {
        "id":          "daily_report",
        "name":        "Tages-Report",
        "description": "Erstellt täglich einen Bericht mit Zusammenfassung des Tages",
        "icon":        "📊",
        "interval":    "daily",
        "time":        "18:00",
        "enabled":     False,
        "last_run":    None,
        "task":        "daily_report",
    },
    "reminder": {
        "id":          "reminder",
        "name":        "Erinnerungs-Agent",
        "description": "Erinnert dich an bevorstehende Kalender-Termine (15 Min vorher)",
        "icon":        "⏰",
        "interval":    "minutes",
        "minutes":     5,
        "enabled":     False,
        "last_run":    None,
        "task":        "reminder",
        "_reminded":   [],
    },
    "system_monitor": {
        "id":          "system_monitor",
        "name":        "System-Überwachung",
        "description": "Warnt wenn CPU > 90% oder RAM > 85% über längere Zeit",
        "icon":        "🖥",
        "interval":    "minutes",
        "minutes":     5,
        "enabled":     False,
        "last_run":    None,
        "task":        "system_monitor",
        "_high_cpu_since": None,
        "_high_ram_since": None,
    },
}


# ── Persistenz ────────────────────────────────────────────────────────────────

def _load_agents() -> dict:
    try:
        if AGENTS_PATH.exists():
            saved = json.loads(AGENTS_PATH.read_text(encoding="utf-8"))
            merged = {}
            for aid, agent in BUILTIN_AGENTS.items():
                merged[aid] = dict(agent)
                if aid in saved:
                    # Nutzer-Einstellungen übernehmen
                    for k in ("enabled", "time", "minutes", "last_run"):
                        if k in saved[aid]:
                            merged[aid][k] = saved[aid][k]
            return merged
    except Exception:
        pass
    return {k: dict(v) for k, v in BUILTIN_AGENTS.items()}


def _save_agents():
    try:
        AGENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        saveable = {}
        for aid, agent in _agents.items():
            saveable[aid] = {
                "enabled":  agent.get("enabled", False),
                "time":     agent.get("time", "08:00"),
                "minutes":  agent.get("minutes", 30),
                "last_run": agent.get("last_run"),
            }
        AGENTS_PATH.write_text(json.dumps(saveable, indent=2, ensure_ascii=False),
                               encoding="utf-8")
    except Exception as e:
        print(f"[AgentScheduler] Speichern fehlgeschlagen: {e}")


def get_agents() -> dict:
    return dict(_agents)


def set_agent_enabled(agent_id: str, enabled: bool):
    with _lock:
        if agent_id in _agents:
            _agents[agent_id]["enabled"] = enabled
            _save_agents()


def set_agent_time(agent_id: str, time_str: str):
    with _lock:
        if agent_id in _agents:
            _agents[agent_id]["time"] = time_str
            _save_agents()


def set_agent_minutes(agent_id: str, minutes: int):
    with _lock:
        if agent_id in _agents:
            _agents[agent_id]["minutes"] = minutes
            _save_agents()


# ── Task-Ausführung ───────────────────────────────────────────────────────────

def _run_task(agent: dict) -> str | None:
    task = agent.get("task")

    if task == "morning_briefing":
        return _task_morning_briefing()
    elif task == "email_monitor":
        return _task_email_monitor()
    elif task == "daily_report":
        return _task_daily_report()
    elif task == "reminder":
        return _task_reminder(agent)
    elif task == "system_monitor":
        return _task_system_monitor(agent)
    return None


def _task_morning_briefing() -> str:
    parts = [f"Guten Morgen! Hier ist dein Briefing für {datetime.now().strftime('%A, %d. %B %Y')}."]

    # Wetter
    try:
        from vadox.tools.weather import get_weather
        from vadox.core import settings
        city = settings.get("user_city", "Berlin")
        w = get_weather(city, days=1)
        parts.append(f"Wetter: {w[:120]}")
    except Exception:
        pass

    # E-Mails
    try:
        from vadox.tools.email_tool import get_unread_count
        count = get_unread_count()
        parts.append(f"E-Mails: {count}")
    except Exception:
        pass

    # Termine
    try:
        from vadox.tools.calendar_tool import get_todays_events
        events = get_todays_events()
        parts.append(f"Kalender: {events[:200]}")
    except Exception:
        pass

    return " | ".join(parts)


def _task_email_monitor() -> str | None:
    try:
        from vadox.tools.email_tool import get_unread_count
        result = get_unread_count()
        # Nur melden wenn ungelesene vorhanden
        if "0 ungelesene" in result or "keine" in result.lower():
            return None
        return f"E-Mail Wächter: {result}"
    except Exception:
        return None


def _task_daily_report() -> str:
    parts = [f"Tages-Report — {datetime.now().strftime('%d.%m.%Y')}"]

    try:
        from vadox.tools.calendar_tool import get_todays_events
        events = get_todays_events()
        parts.append(f"Termine heute: {events[:150]}")
    except Exception:
        pass

    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        parts.append(f"System: CPU {cpu}%, RAM {mem}%")
    except Exception:
        pass

    return " | ".join(parts)


def _task_reminder(agent: dict) -> str | None:
    try:
        from vadox.tools.calendar_tool import get_calendar_events
        events_raw = get_calendar_events(days=1)
        if "Kein" in events_raw or "konnte nicht" in events_raw:
            return None

        now = datetime.now()
        reminded = agent.get("_reminded", [])
        new_reminders = []

        for line in events_raw.split("|"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            try:
                # Format: "DD.MM.YYYY HH:MM bis HH:MM: Titel"
                parts = line.split(":")
                dt_str = parts[0].strip() + ":" + parts[1].strip()
                event_dt = datetime.strptime(dt_str[:16], "%d.%m.%Y %H:%M")
                diff = (event_dt - now).total_seconds() / 60
                uid = dt_str[:16]
                if 0 < diff <= 15 and uid not in reminded:
                    title = ":".join(parts[2:]).split("bis")[0].strip() if len(parts) > 2 else "Termin"
                    new_reminders.append(f"Erinnerung: In {int(diff)} Minuten — {title}")
                    reminded.append(uid)
            except Exception:
                continue

        agent["_reminded"] = reminded[-50:]  # Max 50 merken

        if new_reminders:
            return " | ".join(new_reminders)
    except Exception:
        pass
    return None


def _task_system_monitor(agent: dict) -> str | None:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        now = datetime.now()
        warnings = []

        if cpu > 90:
            if agent.get("_high_cpu_since") is None:
                agent["_high_cpu_since"] = now
            elif (now - agent["_high_cpu_since"]).seconds > 120:
                warnings.append(f"WARNUNG: CPU-Auslastung seit 2 Minuten über 90% (aktuell {cpu:.0f}%)")
                agent["_high_cpu_since"] = None
        else:
            agent["_high_cpu_since"] = None

        if mem > 85:
            if agent.get("_high_ram_since") is None:
                agent["_high_ram_since"] = now
            elif (now - agent["_high_ram_since"]).seconds > 120:
                warnings.append(f"WARNUNG: RAM-Auslastung seit 2 Minuten über 85% (aktuell {mem:.0f}%)")
                agent["_high_ram_since"] = None
        else:
            agent["_high_ram_since"] = None

        return " | ".join(warnings) if warnings else None
    except Exception:
        return None


# ── Scheduler-Loop ────────────────────────────────────────────────────────────

def _should_run(agent: dict) -> bool:
    if not agent.get("enabled"):
        return False

    last_run = agent.get("last_run")
    interval = agent.get("interval", "minutes")

    if interval == "daily":
        run_time = agent.get("time", "08:00")
        now = datetime.now()
        h, m = map(int, run_time.split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)

        if last_run:
            last_dt = datetime.fromisoformat(last_run)
            # Heute schon gelaufen?
            if last_dt.date() >= now.date() and last_dt.hour == h:
                return False

        # Ist es Zeit? (innerhalb 1 Minute Toleranz)
        return abs((now - target).total_seconds()) < 60

    elif interval == "minutes":
        minutes = agent.get("minutes", 30)
        if not last_run:
            return True
        last_dt = datetime.fromisoformat(last_run)
        return (datetime.now() - last_dt).total_seconds() >= minutes * 60

    return False


def _scheduler_loop():
    global _running
    print("[AgentScheduler] Gestartet")
    while _running:
        try:
            with _lock:
                agents_copy = {k: dict(v) for k, v in _agents.items()}

            for aid, agent in agents_copy.items():
                if _should_run(agent):
                    result = _run_task(agent)
                    with _lock:
                        _agents[aid]["last_run"] = datetime.now().isoformat()
                        # Interne Zustandsvariablen zurückschreiben
                        for k in ("_reminded", "_high_cpu_since", "_high_ram_since"):
                            if k in agents_copy[aid]:
                                _agents[aid][k] = agents_copy[aid][k]
                        _save_agents()

                    if result and _result_callback:
                        try:
                            _result_callback(aid, agent["name"], result)
                        except Exception:
                            pass

        except Exception as e:
            print(f"[AgentScheduler] Fehler im Loop: {e}")

        time.sleep(30)  # Alle 30 Sekunden prüfen

    print("[AgentScheduler] Gestoppt")


# ── Öffentliche API ───────────────────────────────────────────────────────────

def start(on_result: Callable | None = None):
    global _running, _thread, _agents, _result_callback
    if _running:
        return
    _result_callback = on_result
    _agents = _load_agents()
    _running = True
    _thread = threading.Thread(target=_scheduler_loop, daemon=True)
    _thread.start()


def stop():
    global _running
    _running = False


def run_now(agent_id: str):
    """Führt einen Agent sofort aus (manuell)."""
    with _lock:
        if agent_id not in _agents:
            return
        agent = dict(_agents[agent_id])

    result = _run_task(agent)

    with _lock:
        _agents[agent_id]["last_run"] = datetime.now().isoformat()
        _save_agents()

    if result and _result_callback:
        try:
            _result_callback(agent_id, _agents[agent_id]["name"], result)
        except Exception:
            pass
    return result
