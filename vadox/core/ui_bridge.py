"""
UI-Bridge
---------
Ermoeglicht Tools (die im Hintergrund-Thread laufen), UI-Aktionen im
Haupt-Thread auszuloesen — ohne dass die Tools das Fenster direkt kennen.

Das Hauptfenster registriert beim Start Handler, die intern ein Qt-Signal
emittieren (Qt marshallt das automatisch sicher in den Haupt-Thread).
"""

_webcam_opener = None
_coding_opener = None


def set_webcam_opener(fn):
    """Vom Hauptfenster aufgerufen. fn(city: str) oeffnet das Webcam-Panel."""
    global _webcam_opener
    _webcam_opener = fn


def open_webcams(city: str = "") -> bool:
    """Von einem Tool aufgerufen. Gibt True zurueck, wenn ein Handler
    registriert ist (also die GUI laeuft)."""
    if _webcam_opener is None:
        return False
    _webcam_opener(city)
    return True


def set_coding_opener(fn):
    """Vom Hauptfenster aufgerufen. fn(task: str, language: str) oeffnet das
    Coding-Panel und startet die Code-Generierung."""
    global _coding_opener
    _coding_opener = fn


def open_coding(task: str = "", language: str = "") -> bool:
    if _coding_opener is None:
        return False
    _coding_opener(task, language)
    return True
