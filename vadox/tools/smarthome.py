"""
Vadox Smart Home Integration
Unterstützt: Philips Hue, Shelly, Home Assistant
Alle Geräte werden lokal angesprochen — kein Cloud-Zwang.
"""
import requests
import json
from vadox.core import settings


def _cfg() -> dict:
    return settings.load().get("smarthome", {})


# ── Philips Hue ───────────────────────────────────────────────────────────────

def _hue_base() -> str | None:
    c = _cfg()
    ip  = c.get("hue_ip", "")
    key = c.get("hue_key", "")
    if not ip or not key:
        return None
    return f"http://{ip}/api/{key}"


def hue_list_lights() -> list[dict]:
    base = _hue_base()
    if not base:
        return []
    try:
        r = requests.get(f"{base}/lights", timeout=5)
        data = r.json()
        return [{"id": k, "name": v["name"], "on": v["state"]["on"],
                 "brightness": v["state"].get("bri", 0)} for k, v in data.items()]
    except Exception:
        return []


def hue_set_light(light_id: str, on: bool, brightness: int = None, color_name: str = None) -> bool:
    base = _hue_base()
    if not base:
        return False
    body = {"on": on}
    if brightness is not None:
        body["bri"] = max(1, min(254, int(brightness * 2.54)))
    if color_name and on:
        hue_map = {
            "rot": (0, 254, 254), "grün": (25500, 254, 254),
            "blau": (46920, 254, 254), "gelb": (12750, 254, 254),
            "lila": (56100, 254, 254), "orange": (6000, 254, 254),
            "weiß": None, "warm": (None, None, None),
        }
        if color_name.lower() in hue_map and hue_map[color_name.lower()][0]:
            h, s, b = hue_map[color_name.lower()]
            body["hue"] = h
            body["sat"] = s
    try:
        r = requests.put(f"{base}/lights/{light_id}/state", json=body, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def hue_all_lights(on: bool) -> str:
    base = _hue_base()
    if not base:
        return "Philips Hue nicht konfiguriert. Bitte IP und API-Key in den Einstellungen eingeben."
    try:
        r = requests.get(f"{base}/lights", timeout=5)
        lights = r.json()
        for lid in lights:
            requests.put(f"{base}/lights/{lid}/state", json={"on": on}, timeout=3)
        status = "eingeschaltet" if on else "ausgeschaltet"
        return f"Alle {len(lights)} Hue-Lampen {status}."
    except Exception as e:
        return f"Hue Fehler: {e}"


def hue_scene(scene_name: str) -> str:
    """Szene nach Name aktivieren."""
    base = _hue_base()
    if not base:
        return "Philips Hue nicht konfiguriert."
    try:
        # Gruppen holen
        r = requests.get(f"{base}/groups", timeout=5)
        groups = r.json()
        # Szenen holen
        rs = requests.get(f"{base}/scenes", timeout=5)
        scenes = rs.json()
        scene_id = None
        for sid, sv in scenes.items():
            if scene_name.lower() in sv.get("name", "").lower():
                scene_id = sid
                break
        if not scene_id:
            available = [sv.get("name") for sv in scenes.values()][:5]
            return f"Szene '{scene_name}' nicht gefunden. Verfügbar: {', '.join(available)}"
        # Szene auf Gruppe 0 (alle) anwenden
        group_id = list(groups.keys())[0] if groups else "0"
        requests.put(f"{base}/groups/{group_id}/action",
                     json={"scene": scene_id}, timeout=5)
        return f"Szene '{scene_name}' aktiviert."
    except Exception as e:
        return f"Hue Szene Fehler: {e}"


# ── Shelly ────────────────────────────────────────────────────────────────────

def _shelly_devices() -> list[dict]:
    return _cfg().get("shelly_devices", [])


def shelly_set(device_name: str, on: bool) -> str:
    devices = _shelly_devices()
    if not devices:
        return "Keine Shelly-Geräte konfiguriert. Bitte in den Einstellungen hinzufügen."
    matches = [d for d in devices if device_name.lower() in d.get("name", "").lower()]
    if not matches:
        names = [d["name"] for d in devices]
        return f"Shelly-Gerät '{device_name}' nicht gefunden. Verfügbar: {', '.join(names)}"
    results = []
    for device in matches:
        ip = device.get("ip", "")
        try:
            # Shelly Gen1
            r = requests.get(f"http://{ip}/relay/0?turn={'on' if on else 'off'}", timeout=5)
            if r.status_code != 200:
                # Shelly Gen2
                requests.post(f"http://{ip}/rpc/Switch.Set",
                              json={"id": 0, "on": on}, timeout=5)
            status = "eingeschaltet" if on else "ausgeschaltet"
            results.append(f"{device['name']} {status}")
        except Exception as e:
            results.append(f"{device['name']}: Fehler ({e})")
    return " | ".join(results)


def shelly_status(device_name: str) -> str:
    devices = _shelly_devices()
    matches = [d for d in devices if device_name.lower() in d.get("name", "").lower()]
    if not matches:
        return f"Shelly-Gerät '{device_name}' nicht gefunden."
    d = matches[0]
    try:
        r = requests.get(f"http://{d['ip']}/status", timeout=5)
        data = r.json()
        relay = data.get("relays", [{}])[0]
        is_on = relay.get("ison", False)
        power = data.get("meters", [{}])[0].get("power", 0)
        return f"{d['name']}: {'AN' if is_on else 'AUS'} | Verbrauch: {power:.1f}W"
    except Exception as e:
        return f"Shelly Status Fehler: {e}"


# ── Home Assistant ─────────────────────────────────────────────────────────────

def _ha_headers() -> dict | None:
    c = _cfg()
    token = c.get("ha_token", "")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _ha_url() -> str:
    c = _cfg()
    ip = c.get("ha_ip", "localhost")
    port = c.get("ha_port", "8123")
    return f"http://{ip}:{port}/api"


def ha_get_states() -> list[dict]:
    headers = _ha_headers()
    if not headers:
        return []
    try:
        r = requests.get(f"{_ha_url()}/states", headers=headers, timeout=8)
        return r.json()
    except Exception:
        return []


def ha_call_service(domain: str, service: str, entity_id: str) -> bool:
    headers = _ha_headers()
    if not headers:
        return False
    try:
        r = requests.post(
            f"{_ha_url()}/services/{domain}/{service}",
            headers=headers,
            json={"entity_id": entity_id},
            timeout=8,
        )
        return r.status_code in (200, 201)
    except Exception:
        return False


def ha_toggle(entity_name: str, on: bool) -> str:
    headers = _ha_headers()
    if not headers:
        return "Home Assistant nicht konfiguriert. Bitte IP und Token in den Einstellungen eingeben."
    states = ha_get_states()
    matches = [s for s in states
               if entity_name.lower() in s.get("attributes", {}).get("friendly_name", "").lower()
               or entity_name.lower() in s.get("entity_id", "").lower()]
    if not matches:
        return f"Gerät '{entity_name}' in Home Assistant nicht gefunden."
    results = []
    for entity in matches[:3]:
        eid = entity["entity_id"]
        domain = eid.split(".")[0]
        service = "turn_on" if on else "turn_off"
        ok = ha_call_service(domain, service, eid)
        name = entity.get("attributes", {}).get("friendly_name", eid)
        status = "eingeschaltet" if on else "ausgeschaltet"
        results.append(f"{name} {'✓' if ok else '✗'} {status if ok else 'Fehler'}")
    return " | ".join(results)


def ha_list_devices() -> str:
    states = ha_get_states()
    if not states:
        return "Home Assistant nicht verbunden oder keine Geräte gefunden."
    controllable = [s for s in states
                    if s["entity_id"].startswith(("light.", "switch.", "climate.", "cover.", "fan."))]
    lines = []
    for s in controllable[:15]:
        name = s.get("attributes", {}).get("friendly_name", s["entity_id"])
        state = s.get("state", "?")
        lines.append(f"• {name} — {state}")
    return "Home Assistant Geräte:\n" + "\n".join(lines)


# ── Universelle Tool-Funktion für den KI-Chat ─────────────────────────────────

def smarthome_command(command: str) -> str:
    """
    Wird vom KI-Tool-System aufgerufen.
    Versteht natürliche Befehle wie:
    - "Licht an", "Lampen aus", "alles ausschalten"
    - "Shelly Steckdose Küche an"
    - "Home Assistant Heizung auf 22 Grad"
    - "Hue Szene Entspannung"
    """
    cmd = command.lower().strip()

    # Licht an/aus
    if any(w in cmd for w in ["licht an", "lampen an", "lichter an", "alles an"]):
        results = []
        if _hue_base():
            results.append(hue_all_lights(True))
        c = _cfg()
        if c.get("ha_token"):
            results.append(ha_toggle("light", True))
        return " | ".join(results) if results else "Kein Smart Home konfiguriert."

    if any(w in cmd for w in ["licht aus", "lampen aus", "lichter aus", "alles aus"]):
        results = []
        if _hue_base():
            results.append(hue_all_lights(False))
        c = _cfg()
        if c.get("ha_token"):
            results.append(ha_toggle("light", False))
        return " | ".join(results) if results else "Kein Smart Home konfiguriert."

    # Szene
    if "szene" in cmd:
        parts = cmd.split("szene")
        scene = parts[-1].strip() if len(parts) > 1 else ""
        if scene and _hue_base():
            return hue_scene(scene)

    # Shelly spezifisch
    if "shelly" in cmd or "steckdose" in cmd:
        on = any(w in cmd for w in [" an", "ein", "on"])
        # Gerätename extrahieren
        name = cmd.replace("shelly", "").replace("steckdose", "").replace(" an", "").replace(" aus", "").strip()
        return shelly_set(name or "alle", on)

    # HA spezifisch
    if "home assistant" in cmd or " ha " in cmd:
        name = cmd.replace("home assistant", "").replace(" ha ", "").strip()
        on = any(w in cmd for w in [" an", "ein", "on", "starten"])
        return ha_toggle(name, on)

    # Gerätestatus abfragen
    if any(w in cmd for w in ["status", "zustand", "was läuft", "geräte"]):
        parts = []
        lights = hue_list_lights()
        if lights:
            on_lights = [l["name"] for l in lights if l["on"]]
            parts.append(f"Hue: {len(on_lights)}/{len(lights)} Lampen an")
        if _cfg().get("ha_token"):
            parts.append(ha_list_devices())
        return "\n".join(parts) if parts else "Kein Smart Home konfiguriert."

    return f"Smart Home Befehl nicht erkannt: '{command}'. Versuche: 'Licht an', 'Lampen aus', 'Szene Entspannung'"
