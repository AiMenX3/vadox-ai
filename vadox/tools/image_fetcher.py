import requests
import tempfile
import os
from pathlib import Path
from vadox.core import settings


PEXELS_BASE = "https://api.pexels.com/v1"


def _get_key() -> str:
    return settings.get("pexels_api_key", "")


def fetch_image_for_topic(topic: str, index: int = 0) -> str | None:
    """
    Lädt ein passendes Bild zu einem Thema herunter.
    Gibt den lokalen Dateipfad zurück, oder None wenn kein Key oder kein Ergebnis.
    """
    key = _get_key()
    if not key:
        return None

    try:
        headers = {"Authorization": key}
        params  = {"query": topic, "per_page": 10, "orientation": "landscape"}
        r = requests.get(f"{PEXELS_BASE}/search", headers=headers, params=params, timeout=10)
        r.raise_for_status()
        photos = r.json().get("photos", [])

        if not photos:
            return None

        photo = photos[index % len(photos)]
        img_url = photo["src"]["large2x"]  # 1920px Breite

        img_r = requests.get(img_url, timeout=15)
        img_r.raise_for_status()

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp.write(img_r.content)
        tmp.close()
        return tmp.name

    except Exception as e:
        print(f"[ImageFetcher] Fehler: {e}")
        return None


def fetch_images_for_presentation(topic: str, count: int = 6) -> list[str | None]:
    """Holt `count` verschiedene Bilder für eine Präsentation."""
    key = _get_key()
    if not key:
        return [None] * count

    try:
        headers = {"Authorization": key}
        params  = {"query": topic, "per_page": min(count, 15), "orientation": "landscape"}
        r = requests.get(f"{PEXELS_BASE}/search", headers=headers, params=params, timeout=10)
        r.raise_for_status()
        photos = r.json().get("photos", [])

        paths = []
        for i, photo in enumerate(photos[:count]):
            try:
                img_url = photo["src"]["large"]
                img_r = requests.get(img_url, timeout=15)
                img_r.raise_for_status()
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                tmp.write(img_r.content)
                tmp.close()
                paths.append(tmp.name)
            except Exception:
                paths.append(None)

        # Auffüllen falls weniger Bilder als Folien
        while len(paths) < count:
            paths.append(paths[0] if paths else None)

        return paths

    except Exception as e:
        print(f"[ImageFetcher] Batch-Fehler: {e}")
        return [None] * count


def cleanup_temp_images(paths: list):
    for p in paths:
        if p and os.path.exists(p):
            try:
                os.unlink(p)
            except Exception:
                pass
