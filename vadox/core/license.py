"""
Vadox Lizenz-System
-------------------
Pakete:
  TRIAL    — 24 Stunden kostenlos (ab erstem Start)
  PRO      — 197€ Lifetime
  MONTH    — 67€ / 30 Tage
  BUSINESS — 1.497€ Lifetime + Source Code + Branding

Keys:
  VADOX-... → gegen den Vadox-Lizenz-Server geprüft (server/vadox-license-worker/).
              Das Signier-Secret liegt NUR dort, nie in diesem (öffentlichen) Repo.
  Gumroad-Keys (XXXX-XXXX-XXXX-XXXX) → online gegen Gumroad API geprüft (Legacy,
              aktuell ungenutzt — Verkauf läuft über Stripe)
"""

import hashlib
import hmac
import json
import socket
import os
from pathlib import Path
from datetime import datetime, timedelta

# ── Konfiguration ─────────────────────────────────────────────────────────────

# Gumroad Produkt-Permalinks — Legacy, aktuell ungenutzt (Verkauf laeuft ueber Stripe)
GUMROAD_PRO_ID      = os.environ.get("VADOX_GUMROAD_PRO",      "vadox-pro")
GUMROAD_BUSINESS_ID = os.environ.get("VADOX_GUMROAD_BUSINESS",  "vadox-business")

# Lizenz-Server (Cloudflare Worker, siehe server/vadox-license-worker/) —
# prueft VADOX-...-Keys serverseitig und erstellt dynamische Stripe-Checkout-Links.
# Das HMAC-Signier-Secret lebt ausschliesslich dort, nie in diesem Repo.
LICENSE_SERVER_URL = os.environ.get(
    "VADOX_LICENSE_SERVER_URL", "https://vadox-license.krivonosvadim995.workers.dev"
)

LICENSE_PATH = Path.home() / ".vadox" / "license.json"
TRIAL_PATH   = Path.home() / ".vadox" / "trial.json"

KEY_TYPES = {
    "TRIAL":    {"label": "Trial (24h)",      "days": 0},
    "MONTH":    {"label": "1 Monat",          "days": 30},
    "PRO":      {"label": "PRO Lifetime",     "days": 36500},
    "BUSINESS": {"label": "Business Lifetime","days": 36500},
}


# ── Machine ID ────────────────────────────────────────────────────────────────

def _machine_id() -> str:
    try:
        import uuid
        mac  = str(uuid.getnode())
        host = socket.gethostname()
        return hashlib.sha256(f"{host}-{mac}".encode()).hexdigest()[:16].upper()
    except Exception:
        return "UNKNOWN"


# ── Trial ─────────────────────────────────────────────────────────────────────

def start_trial() -> dict:
    """Startet den 24h Trial beim ersten Programmstart. Gibt Trial-Info zurück."""
    TRIAL_PATH.parent.mkdir(parents=True, exist_ok=True)

    if TRIAL_PATH.exists():
        return json.loads(TRIAL_PATH.read_text(encoding="utf-8"))

    data = {
        "started":    datetime.now().isoformat(),
        "expires":    (datetime.now() + timedelta(hours=24)).isoformat(),
        "machine_id": _machine_id(),
    }
    TRIAL_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def get_trial_info() -> dict:
    """Gibt Trial-Status zurück: active, seconds_left, expired."""
    if not TRIAL_PATH.exists():
        return {"active": False, "expired": False, "seconds_left": 0}

    try:
        data    = json.loads(TRIAL_PATH.read_text(encoding="utf-8"))
        expires = datetime.fromisoformat(data["expires"])
        now     = datetime.now()

        if now >= expires:
            return {"active": False, "expired": True, "seconds_left": 0}

        seconds_left = int((expires - now).total_seconds())
        return {
            "active":       True,
            "expired":      False,
            "seconds_left": seconds_left,
            "expires":      expires.isoformat(),
        }
    except Exception:
        return {"active": False, "expired": True, "seconds_left": 0}


# ── Entwickler-Testkeys (nur fuer dich selbst, kein Kundenpfad) ───────────────

def generate_key(customer_email: str = "", key_type: str = "PRO") -> str:
    """
    Generiert einen HMAC-signierten Test-Lizenzschlüssel für die lokale
    Entwicklung (genutzt von generate_key.py). Braucht VADOX_DEV_SECRET als
    Umgebungsvariable — echte Kunden-Keys werden ausschliesslich vom
    Lizenz-Server ausgestellt (server/vadox-license-worker/), nicht hier.
    key_type: MONTH, PRO oder BUSINESS
    Format: VADOX-XXXX-XXXX-XXXX-XXXX-META
    """
    import base64
    secret = os.environ.get("VADOX_DEV_SECRET", "")
    if not secret:
        raise RuntimeError(
            "VADOX_DEV_SECRET nicht gesetzt. Für lokale Test-Keys z.B.:\n"
            "  export VADOX_DEV_SECRET=<dein-dev-secret>\n"
            "Echte Kunden-Keys werden ueber den Lizenz-Server ausgestellt."
        )
    days     = KEY_TYPES.get(key_type.upper(), {}).get("days", 36500)
    expiry   = (datetime.now() + timedelta(days=days)).strftime("%Y%m%d")
    payload  = f"{expiry}|{key_type.upper()}|{customer_email.lower()}"

    sig = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest().upper()

    key_body = f"{sig[0:4]}-{sig[4:8]}-{sig[8:12]}-{sig[12:16]}"
    meta     = base64.b32encode(payload.encode()).decode().rstrip("=")

    return f"VADOX-{key_body}-{meta}"


# ── Serverseitige Key-Verifikation ────────────────────────────────────────────

def _verify_remote_key(key: str) -> tuple[bool, dict]:
    """Prüft einen VADOX-...-Key gegen den Lizenz-Server statt lokal per HMAC —
    das Signier-Secret liegt so nie im (öffentlichen) Client-Code."""
    try:
        import requests
        r = requests.post(
            f"{LICENSE_SERVER_URL}/verify",
            json={"key": key.strip()},
            timeout=10,
        )
        data = r.json()
        if not data.get("valid"):
            return False, {"error": data.get("error", "Ungültiger Key")}
        return True, {
            "type":      data.get("type", "PRO"),
            "expiry":    data.get("expiry", ""),
            "days_left": data.get("days_left", 0),
            "source":    "server",
            "email":     data.get("email", ""),
        }
    except Exception as e:
        if "ConnectionError" in type(e).__name__ or "ConnectTimeout" in type(e).__name__ or "Timeout" in type(e).__name__:
            return False, {"error": "no_internet"}
        return False, {"error": str(e)}


def start_checkout(plan: str) -> str | None:
    """Fordert eine dynamische Stripe-Checkout-URL vom Lizenz-Server an.
    plan: 'pro' oder 'month'. Gibt None zurück, wenn der Server nicht
    erreichbar ist (z.B. kein Internet)."""
    try:
        import requests
        r = requests.post(
            f"{LICENSE_SERVER_URL}/checkout",
            json={"plan": plan},
            timeout=10,
        )
        data = r.json()
        return data.get("url")
    except Exception:
        return None


# ── Gumroad Online-Verifikation ───────────────────────────────────────────────

def _verify_gumroad(key: str, product_id: str) -> tuple[bool, dict]:
    try:
        import requests
        r = requests.post(
            "https://api.gumroad.com/v2/licenses/verify",
            data={
                "product_permalink":    product_id,
                "license_key":          key.strip(),
                "increment_uses_count": "false",
            },
            timeout=10,
        )
        data = r.json()

        if not data.get("success"):
            return False, {"error": data.get("message", "Ungültiger Key")}

        purchase   = data.get("purchase", {})
        created    = purchase.get("created_at", "")
        email      = purchase.get("email", "")
        refunded   = purchase.get("refunded", False)
        chargebacked = purchase.get("chargebacked", False)

        if refunded or chargebacked:
            return False, {"error": "Kauf wurde erstattet"}

        try:
            created_dt = datetime.strptime(created[:10], "%Y-%m-%d")
            expiry     = created_dt + timedelta(days=36500)
        except Exception:
            expiry = datetime.now() + timedelta(days=36500)

        return True, {
            "type":      "PRO",
            "expiry":    expiry.strftime("%Y-%m-%d"),
            "days_left": (expiry - datetime.now()).days,
            "source":    "gumroad",
            "email":     email,
        }

    except Exception as e:
        err = str(e)
        if "ConnectionError" in type(e).__name__ or "ConnectTimeout" in type(e).__name__:
            return False, {"error": "no_internet"}
        return False, {"error": err}


# ── Aktivierung ───────────────────────────────────────────────────────────────

def activate(key: str) -> tuple[bool, str]:
    """Aktiviert einen Lizenzschlüssel (server-geprüft oder Gumroad-Legacy)."""
    key = key.strip().upper()

    if key.startswith("VADOX-"):
        ok, info = _verify_remote_key(key)
        if not ok:
            err = info.get("error", "Unbekannt")
            if err == "no_internet":
                return False, "Kein Internet — bitte Verbindung prüfen und erneut versuchen."
            return False, f"Ungültiger Key: {err}"
    else:
        # Gumroad-Key — erst PRO, dann BUSINESS probieren
        ok, info = _verify_gumroad(key, GUMROAD_PRO_ID)
        if not ok and info.get("error") != "no_internet":
            ok, info = _verify_gumroad(key, GUMROAD_BUSINESS_ID)
            if ok:
                info["type"] = "BUSINESS"

        if not ok:
            err = info.get("error", "Unbekannt")
            if err == "no_internet":
                return False, "Kein Internet — bitte Verbindung prüfen und erneut versuchen."
            if "erstattet" in err.lower():
                return False, "Dieser Kauf wurde erstattet. Key nicht mehr gültig."
            return False, f"Ungültiger Key: {err}"

    # Lizenz lokal speichern
    LICENSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "key":        key,
        "type":       info.get("type", "PRO"),
        "expiry":     info.get("expiry", ""),
        "days_left":  info.get("days_left", 36500),
        "machine_id": _machine_id(),
        "activated":  datetime.now().isoformat(),
        "source":     info.get("source", "local"),
        "email":      info.get("email", ""),
    }
    LICENSE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    ltype = info.get("type", "PRO")
    label = KEY_TYPES.get(ltype, {}).get("label", ltype)
    return True, f"Lizenz aktiviert! Vadox {label} — freigeschaltet."


# ── Status prüfen ─────────────────────────────────────────────────────────────

def check() -> tuple[bool, str]:
    """
    Prüft ob eine gültige Lizenz oder aktiver Trial vorhanden ist.
    Gibt (ok, status_string) zurück.
    """
    # Lizenz vorhanden?
    if LICENSE_PATH.exists():
        try:
            data   = json.loads(LICENSE_PATH.read_text(encoding="utf-8"))
            expiry = datetime.strptime(data["expiry"], "%Y-%m-%d")
            if datetime.now() <= expiry:
                ltype = data.get("type", "PRO")
                label = KEY_TYPES.get(ltype, {}).get("label", ltype)
                return True, label
        except Exception:
            pass

    # Trial aktiv?
    trial = get_trial_info()
    if trial.get("active"):
        h = trial["seconds_left"] // 3600
        m = (trial["seconds_left"] % 3600) // 60
        return True, f"TRIAL — noch {h}h {m}m"

    if trial.get("expired"):
        return False, "trial_expired"

    return False, "no_license"


def is_licensed() -> bool:
    ok, _ = check()
    return ok


def get_info() -> dict:
    """Vollständige Lizenzinformationen für das Einstellungs-Panel."""
    # Aktive Lizenz
    if LICENSE_PATH.exists():
        try:
            data   = json.loads(LICENSE_PATH.read_text(encoding="utf-8"))
            expiry = datetime.strptime(data["expiry"], "%Y-%m-%d")
            if datetime.now() <= expiry:
                ltype = data.get("type", "PRO")
                return {
                    "valid":     True,
                    "type":      ltype,
                    "label":     KEY_TYPES.get(ltype, {}).get("label", ltype),
                    "expiry":    data["expiry"],
                    "days_left": (expiry - datetime.now()).days,
                    "email":     data.get("email", ""),
                    "source":    data.get("source", ""),
                }
        except Exception:
            pass

    # Trial
    trial = get_trial_info()
    if trial.get("active"):
        return {
            "valid":       True,
            "type":        "TRIAL",
            "label":       "Trial (24h)",
            "seconds_left": trial["seconds_left"],
            "expires":     trial.get("expires", ""),
        }

    return {"valid": False, "type": "NONE", "label": "Keine Lizenz"}
