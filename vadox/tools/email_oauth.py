"""
Microsoft OAuth für Exchange / Office 365
Nutzt Device Code Flow — kein Azure App nötig wenn eigene Client-ID vorhanden.
Speichert den Token in settings damit der Benutzer sich nicht jedes Mal einloggen muss.
"""
import json
import threading
import webbrowser
from pathlib import Path

from vadox.core import settings

# Azure App Registration — der Benutzer trägt seine eigene Client-ID ein
# oder wir nutzen eine vorkonfigurierte Test-App
_DEFAULT_CLIENT_ID = "d659c2a3-29d7-404c-b99e-5e85599cd84e"
_TENANT_ID         = "6ad0aee7-260f-45d5-948a-bbc6fa8720c5"

# Microsoft Graph API Scopes für E-Mail
_SCOPES = [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/User.Read",
    # EWS-Scope als Alternative
    "https://outlook.office.com/EWS.AccessAsUser.All",
]

_TOKEN_CACHE_FILE = Path.home() / ".vadox_ms_token.json"


def get_client_id() -> str:
    saved = settings.load().get("ms_client_id", "").strip()
    return saved if saved else _DEFAULT_CLIENT_ID


def _load_cache() -> dict:
    if _TOKEN_CACHE_FILE.exists():
        try:
            return json.loads(_TOKEN_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_cache(data: dict):
    try:
        _TOKEN_CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_token_silent() -> str | None:
    """Gibt Access Token zurück falls noch gültig (aus Cache)."""
    import msal
    client_id = get_client_id()
    if not client_id:
        return None

    cache = msal.SerializableTokenCache()
    cached = _load_cache()
    if cached:
        cache.deserialize(json.dumps(cached))

    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{_TENANT_ID}",
        token_cache=cache,
    )

    accounts = app.get_accounts()
    if not accounts:
        return None

    result = app.acquire_token_silent(_SCOPES, account=accounts[0])
    if result and "access_token" in result:
        _save_cache(json.loads(cache.serialize()))
        return result["access_token"]
    return None


def login_device_code(on_message=None, on_done=None):
    """
    Startet Device Code Flow im Hintergrund.
    on_message(text): Callback für Status-Updates (Haupt-Thread via QTimer)
    on_done(ok, token_or_error): Callback wenn fertig
    """
    import msal

    client_id = get_client_id()
    if not client_id:
        if on_done:
            on_done(False, "Keine Azure Client-ID eingetragen.\nBitte unter Einstellungen → E-Mail → Azure Client ID eintragen.")
        return

    def _run():
        try:
            cache = msal.SerializableTokenCache()
            app = msal.PublicClientApplication(
                client_id=client_id,
                authority=f"https://login.microsoftonline.com/{_TENANT_ID}",
                token_cache=cache,
            )

            flow = app.initiate_device_flow(scopes=_SCOPES)
            if "user_code" not in flow:
                raise RuntimeError("Device Flow konnte nicht gestartet werden.")

            # Code + URL anzeigen und Browser öffnen
            code = flow["user_code"]
            url  = flow["verification_uri"]
            msg  = f"CODE: {code}\n\nURL: {url}\n\nBrowser öffnet sich automatisch..."
            if on_message:
                on_message(msg)
            # Kurz warten damit UI aktualisiert wird, dann Browser öffnen
            import time; time.sleep(0.5)
            webbrowser.open(url)

            # Warten bis Benutzer sich eingeloggt hat (bis 15 Min)
            result = app.acquire_token_by_device_flow(flow)

            if "access_token" in result:
                _save_cache(json.loads(cache.serialize()))
                token = result["access_token"]
                if on_done:
                    on_done(True, token)
            else:
                err = result.get("error_description", str(result))
                if on_done:
                    on_done(False, f"Login fehlgeschlagen: {err}")

        except Exception as e:
            if on_done:
                on_done(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


def read_emails_graph(count: int = 5, unread_only: bool = False) -> str:
    """E-Mails lesen via Microsoft Graph API (OAuth)."""
    import requests

    token = get_token_silent()
    if not token:
        return "Nicht eingeloggt. Bitte in Einstellungen → E-Mail → Microsoft Login klicken."

    url    = "https://graph.microsoft.com/v1.0/me/messages"
    params = {
        "$top":     count,
        "$orderby": "receivedDateTime desc",
        "$select":  "subject,from,receivedDateTime,bodyPreview,isRead",
    }
    if unread_only:
        params["$filter"] = "isRead eq false"

    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    r.raise_for_status()

    msgs = r.json().get("value", [])
    if not msgs:
        return "Keine E-Mails gefunden."

    summaries = []
    for m in msgs:
        sender  = m.get("from", {}).get("emailAddress", {}).get("address", "?")
        subject = m.get("subject", "(kein Betreff)")
        date    = m.get("receivedDateTime", "")[:16]
        preview = m.get("bodyPreview", "")[:120]
        summaries.append(f"Von: {sender} | Betreff: {subject} | Datum: {date} | Vorschau: {preview}")

    label = "ungelesene " if unread_only else ""
    return f"Die letzten {len(summaries)} {label}E-Mails: " + " || ".join(summaries)


def send_email_graph(to: str, subject: str, body: str) -> str:
    """E-Mail senden via Microsoft Graph API (OAuth)."""
    import requests

    token = get_token_silent()
    if not token:
        return "Nicht eingeloggt. Bitte in Einstellungen → E-Mail → Microsoft Login klicken."

    url     = "https://graph.microsoft.com/v1.0/me/sendMail"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "message": {
            "subject": subject,
            "body":    {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": to}}],
        }
    }
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    if r.status_code == 202:
        return f"E-Mail erfolgreich gesendet an {to}"
    r.raise_for_status()
    return f"Fehler: {r.status_code} {r.text[:200]}"


def get_unread_count_graph() -> str:
    """Ungelesene E-Mails zählen via Graph API."""
    import requests

    token = get_token_silent()
    if not token:
        return "Nicht eingeloggt. Bitte Microsoft Login in Einstellungen klicken."

    url     = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    count = r.json().get("unreadItemCount", 0)
    return f"Du hast {count} ungelesene E-Mails im Posteingang."


def is_logged_in() -> bool:
    return get_token_silent() is not None


def logout():
    """Token-Cache löschen."""
    if _TOKEN_CACHE_FILE.exists():
        _TOKEN_CACHE_FILE.unlink()
