import json
import base64
import os
from pathlib import Path


SETTINGS_PATH = Path.home() / ".vadox" / "settings.json"


def _encode(value: str) -> str:
    return base64.b64encode(value.encode()).decode()


def _decode(value: str) -> str:
    try:
        return base64.b64decode(value.encode()).decode()
    except Exception:
        return value


DEFAULT = {
    "api_key": "",
    "provider": "claude",
    "model": "claude-sonnet-5",
    "voice": "de-DE-KatjaNeural",
    "user_name": "",
    "language": "de-DE",
    "tts_enabled": True,
    "stt_enabled": True,
    "email_provider": "gmail",
    "email_address": "",
    "email_password": "",
    "pexels_api_key": "",
    "picovoice_key": "",
    "exchange_domain": "",
    "exchange_server": "",
    "smarthome": {
        "hue_ip": "",
        "hue_key": "",
        "ha_ip": "",
        "ha_port": "8123",
        "ha_token": "",
        "shelly_devices": [],
    },
}


def load() -> dict:
    try:
        if SETTINGS_PATH.exists():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            merged = {**DEFAULT, **data}
            if merged.get("api_key"):
                merged["api_key"] = _decode(merged["api_key"])
            if merged.get("email_password"):
                merged["email_password"] = _decode(merged["email_password"])
            return merged
    except Exception:
        pass
    return dict(DEFAULT)


def save(settings: dict):
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = dict(settings)
        if data.get("api_key"):
            data["api_key"] = _encode(data["api_key"])
        if data.get("email_password"):
            data["email_password"] = _encode(data["email_password"])
        SETTINGS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[Settings] Speichern fehlgeschlagen: {e}")


def get(key: str, default=None):
    return load().get(key, default)


def set_value(key: str, value):
    s = load()
    s[key] = value
    save(s)
