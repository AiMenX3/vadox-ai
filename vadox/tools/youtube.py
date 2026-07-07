"""
YouTube Tool — Videos suchen und öffnen.
Nutzt YouTube Data API v3 (kostenlos, 10.000 Anfragen/Tag) oder Fallback via yt-dlp.
"""
import webbrowser
import urllib.parse
import requests


def _get_yt_api_key() -> str:
    try:
        from vadox.core import settings
        return settings.load().get("youtube_api_key", "")
    except Exception:
        return ""


def _search_via_api(query: str, count: int = 5) -> list:
    """Sucht Videos über YouTube Data API v3."""
    api_key = _get_yt_api_key()
    if not api_key:
        return []
    try:
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": query,
                "maxResults": count,
                "type": "video",
                "key": api_key,
                "relevanceLanguage": "de",
            },
            timeout=8
        )
        data = r.json()
        results = []
        for item in data.get("items", []):
            vid_id  = item["id"]["videoId"]
            snippet = item["snippet"]
            results.append({
                "title":   snippet.get("title", "?"),
                "channel": snippet.get("channelTitle", "?"),
                "id":      vid_id,
                "url":     f"https://youtube.com/watch?v={vid_id}",
            })
        return results
    except Exception:
        return []


def _search_via_ytdlp(query: str, count: int = 5) -> list:
    """Sucht Videos über yt-dlp (kein API-Key nötig)."""
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "playlist_items": f"1:{count}",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_url = f"ytsearch{count}:{query}"
            info = ydl.extract_info(search_url, download=False)
            results = []
            for entry in info.get("entries", []):
                if entry:
                    vid_id = entry.get("id", "")
                    results.append({
                        "title":    entry.get("title", "?"),
                        "channel":  entry.get("uploader", "?"),
                        "duration": entry.get("duration_string", "?"),
                        "id":       vid_id,
                        "url":      f"https://youtube.com/watch?v={vid_id}",
                    })
            return results
    except Exception:
        return []


def _search_videos(query: str, count: int = 5) -> list:
    """Sucht Videos — versucht API, dann yt-dlp."""
    results = _search_via_api(query, count)
    if not results:
        results = _search_via_ytdlp(query, count)
    return results


def search_youtube(query: str, count: int = 5) -> str:
    """Sucht YouTube-Videos und gibt Titel + Links zurück."""
    videos = _search_videos(query, count)

    if not videos:
        encoded = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        webbrowser.open(url)
        return f"YouTube-Suche nach '{query}' im Browser geöffnet (kein API-Key konfiguriert)."

    lines = [f"YouTube-Suchergebnisse fuer '{query}':"]
    for i, v in enumerate(videos, 1):
        duration = v.get("duration", "")
        dur_str  = f" | {duration}" if duration else ""
        lines.append(f"{i}. {v['title']} | {v['channel']}{dur_str}\n   {v['url']}")

    return "\n".join(lines)


def open_youtube(query: str) -> str:
    """Sucht und öffnet das erste Ergebnis direkt im Browser."""
    videos = _search_videos(query, 1)

    if not videos:
        # Kein API-Key — direkt Suchseite öffnen
        encoded = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        webbrowser.open(url)
        return f"YouTube-Suchseite fuer '{query}' geoeffnet. Kein API-Key hinterlegt — Video muss manuell ausgewaehlt werden."

    v   = videos[0]
    url = v["url"]
    webbrowser.open(url)
    return f"YouTube geoeffnet: '{v['title']}' von {v['channel']}\n{url}"


def open_youtube_music(query: str) -> str:
    """Öffnet YouTube Music mit einem Suchbegriff."""
    encoded = urllib.parse.quote(query)
    url = f"https://music.youtube.com/search?q={encoded}"
    webbrowser.open(url)
    return f"YouTube Music geoeffnet fuer: '{query}'"


def get_trending() -> str:
    """Öffnet YouTube Trending im Browser."""
    webbrowser.open("https://www.youtube.com/feed/trending")
    return "YouTube Trending im Browser geoeffnet."


def get_video_summary(query: str) -> str:
    """Sucht Videos und gibt Titel/Kanal/Link zurück."""
    videos = _search_videos(query, 3)
    if not videos:
        return f"Keine Videos zu '{query}' gefunden."

    lines = [f"YouTube-Videos zu '{query}':"]
    for v in videos:
        lines.append(f"- {v['title']} | {v['channel']}\n  {v['url']}")
    return "\n".join(lines)
