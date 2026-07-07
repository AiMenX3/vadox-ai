"""
Morgen-Briefing — startet automatisch wenn Vadox geöffnet wird.
Spricht: Uhrzeit, Wetter, ungelesene E-Mails, Kalendertermine heute.
"""

import threading
from datetime import datetime


def _build_briefing_text() -> str:
    """Sammelt alle Infos und baut den Briefing-Text."""
    now   = datetime.now()
    stunde = now.hour
    minute = now.strftime("%M")
    wochentag = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][now.weekday()]
    datum = now.strftime(f"{wochentag}, %d. %B %Y")

    # Begrüßung je nach Tageszeit
    if stunde < 12:
        gruss = "Guten Morgen"
    elif stunde < 18:
        gruss = "Guten Tag"
    else:
        gruss = "Guten Abend"

    parts = [f"{gruss}! Es ist {now.hour} Uhr {minute}, {datum}."]

    # Wetter
    try:
        from vadox.tools.weather import get_weather
        from vadox.core import settings
        cfg  = settings.load()
        city = cfg.get("weather_city", "Berlin")
        raw  = get_weather(city=city, days=1)
        # Kompakten Wettertext extrahieren
        lines = [l.strip() for l in raw.split("\n") if l.strip()]
        if lines:
            # Ersten informativen Satz nehmen
            weather_line = lines[0] if lines else ""
            for l in lines:
                if "°" in l or "grad" in l.lower():
                    weather_line = l
                    break
            parts.append(f"Das Wetter in {city}: {weather_line}.")
    except Exception as e:
        print(f"[Briefing Wetter] {e}")

    # Ungelesene E-Mails
    try:
        from vadox.tools.email_tool import get_unread_count
        count = get_unread_count()
        if isinstance(count, int) and count > 0:
            parts.append(f"Du hast {count} ungelesene E-Mails.")
        elif isinstance(count, str) and any(c.isdigit() for c in count):
            parts.append(f"E-Mails: {count}.")
    except Exception as e:
        print(f"[Briefing E-Mail] {e}")

    # Kalendertermine heute
    try:
        from vadox.tools.calendar_tool import get_todays_events
        events_raw = get_todays_events()
        if events_raw and "keine" not in events_raw.lower() and "error" not in events_raw.lower():
            lines = [l.strip() for l in events_raw.split("\n") if l.strip() and l.strip() != "•"]
            count = len([l for l in lines if l.startswith("•") or ":" in l])
            if count > 0:
                parts.append(f"Heute stehen {count} Termine in deinem Kalender.")
    except Exception as e:
        print(f"[Briefing Kalender] {e}")

    # Abschluss
    parts.append("Ich stehe für deine Fragen bereit. Was kann ich für dich tun?")

    return " ".join(parts)


def run_briefing(tts_engine, delay_seconds: float = 1.5):
    """
    Startet das Morgen-Briefing in einem Hintergrundthread.
    delay_seconds: kurze Pause damit UI fertig geladen ist.
    """
    def _run():
        import time
        time.sleep(delay_seconds)
        try:
            text = _build_briefing_text()
            print(f"[Briefing] {text}")
            tts_engine.speak(text)
        except Exception as e:
            print(f"[Briefing Fehler] {e}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def should_run_briefing() -> bool:
    """
    Gibt True zurück wenn das Briefing heute noch nicht gelaufen ist
    und die aktuelle Uhrzeit sinnvoll ist (05:00 – 22:00).
    """
    import json
    from pathlib import Path

    state_path = Path.home() / ".vadox" / "briefing_state.json"
    today = datetime.now().strftime("%Y-%m-%d")
    hour  = datetime.now().hour

    if hour < 5 or hour >= 22:
        return False

    try:
        if state_path.exists():
            data = json.loads(state_path.read_text(encoding="utf-8"))
            if data.get("last_run") == today:
                return False  # Heute schon gelaufen
    except Exception:
        pass

    # Heute noch nicht gelaufen → speichern und True zurückgeben
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps({"last_run": today}), encoding="utf-8"
        )
    except Exception:
        pass

    return True
