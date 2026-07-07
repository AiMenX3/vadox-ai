"""
Telegram Bot — Vadox sendet Nachrichten aufs Handy.
Benötigt: Bot-Token von @BotFather + eigene Chat-ID.
"""
import requests


def _get_config() -> tuple[str, str]:
    try:
        from vadox.core import settings
        cfg = settings.load()
        return cfg.get("telegram_token", ""), cfg.get("telegram_chat_id", "")
    except Exception:
        return "", ""


def send_telegram(message: str, token: str = "", chat_id: str = "") -> str:
    """Sendet eine Nachricht via Telegram an den konfigurierten Chat."""
    if not token or not chat_id:
        token, chat_id = _get_config()
    if not token:
        return "Telegram nicht eingerichtet. Bitte Token und Chat-ID in den Einstellungen eintragen."
    if not chat_id:
        return "Telegram Chat-ID fehlt. Schreibe deinem Bot eine Nachricht und rufe /get_my_id ab."

    try:
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        r    = requests.post(url, json=data, timeout=10)
        if r.status_code == 200:
            return f"Telegram-Nachricht gesendet: {message[:80]}"
        return f"Telegram-Fehler {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Telegram-Verbindungsfehler: {e}"


def send_telegram_photo(image_path: str, caption: str = "") -> str:
    """Sendet ein Foto via Telegram."""
    token, chat_id = _get_config()
    if not token or not chat_id:
        return "Telegram nicht eingerichtet."
    try:
        url  = f"https://api.telegram.org/bot{token}/sendPhoto"
        with open(image_path, "rb") as f:
            r = requests.post(url, data={"chat_id": chat_id, "caption": caption},
                              files={"photo": f}, timeout=15)
        if r.status_code == 200:
            return f"Foto gesendet via Telegram."
        return f"Telegram-Fehler: {r.text[:200]}"
    except Exception as e:
        return f"Fehler: {e}"


def get_telegram_updates() -> str:
    """Prüft ob neue Nachrichten vom Nutzer an den Bot eingegangen sind."""
    token, _ = _get_config()
    if not token:
        return "Telegram nicht eingerichtet."
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        r   = requests.get(url, timeout=8)
        if r.status_code != 200:
            return f"Fehler: {r.text[:100]}"
        updates = r.json().get("result", [])
        if not updates:
            return "Keine neuen Telegram-Nachrichten."
        lines = ["Telegram-Nachrichten:"]
        for u in updates[-5:]:
            msg = u.get("message", {})
            text    = msg.get("text", "")
            sender  = msg.get("from", {}).get("first_name", "?")
            chat_id = msg.get("chat", {}).get("id", "")
            lines.append(f"  Von {sender} (ID: {chat_id}): {text}")
        return "\n".join(lines)
    except Exception as e:
        return f"Fehler: {e}"


def get_my_chat_id() -> str:
    """Gibt die Chat-ID des letzten Absenders zurück — zum Einrichten."""
    token, _ = _get_config()
    if not token:
        return "Bitte zuerst den Telegram Bot-Token in den Einstellungen eintragen."
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        r   = requests.get(url, timeout=8)
        updates = r.json().get("result", [])
        if not updates:
            return "Keine Nachrichten gefunden. Schreibe deinem Bot eine Nachricht (z.B. /start) und versuche es nochmal."
        last = updates[-1].get("message", {})
        chat_id  = last.get("chat", {}).get("id", "")
        name     = last.get("from", {}).get("first_name", "?")
        return f"Deine Telegram Chat-ID: {chat_id} (Name: {name}). Trage diese ID in die Einstellungen ein."
    except Exception as e:
        return f"Fehler: {e}"
