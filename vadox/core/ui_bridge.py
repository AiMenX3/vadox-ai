"""
UI-Bridge
---------
Ermoeglicht Tools (die im Hintergrund-Thread laufen), UI-Aktionen im
Haupt-Thread auszuloesen — ohne dass die Tools das Fenster direkt kennen.

Das Hauptfenster registriert beim Start Handler, die intern ein Qt-Signal
emittieren (Qt marshallt das automatisch sicher in den Haupt-Thread).
"""

_webcam_opener = None


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
