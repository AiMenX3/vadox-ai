"""
Live-Webcams (YouTube-Livestreams via VLC)
------------------------------------------
Zeigt echte oeffentliche Live-Video-Streams grosser Staedte. Quelle sind
oeffentliche 24/7-YouTube-Livestreams; die direkte Stream-URL wird per yt-dlp
ermittelt und im Panel per VLC abgespielt (native System-Codecs, H.264).

So gibt es echtes Live-Video statt nur Standbilder, und keine YouTube-Embed-
Fehler, weil nicht eingebettet, sondern direkt der Stream abgespielt wird.
"""

from concurrent.futures import ThreadPoolExecutor

# Kuratierte Staedte: key -> (Anzeigename, Land-Emoji, YouTube-Suchbegriff)
CITIES = {
    "new york":    ("New York",    "🇺🇸", "New York Times Square live cam 24/7"),
    "berlin":      ("Berlin",      "🇩🇪", "Berlin live webcam 24/7"),
    "hamburg":     ("Hamburg",     "🇩🇪", "Hamburg live webcam 24/7"),
    "venice":      ("Venedig",     "🇮🇹", "Venice live cam 24/7"),
    "rome":        ("Rom",         "🇮🇹", "Rome live cam 24/7"),
    "tokyo":       ("Tokio",       "🇯🇵", "Tokyo Shibuya live cam 24/7"),
    "paris":       ("Paris",       "🇫🇷", "Paris live cam 24/7"),
    "london":      ("London",      "🇬🇧", "London live cam 24/7"),
    "dubai":       ("Dubai",       "🇦🇪", "Dubai live cam 24/7"),
    "barcelona":   ("Barcelona",   "🇪🇸", "Barcelona live cam 24/7"),
    "amsterdam":   ("Amsterdam",   "🇳🇱", "Amsterdam live cam 24/7"),
    "miami":       ("Miami Beach", "🇺🇸", "Miami Beach live cam 24/7"),
    "los angeles": ("Los Angeles", "🇺🇸", "Los Angeles live cam 24/7"),
    "prague":      ("Prag",        "🇨🇿", "Prague live cam 24/7"),
    "sydney":      ("Sydney",      "🇦🇺", "Sydney live cam 24/7"),
}

_ALIASES = {
    "nyc": "new york", "new york city": "new york", "manhattan": "new york",
    "venedig": "venice", "venezia": "venice",
    "rom": "rome", "roma": "rome",
    "tokio": "tokyo",
    "prag": "prague", "praha": "prague",
    "la": "los angeles",
}


def _normalize(location: str) -> str:
    loc = (location or "").strip().lower()
    if loc in CITIES:
        return loc
    if loc in _ALIASES:
        return _ALIASES[loc]
    for key in CITIES:
        if key in loc:
            return key
    for alias, key in _ALIASES.items():
        if alias in loc:
            return key
    return ""


def _search_live_ids(query: str, want: int = 3) -> list:
    """Findet aktuell LIVE laufende YouTube-Streams (schnelle Flat-Suche).
    Gibt Liste von (titel, video_id) zurueck."""
    try:
        import yt_dlp
        n = max(want * 4, 10)
        with yt_dlp.YoutubeDL({
            "quiet": True, "no_warnings": True,
            "extract_flat": True, "playlist_items": f"1:{n}",
        }) as ydl:
            info = ydl.extract_info(f"ytsearch{n}:{query}", download=False)
        out = []
        for e in info.get("entries", []) or []:
            if e and e.get("live_status") == "is_live" and e.get("id"):
                out.append((e.get("title", "Live"), e["id"]))
            if len(out) >= want:
                break
        return out
    except Exception:
        return []


def _resolve_stream(video_id: str) -> str:
    """Ermittelt die direkte abspielbare Stream-URL (HLS) eines Videos."""
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL({
            "quiet": True, "no_warnings": True,
            # Niedrige Aufloesung fuer die kleinen Grid-Kacheln: 6 gleichzeitige
            # HD-Streams koennen schwaechere Rechner ueberlasten/einfrieren.
            # 480p reicht fuer die Vorschau und spart massiv CPU/GPU/RAM.
            "format": "best[height<=480]/best[height<=720]/best",
        }) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )
        return info.get("url", "") or ""
    except Exception:
        return ""


def _cams_for_query(query: str, name: str, flag: str, want: int) -> list:
    """Sucht Live-IDs und loest deren Stream-URLs parallel auf."""
    pairs = _search_live_ids(query, want=want)
    if not pairs:
        return []
    with ThreadPoolExecutor(max_workers=min(6, len(pairs))) as ex:
        urls = list(ex.map(lambda p: _resolve_stream(p[1]), pairs))
    cams = []
    for (title, vid), url in zip(pairs, urls):
        if url:
            cams.append({
                "title": title, "city": name, "flag": flag,
                "stream_url": url,
                "watch_url": f"https://www.youtube.com/watch?v={vid}",
            })
    return cams[:want]


def get_webcams(location: str = "", max_cams: int = 6) -> dict:
    """Ermittelt echte Live-Streams (Netzwerk — nicht im UI-Thread aufrufen).

    Rueckgabe: {"title", "cams":[{title,city,flag,stream_url,watch_url}], "error"}
    """
    city = _normalize(location)

    if city:
        name, flag, query = CITIES[city]
        cams = _cams_for_query(query, name, flag, max_cams)
        return {"title": f"{flag}  Live-Kameras — {name}", "cams": cams, "error": ""}

    # Welt-Auswahl: je eine Kamera aus mehreren Staedten, parallel
    picks = list(CITIES.items())

    def _one(item):
        name, flag, query = item[1]
        cams = _cams_for_query(query, name, flag, 1)
        return cams[0] if cams else None

    cams = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for res in ex.map(_one, picks):
            if res:
                cams.append(res)
            if len(cams) >= max_cams:
                break
    return {"title": "🌍  Live-Kameras aus aller Welt", "cams": cams[:max_cams], "error": ""}


def list_available_cities() -> str:
    names = [f"{flag} {name}" for (name, flag, _) in CITIES.values()]
    return "Verfuegbare Live-Kamera-Staedte: " + ", ".join(names)


def open_webcams(location: str = "") -> str:
    """Tool-Einstieg: oeffnet das Webcam-Panel im Hauptfenster (falls GUI laeuft)."""
    from vadox.core import ui_bridge
    opened = ui_bridge.open_webcams(location)
    if not opened:
        return list_available_cities()
    city = _normalize(location)
    if city:
        return f"Ich oeffne Live-Kameras aus {CITIES[city][0]}."
    return "Ich oeffne Live-Kameras aus aller Welt."
