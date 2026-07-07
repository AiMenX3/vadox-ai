"""
Kalender-Integration für Vadox.
Unterstützt: Outlook Exchange, Google Calendar (CalDAV), lokale ICS-Datei
"""
import os
from datetime import datetime, timedelta, date
from pathlib import Path
from vadox.core import settings


def _get_cfg():
    cfg = settings.load()
    return {
        "provider":   cfg.get("cal_provider", ""),
        "email":      cfg.get("email_address", ""),
        "password":   cfg.get("email_password", ""),
        "domain":     cfg.get("exchange_domain", ""),
        "server":     cfg.get("exchange_server", ""),
        "cal_url":    cfg.get("cal_caldav_url", ""),
    }


# ── Exchange (Outlook Firma / Outlook.com) ────────────────────────────────────

def _exchange_account():
    cfg = _get_cfg()
    from exchangelib import Credentials, Account, DELEGATE, Configuration
    username = f"{cfg['domain']}\\{cfg['email']}" if cfg["domain"] else cfg["email"]
    creds = Credentials(username=username, password=cfg["password"])
    if cfg["server"]:
        config = Configuration(server=cfg["server"], credentials=creds)
        return Account(primary_smtp_address=cfg["email"], config=config,
                       autodiscover=False, access_type=DELEGATE)
    return Account(primary_smtp_address=cfg["email"], credentials=creds,
                   autodiscover=True, access_type=DELEGATE)


def _get_events_exchange(days: int = 7) -> list[dict]:
    acc = _exchange_account()
    from exchangelib import EWSDateTime, EWSTimeZone
    tz   = EWSTimeZone.localzone()
    now  = EWSDateTime.now(tz)
    end  = now + timedelta(days=days)
    items = acc.calendar.view(start=now, end=end).order_by("start")
    events = []
    for item in items:
        try:
            start = item.start.astimezone().strftime("%d.%m.%Y %H:%M") if item.start else "?"
            end_t = item.end.astimezone().strftime("%H:%M") if item.end else "?"
            events.append({
                "title":    item.subject or "(kein Titel)",
                "start":    start,
                "end":      end_t,
                "location": item.location or "",
                "id":       str(item.id) if item.id else "",
            })
        except Exception:
            continue
    return events


def _create_event_exchange(title: str, start_dt: datetime, end_dt: datetime,
                           location: str = "", body: str = "") -> str:
    from exchangelib import CalendarItem, EWSDateTime, EWSTimeZone
    acc = _exchange_account()
    tz  = EWSTimeZone.localzone()
    item = CalendarItem(
        account=acc,
        folder=acc.calendar,
        subject=title,
        start=EWSDateTime.from_datetime(start_dt.replace(tzinfo=None)).replace(tzinfo=tz),
        end=EWSDateTime.from_datetime(end_dt.replace(tzinfo=None)).replace(tzinfo=tz),
        location=location,
        body=body,
    )
    item.save()
    return f"Termin '{title}' am {start_dt.strftime('%d.%m.%Y %H:%M')} erstellt."


# ── CalDAV (Google Calendar, iCloud, Nextcloud …) ─────────────────────────────

def _caldav_calendar():
    import caldav
    cfg = _get_cfg()
    url = cfg["cal_url"]
    if not url:
        raise ValueError("Keine CalDAV-URL konfiguriert.")
    client = caldav.DAVClient(url=url, username=cfg["email"], password=cfg["password"])
    principal = client.principal()
    calendars = principal.calendars()
    if not calendars:
        raise ValueError("Kein Kalender gefunden.")
    return calendars[0]


def _get_events_caldav(days: int = 7) -> list[dict]:
    cal = _caldav_calendar()
    now = datetime.now()
    end = now + timedelta(days=days)
    raw = cal.date_search(start=now, end=end, expand=True)
    events = []
    for obj in raw:
        try:
            comp = obj.icalendar_component
            dt_start = comp.get("DTSTART")
            dt_end   = comp.get("DTEND")
            if dt_start:
                s = dt_start.dt
                e = dt_end.dt if dt_end else s
                if isinstance(s, date) and not isinstance(s, datetime):
                    s = datetime(s.year, s.month, s.day)
                    e = datetime(e.year, e.month, e.day)
                events.append({
                    "title":    str(comp.get("SUMMARY", "(kein Titel)")),
                    "start":    s.strftime("%d.%m.%Y %H:%M"),
                    "end":      e.strftime("%H:%M"),
                    "location": str(comp.get("LOCATION", "")),
                    "id":       str(comp.get("UID", "")),
                })
        except Exception:
            continue
    events.sort(key=lambda x: x["start"])
    return events


def _create_event_caldav(title: str, start_dt: datetime, end_dt: datetime,
                         location: str = "", body: str = "") -> str:
    import uuid
    from icalendar import Calendar, Event
    cal_obj = _caldav_calendar()
    cal = Calendar()
    cal.add("prodid", "-//Vadox//DE")
    cal.add("version", "2.0")
    event = Event()
    event.add("summary", title)
    event.add("dtstart", start_dt)
    event.add("dtend", end_dt)
    event.add("uid", str(uuid.uuid4()))
    if location:
        event.add("location", location)
    if body:
        event.add("description", body)
    cal.add_component(event)
    cal_obj.add_event(cal.to_ical().decode())
    return f"Termin '{title}' am {start_dt.strftime('%d.%m.%Y %H:%M')} erstellt."


# ── ICS-Datei (universell, kein Account nötig) ───────────────────────────────

def _create_ics_file(title: str, start_dt: datetime, end_dt: datetime,
                     location: str = "", body: str = "") -> str:
    import uuid
    from icalendar import Calendar, Event
    cal = Calendar()
    cal.add("prodid", "-//Vadox//DE")
    cal.add("version", "2.0")
    event = Event()
    event.add("summary", title)
    event.add("dtstart", start_dt)
    event.add("dtend", end_dt)
    event.add("uid", str(uuid.uuid4()))
    if location:
        event.add("location", location)
    if body:
        event.add("description", body)
    cal.add_component(event)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path.home() / "Desktop" / f"Termin_{ts}.ics"
    path.write_bytes(cal.to_ical())
    import subprocess
    subprocess.Popen(["cmd", "/c", "start", "", str(path)], shell=False)
    return f"Termin '{title}' als ICS-Datei gespeichert und geöffnet: {path}"


# ── Datum parsen ──────────────────────────────────────────────────────────────

def _parse_datetime(text: str) -> datetime:
    """
    Wandelt natürliche Datumseingaben in datetime um.
    z.B. "morgen 15:00", "Montag 10:30", "25.12.2025 14:00"
    """
    text = text.strip().lower()
    now  = datetime.now()

    # Relative Tage
    relative = {
        "heute": 0, "today": 0,
        "morgen": 1, "tomorrow": 1,
        "übermorgen": 2,
    }
    weekdays_de = {
        "montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3,
        "freitag": 4, "samstag": 5, "sonntag": 6,
    }

    base_date = now.date()
    time_part = "09:00"

    for word, delta in relative.items():
        if word in text:
            base_date = (now + timedelta(days=delta)).date()
            text = text.replace(word, "").strip()
            break
    else:
        for name, wd in weekdays_de.items():
            if name in text:
                days_ahead = (wd - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                base_date = (now + timedelta(days=days_ahead)).date()
                text = text.replace(name, "").strip()
                break

    # Uhrzeit extrahieren
    import re
    time_match = re.search(r"(\d{1,2})[:\.](\d{2})", text)
    if time_match:
        time_part = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
    elif re.search(r"\d{1,2}\s*uhr", text):
        h = re.search(r"(\d{1,2})\s*uhr", text)
        if h:
            time_part = f"{int(h.group(1)):02d}:00"

    # Absolutes Datum
    abs_match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if abs_match:
        base_date = date(int(abs_match.group(3)),
                         int(abs_match.group(2)),
                         int(abs_match.group(1)))

    h, m = map(int, time_part.split(":"))
    return datetime(base_date.year, base_date.month, base_date.day, h, m)


# ── Öffentliche Tool-Funktionen ───────────────────────────────────────────────

def get_calendar_events(days: int = 7) -> str:
    """Liest bevorstehende Termine."""
    try:
        cfg = _get_cfg()
        provider = cfg["provider"]

        if provider == "exchange" or (not provider and cfg["email"] and cfg["password"]):
            try:
                events = _get_events_exchange(days)
            except Exception:
                events = _get_events_caldav(days)
        elif provider == "caldav" or cfg["cal_url"]:
            events = _get_events_caldav(days)
        else:
            return ("Kein Kalender konfiguriert. "
                    "Bitte in den Einstellungen unter KALENDER konfigurieren.")

        if not events:
            return f"Keine Termine in den nächsten {days} Tagen."

        lines = [f"Termine der nächsten {days} Tage:"]
        for e in events:
            loc = f" — {e['location']}" if e["location"] else ""
            lines.append(f"{e['start']} bis {e['end']}: {e['title']}{loc}")
        return " | ".join(lines)

    except Exception as ex:
        return f"Kalender konnte nicht geladen werden: {ex}"


def create_calendar_event(title: str, start: str, end: str = "",
                          location: str = "", description: str = "") -> str:
    """Erstellt einen neuen Termin."""
    try:
        start_dt = _parse_datetime(start)
        if end:
            end_dt = _parse_datetime(end)
        else:
            end_dt = start_dt + timedelta(hours=1)

        if end_dt <= start_dt:
            end_dt = start_dt + timedelta(hours=1)

        cfg = _get_cfg()
        provider = cfg["provider"]

        if provider == "exchange" or (not provider and cfg["email"] and cfg["password"]):
            try:
                return _create_event_exchange(title, start_dt, end_dt, location, description)
            except Exception:
                pass
        if provider == "caldav" or cfg["cal_url"]:
            try:
                return _create_event_caldav(title, start_dt, end_dt, location, description)
            except Exception:
                pass

        # Fallback: ICS-Datei
        return _create_ics_file(title, start_dt, end_dt, location, description)

    except Exception as ex:
        return f"Termin konnte nicht erstellt werden: {ex}"


def get_todays_events() -> str:
    """Gibt alle Termine von heute zurück."""
    try:
        cfg = _get_cfg()
        provider = cfg["provider"]

        if provider == "exchange" or (not provider and cfg["email"] and cfg["password"]):
            try:
                events = _get_events_exchange(days=1)
            except Exception:
                events = _get_events_caldav(days=1)
        elif provider == "caldav" or cfg["cal_url"]:
            events = _get_events_caldav(days=1)
        else:
            return "Kein Kalender konfiguriert."

        today = datetime.now().strftime("%d.%m.%Y")
        today_events = [e for e in events if e["start"].startswith(today)]

        if not today_events:
            return "Heute sind keine Termine eingetragen."

        lines = ["Deine heutigen Termine:"]
        for e in today_events:
            loc = f" ({e['location']})" if e["location"] else ""
            lines.append(f"{e['start'][11:]} Uhr: {e['title']}{loc}")
        return " | ".join(lines)

    except Exception as ex:
        return f"Termine konnten nicht geladen werden: {ex}"
