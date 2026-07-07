import imaplib
import smtplib
import email
import socket
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from vadox.core import settings


PROVIDERS = {
    "gmail":    {"imap": "imap.gmail.com",              "smtp": "smtp.gmail.com",          "port": 587},
    "outlook":  {"imap": "imap-mail.outlook.com",       "smtp": "smtp-mail.outlook.com",   "port": 587},
    "hotmail":  {"imap": "imap-mail.outlook.com",       "smtp": "smtp-mail.outlook.com",   "port": 587},
    "yahoo":    {"imap": "imap.mail.yahoo.com",         "smtp": "smtp.mail.yahoo.com",     "port": 587},
    "web.de":   {"imap": "imap.web.de",                 "smtp": "smtp.web.de",             "port": 587},
    "gmx":      {"imap": "imap.gmx.net",                "smtp": "smtp.gmx.net",            "port": 587},
    "t-online": {"imap": "secureimap.t-online.de",      "smtp": "securesmtp.t-online.de",  "port": 587},
    # Exchange IMAP-Fallback
    "o365":     {"imap": "outlook.office365.com",       "smtp": "smtp.office365.com",      "port": 587},
}

# Exchange IMAP-Server-Muster (wird aus E-Mail-Domain abgeleitet)
_EXCHANGE_IMAP_PATTERNS = [
    "outlook.office365.com",          # Office 365 (Firmenkonten)
    "imap-mail.outlook.com",          # Persönliches Outlook/Hotmail
    "mail.{domain}",
    "webmail.{domain}",
    "owa.{domain}",
    "exchange.{domain}",
    "imap.{domain}",
]


def _get_credentials() -> tuple[str, str, str]:
    cfg = settings.load()
    return (
        cfg.get("email_address", ""),
        cfg.get("email_password", ""),
        cfg.get("email_provider", "gmail"),
    )


def _is_exchange() -> bool:
    return settings.load().get("email_provider", "") == "exchange"


# ── Exchange via EWS (exchangelib) ────────────────────────────────────────────

def _exchange_via_ews(addr: str, pwd: str, server: str = "") -> object:
    """
    Versucht EWS-Verbindung mit allen gängigen Username-Formaten und Auth-Methoden.
    Leitet Windows-Domain automatisch aus dem Server-Hostnamen ab.
    """
    from exchangelib import (
        Credentials, Account, DELEGATE, Configuration, NTLM, BASIC
    )
    from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter

    email_domain   = addr.split("@")[1] if "@" in addr else ""
    username_short = addr.split("@")[0]
    socket.setdefaulttimeout(15)
    errors = []

    # Windows-Domain aus Server ableiten wenn nicht angegeben
    # z.B. mxch.gvtruck.net  →  GVTRUCK  oder  gvtruck
    auto_domain = ""
    if server:
        parts = server.replace("https://", "").replace("http://", "").split(".")
        if len(parts) >= 2:
            auto_domain = parts[-2].upper()   # "gvtruck" aus "mxch.gvtruck.net"

    # Alle Username-Varianten die wir probieren
    usernames = [
        addr,                                          # max@firma.de  (Office 365)
        username_short,                                # max
    ]
    if auto_domain:
        usernames.insert(1, f"{auto_domain}\\{username_short}")   # GVTRUCK\max
        usernames.insert(2, f"{auto_domain.lower()}\\{username_short}")  # gvtruck\max

    # EWS-URLs (server zuerst, dann Fallbacks)
    ews_urls = []
    if server:
        base = server if server.startswith("http") else f"https://{server}"
        base = base.rstrip("/")
        ews_urls.append(f"{base}/EWS/Exchange.asmx")
        # Auch HTTP versuchen (manche Firmen-Server ohne SSL intern)
        http_base = base.replace("https://", "http://")
        ews_urls.append(f"{http_base}/EWS/Exchange.asmx")
    ews_urls += [
        f"https://outlook.office365.com/EWS/Exchange.asmx",
        f"https://mail.{email_domain}/EWS/Exchange.asmx",
        f"https://webmail.{email_domain}/EWS/Exchange.asmx",
        f"https://owa.{email_domain}/EWS/Exchange.asmx",
    ]

    def _try(creds, config=None, autodiscover=False):
        if autodiscover:
            acc = Account(primary_smtp_address=addr, credentials=creds,
                          autodiscover=True, access_type=DELEGATE)
        else:
            acc = Account(primary_smtp_address=addr, config=config,
                          access_type=DELEGATE)
        _ = acc.inbox.total_count
        return acc

    # ── Runde 1: Mit SSL-Verifizierung ────────────────────────────
    # Erst explizite URLs (server steht zuerst), dann Autodiscover
    for url in ews_urls:
        for uname in usernames:
            for auth in (NTLM, BASIC):
                try:
                    creds  = Credentials(username=uname, password=pwd)
                    config = Configuration(service_endpoint=url,
                                           credentials=creds, auth_type=auth)
                    return _try(creds, config=config)
                except Exception as e:
                    errors.append(f"[{auth.__name__ if hasattr(auth,'__name__') else auth}] {url} | {uname}: {e}")

    # Autodiscover als letzter Versuch mit SSL
    for uname in usernames:
        try:
            creds = Credentials(username=uname, password=pwd)
            return _try(creds, autodiscover=True)
        except Exception as e:
            errors.append(f"[Autodiscover] {uname}: {e}")

    # ── Runde 2: Ohne SSL-Verifizierung (selbstsignierte Zertifikate) ─
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter

        for url in ews_urls[:4]:     # nur die wichtigsten URLs
            for uname in usernames:
                for auth in (NTLM, BASIC):
                    try:
                        creds  = Credentials(username=uname, password=pwd)
                        config = Configuration(service_endpoint=url,
                                               credentials=creds, auth_type=auth)
                        return _try(creds, config=config)
                    except Exception as e:
                        errors.append(f"[NoSSL/{auth}] {url} | {uname}: {e}")

        for uname in usernames:
            try:
                creds = Credentials(username=uname, password=pwd)
                return _try(creds, autodiscover=True)
            except Exception as e:
                errors.append(f"[NoSSL/Autodiscover] {uname}: {e}")
    finally:
        try:
            from requests.adapters import HTTPAdapter
            BaseProtocol.HTTP_ADAPTER_CLS = HTTPAdapter
        except Exception:
            pass

    raise ConnectionError("\n".join(errors[-8:]))


# ── Exchange via IMAP (Fallback) ─────────────────────────────────────────────

def _exchange_via_imap(addr: str, pwd: str, server: str = "") -> imaplib.IMAP4_SSL:
    """
    IMAP-Fallback für Exchange/Office 365.
    Funktioniert wenn EWS gesperrt ist aber IMAP erlaubt ist.
    Genau das gleiche Protokoll das viele E-Mail-Apps (auch iPhone) nutzen.
    """
    email_domain = addr.split("@")[1] if "@" in addr else ""
    socket.setdefaulttimeout(12)

    servers_to_try = []
    if server:
        servers_to_try.append(server)
    servers_to_try += [
        "outlook.office365.com",          # Office 365 Firmenkonten
        "imap-mail.outlook.com",          # Persönliches Outlook
        f"mail.{email_domain}",
        f"webmail.{email_domain}",
        f"owa.{email_domain}",
        f"imap.{email_domain}",
    ]

    errors = []
    for host in servers_to_try:
        try:
            mail = imaplib.IMAP4_SSL(host, 993)
            mail.login(addr, pwd)
            mail.select("INBOX")
            return mail
        except Exception as e:
            errors.append(f"{host}: {e}")

    raise ConnectionError(
        f"IMAP-Fallback fehlgeschlagen.\nVersuche: {', '.join(servers_to_try[:4])}\n"
        f"Letzter Fehler: {errors[-1] if errors else '?'}"
    )


# ── Haupt-Verbindungsfunktion ─────────────────────────────────────────────────

def _exchange_connect():
    """
    Verbindet mit Exchange — versucht zuerst EWS, dann IMAP.
    Gibt zurück: ('ews', account) oder ('imap', mail_connection)
    """
    cfg    = settings.load()
    addr   = cfg.get("email_address", "")
    pwd    = cfg.get("email_password", "")
    server = cfg.get("exchange_server", "").strip()

    if not addr or not pwd:
        raise ValueError("Keine E-Mail-Zugangsdaten hinterlegt.")

    ews_error  = None
    imap_error = None

    # Erst EWS versuchen
    try:
        acc = _exchange_via_ews(addr, pwd, server)
        return ("ews", acc)
    except Exception as e:
        ews_error = str(e)

    # Dann IMAP-Fallback
    try:
        mail = _exchange_via_imap(addr, pwd, server)
        return ("imap", mail)
    except Exception as e:
        imap_error = str(e)

    # Beide fehlgeschlagen
    raise ConnectionError(
        f"Verbindung fehlgeschlagen.\n\n"
        f"EWS: {ews_error[:200] if ews_error else '?'}\n\n"
        f"IMAP: {imap_error[:200] if imap_error else '?'}\n\n"
        f"Tipps:\n"
        f"• Exchange Server-URL in Einstellungen eintragen (z.B. mail.firma.de)\n"
        f"• VPN prüfen — manche Firmen erlauben nur internen Zugriff\n"
        f"• Für Office 365: Oft ist ein App-Passwort nötig\n"
        f"  → account.microsoft.com → Sicherheit → App-Kennwörter"
    )


# ── Exchange: Lesen ───────────────────────────────────────────────────────────

def _exchange_read(count: int = 5, unread_only: bool = False) -> str:
    try:
        mode, conn = _exchange_connect()

        if mode == "ews":
            inbox = conn.inbox
            items = inbox.filter(is_read=False) if unread_only else inbox.all()
            items = items.order_by("-datetime_received")[:count]
            summaries = []
            for msg in items:
                body = ""
                if msg.text_body:
                    body = msg.text_body[:150].replace("\n", " ").strip()
                elif msg.body:
                    body = str(msg.body)[:150].replace("\n", " ").strip()
                sender = str(msg.sender.email_address) if msg.sender else "Unbekannt"
                summaries.append(
                    f"Von: {sender} | Betreff: {msg.subject} "
                    f"| Datum: {str(msg.datetime_received)[:16]} | Vorschau: {body}"
                )
            label = "ungelesene " if unread_only else ""
            return f"Die letzten {len(summaries)} {label}E-Mails: " + " || ".join(summaries) if summaries else "Keine E-Mails gefunden."

        else:  # IMAP-Fallback
            criteria = "UNSEEN" if unread_only else "ALL"
            _, ids = conn.search(None, criteria)
            id_list = ids[0].split()
            if not id_list:
                conn.logout()
                return "Keine E-Mails gefunden."
            recent = id_list[-count:][::-1]
            summaries = []
            for mid in recent:
                _, data = conn.fetch(mid, "(RFC822)")
                msg     = email.message_from_bytes(data[0][1])
                subject = _decode_str(msg.get("Subject", "(kein Betreff)"))
                sender  = _decode_str(msg.get("From", "Unbekannt"))
                date    = _decode_str(msg.get("Date", ""))[:25]
                body    = _get_body(msg)
                summaries.append(f"Von: {sender} | Betreff: {subject} | Datum: {date} | Vorschau: {body[:120]}")
            conn.logout()
            label = "ungelesene " if unread_only else ""
            return f"Die letzten {len(summaries)} {label}E-Mails (via IMAP): " + " || ".join(summaries)

    except Exception as e:
        return f"Exchange Fehler: {e}"


# ── Exchange: Senden ──────────────────────────────────────────────────────────

def _exchange_send(to: str, subject: str, body: str) -> str:
    try:
        cfg    = settings.load()
        addr   = cfg.get("email_address", "")
        pwd    = cfg.get("email_password", "")
        server = cfg.get("exchange_server", "").strip()
        email_domain = addr.split("@")[1] if "@" in addr else ""

        mode, conn = _exchange_connect()

        if mode == "ews":
            from exchangelib import Message, Mailbox
            msg = Message(
                account=conn,
                folder=conn.sent,
                subject=subject,
                body=body,
                to_recipients=[Mailbox(email_address=to)],
            )
            msg.send_and_save()
            return f"E-Mail erfolgreich gesendet an {to}"

        else:
            conn.logout()
            # SMTP für Senden
            smtp_servers = []
            if server:
                smtp_servers.append((server, 587))
                smtp_servers.append((server, 25))
            smtp_servers += [
                ("smtp.office365.com",      587),
                ("smtp-mail.outlook.com",   587),
                (f"mail.{email_domain}",    587),
                (f"smtp.{email_domain}",    587),
            ]
            last_err = ""
            for host, port in smtp_servers:
                try:
                    msg_obj = MIMEMultipart()
                    msg_obj["From"]    = addr
                    msg_obj["To"]      = to
                    msg_obj["Subject"] = subject
                    msg_obj.attach(MIMEText(body, "plain", "utf-8"))
                    with smtplib.SMTP(host, port, timeout=12) as s:
                        s.starttls()
                        s.login(addr, pwd)
                        s.send_message(msg_obj)
                    return f"E-Mail erfolgreich gesendet an {to} (via {host})"
                except Exception as e:
                    last_err = str(e)
            return f"SMTP senden fehlgeschlagen: {last_err}"

    except Exception as e:
        return f"Exchange Senden fehlgeschlagen: {e}"


def _exchange_unread_count() -> str:
    try:
        mode, conn = _exchange_connect()
        if mode == "ews":
            count = conn.inbox.filter(is_read=False).count()
        else:
            conn.select("INBOX")
            _, ids = conn.search(None, "UNSEEN")
            count = len(ids[0].split()) if ids[0] else 0
            conn.logout()
        return f"Du hast {count} ungelesene E-Mails in deinem Posteingang."
    except Exception as e:
        return f"Exchange Fehler: {e}"


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _decode_str(s) -> str:
    if s is None:
        return ""
    if isinstance(s, str):
        return s
    parts  = decode_header(s)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="ignore"))
        else:
            result.append(str(part))
    return " ".join(result)


def _get_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode("utf-8", errors="ignore")[:200]
                except Exception:
                    pass
    try:
        return msg.get_payload(decode=True).decode("utf-8", errors="ignore")[:200]
    except Exception:
        return ""


def _connect_imap(email_addr, email_pass, provider_key):
    cfg  = PROVIDERS.get(provider_key, PROVIDERS["gmail"])
    mail = imaplib.IMAP4_SSL(cfg["imap"])
    mail.login(email_addr, email_pass)
    return mail


# ── Öffentliche Funktionen ────────────────────────────────────────────────────

def read_emails(count: int = 5, folder: str = "INBOX", unread_only: bool = False) -> str:
    if _is_exchange():
        try:
            from vadox.tools.email_oauth import is_logged_in, read_emails_graph
            if is_logged_in():
                return read_emails_graph(count, unread_only)
        except Exception:
            pass
        return _exchange_read(count, unread_only)

    try:
        addr, pwd, prov = _get_credentials()
        if not addr or not pwd:
            return "Keine E-Mail-Zugangsdaten hinterlegt. Bitte in den Einstellungen konfigurieren."

        mail = _connect_imap(addr, pwd, prov)
        mail.select(folder)

        criteria = "UNSEEN" if unread_only else "ALL"
        _, msg_ids = mail.search(None, criteria)
        ids = msg_ids[0].split()
        if not ids:
            return "Keine E-Mails gefunden."

        recent    = ids[-count:][::-1]
        summaries = []
        for mid in recent:
            _, data = mail.fetch(mid, "(RFC822)")
            msg     = email.message_from_bytes(data[0][1])
            subject = _decode_str(msg.get("Subject", "(kein Betreff)"))
            sender  = _decode_str(msg.get("From", "Unbekannt"))
            date    = _decode_str(msg.get("Date", ""))[:25]
            body    = _get_body(msg)
            summaries.append(
                f"Von: {sender} | Betreff: {subject} | Datum: {date} | Vorschau: {body.strip()[:120]}"
            )

        mail.logout()
        label = "ungelesene " if unread_only else ""
        return f"Die letzten {len(summaries)} {label}E-Mails: " + " || ".join(summaries)

    except imaplib.IMAP4.error as e:
        return f"IMAP Fehler: {e}. Tipp: Bei Gmail App-Passwort unter myaccount.google.com/apppasswords erstellen."
    except Exception as e:
        return f"E-Mail lesen fehlgeschlagen: {e}"


def send_email(to: str, subject: str, body: str) -> str:
    if _is_exchange():
        try:
            from vadox.tools.email_oauth import is_logged_in, send_email_graph
            if is_logged_in():
                return send_email_graph(to, subject, body)
        except Exception:
            pass
        return _exchange_send(to, subject, body)

    try:
        addr, pwd, prov = _get_credentials()
        if not addr or not pwd:
            return "Keine E-Mail-Zugangsdaten hinterlegt."

        cfg = PROVIDERS.get(prov, PROVIDERS["gmail"])
        msg = MIMEMultipart()
        msg["From"]    = addr
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(cfg["smtp"], cfg["port"]) as server:
            server.starttls()
            server.login(addr, pwd)
            server.send_message(msg)

        return f"E-Mail erfolgreich gesendet an {to} mit Betreff: {subject}"
    except Exception as e:
        return f"E-Mail senden fehlgeschlagen: {e}"


def search_emails(keyword: str, count: int = 5) -> str:
    try:
        addr, pwd, prov = _get_credentials()
        if not addr or not pwd:
            return "Keine E-Mail-Zugangsdaten hinterlegt."

        mail = _connect_imap(addr, pwd, prov)
        mail.select("INBOX")
        _, msg_ids = mail.search(None, f'SUBJECT "{keyword}"')
        ids = msg_ids[0].split()
        if not ids:
            _, msg_ids = mail.search(None, f'BODY "{keyword}"')
            ids = msg_ids[0].split()
        if not ids:
            return f"Keine E-Mails mit '{keyword}' gefunden."

        recent    = ids[-count:][::-1]
        summaries = []
        for mid in recent:
            _, data = mail.fetch(mid, "(RFC822)")
            msg     = email.message_from_bytes(data[0][1])
            subject = _decode_str(msg.get("Subject", "(kein Betreff)"))
            sender  = _decode_str(msg.get("From", "Unbekannt"))
            summaries.append(f"Von: {sender} | Betreff: {subject}")

        mail.logout()
        return f"Gefundene E-Mails zu '{keyword}': " + " || ".join(summaries)
    except Exception as e:
        return f"E-Mail Suche fehlgeschlagen: {e}"


def get_unread_count() -> str:
    if _is_exchange():
        try:
            from vadox.tools.email_oauth import is_logged_in, get_unread_count_graph
            if is_logged_in():
                return get_unread_count_graph()
        except Exception:
            pass
        return _exchange_unread_count()

    try:
        addr, pwd, prov = _get_credentials()
        if not addr or not pwd:
            return "Keine E-Mail-Zugangsdaten hinterlegt."

        mail = _connect_imap(addr, pwd, prov)
        mail.select("INBOX")
        _, ids = mail.search(None, "UNSEEN")
        count = len(ids[0].split()) if ids[0] else 0
        mail.logout()
        return f"Du hast {count} ungelesene E-Mails in deinem Posteingang."
    except Exception as e:
        return f"Ungelesene E-Mails konnten nicht abgerufen werden: {e}"


def move_email_to_folder(subject_keyword: str, target_folder: str) -> str:
    try:
        addr, pwd, prov = _get_credentials()
        if not addr or not pwd:
            return "Keine E-Mail-Zugangsdaten hinterlegt."

        mail = _connect_imap(addr, pwd, prov)
        mail.select("INBOX")
        _, ids = mail.search(None, f'SUBJECT "{subject_keyword}"')
        moved = 0
        for mid in ids[0].split():
            mail.copy(mid, target_folder)
            mail.store(mid, "+FLAGS", "\\Deleted")
            moved += 1
        mail.expunge()
        mail.logout()
        return f"{moved} E-Mail(s) verschoben nach '{target_folder}'."
    except Exception as e:
        return f"Verschieben fehlgeschlagen: {e}"
