"""
WhatsApp Tool — sendet Nachrichten über WhatsApp Web via Browser-Automation.
Kein API-Key nötig. WhatsApp Web muss einmalig im Browser eingeloggt sein.
"""
import time
import webbrowser
import urllib.parse


def send_whatsapp(contact: str, message: str, wait: int = 15) -> str:
    """
    Sendet eine WhatsApp-Nachricht an einen Kontakt oder eine Nummer.

    contact: Name oder Telefonnummer mit Ländervorwahl (z.B. +4917612345678)
    message: Text der gesendet werden soll
    wait:    Sekunden die WhatsApp Web zum Laden hat (Standard: 15)
    """
    try:
        # Nummer bereinigen
        phone = contact.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

        # Falls es kein '+' gibt aber mit 0 anfängt → deutsche Nummer
        if phone.startswith("0") and not phone.startswith("+"):
            phone = "+49" + phone[1:]

        # Falls es eine reine Zahl ohne + ist
        if phone.isdigit() and len(phone) > 6:
            phone = "+" + phone

        if not phone.startswith("+"):
            # Kein Nummer-Format → versuche als Name über WhatsApp Web Suche
            return _send_by_name(contact, message, wait)

        # WhatsApp Web direkt-Link mit vorausgefüllter Nachricht
        encoded_msg = urllib.parse.quote(message)
        url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}&app_absent=0"

        webbrowser.open(url)
        return (
            f"WhatsApp Web wird geöffnet für {contact}.\n"
            f"Bitte auf 'Senden' klicken wenn der Chat geladen ist.\n"
            f"Nachricht: '{message}'"
        )

    except Exception as e:
        return f"WhatsApp Fehler: {e}"


def _send_by_name(name: str, message: str, wait: int = 15) -> str:
    """Öffnet WhatsApp Web und sucht den Kontaktnamen."""
    encoded_msg = urllib.parse.quote(message)
    # Direkt-URL ohne Nummer öffnet WhatsApp Web Hauptseite
    webbrowser.open("https://web.whatsapp.com")
    return (
        f"WhatsApp Web geöffnet.\n"
        f"Suche '{name}' im Suchfeld und sende die Nachricht:\n"
        f"'{message}'\n\n"
        f"Tipp: Gib beim nächsten Mal die Telefonnummer an für automatisches Senden."
    )


def send_whatsapp_now(phone: str, message: str) -> str:
    """
    Sendet WhatsApp sofort via pywhatkit (öffnet Browser + sendet automatisch).
    phone: Telefonnummer mit Ländervorwahl, z.B. +4917612345678
    """
    try:
        import pywhatkit as kit

        # Nummer bereinigen
        phone = phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("0"):
            phone = "+49" + phone[1:]
        if not phone.startswith("+"):
            phone = "+" + phone

        # Sofort senden (0 Minuten Verzögerung, 10 Sek zum Laden)
        kit.sendwhatmsg_instantly(
            phone_no=phone,
            message=message,
            wait_time=12,
            tab_close=True,
            close_time=3,
        )
        return f"WhatsApp-Nachricht an {phone} gesendet: '{message}'"

    except Exception as e:
        # Fallback: einfacher Link
        return send_whatsapp(phone, message)


def get_whatsapp_status() -> str:
    """Öffnet WhatsApp Web um Status zu sehen."""
    webbrowser.open("https://web.whatsapp.com")
    return "WhatsApp Web wurde geöffnet."
