"""
Spotify-Integration — Musik über Spotify abspielen und steuern.
Nutzt spotipy (Spotify Web API) oder öffnet Spotify direkt.
"""
import webbrowser
import urllib.parse
import subprocess
import os


def _open_spotify_app() -> bool:
    """Öffnet Spotify falls nicht bereits offen."""
    try:
        paths = [
            os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
            r"C:\Program Files\WindowsApps\SpotifyAB.SpotifyMusic_*\Spotify.exe",
        ]
        for p in paths:
            if os.path.exists(p):
                subprocess.Popen([p])
                return True
        # Microsoft Store Version
        subprocess.Popen(["explorer", "spotify:"])
        return True
    except Exception:
        return False


def spotify_play(query: str) -> str:
    """Öffnet Spotify und sucht/spielt den Song oder Künstler."""
    try:
        # Spotipy (Web API) versuchen — benötigt Client-ID/Secret
        from vadox.core import settings
        cfg = settings.load()
        client_id     = cfg.get("spotify_client_id", "")
        client_secret = cfg.get("spotify_client_secret", "")

        if client_id and client_secret:
            return _spotify_via_api(query, client_id, client_secret)
    except Exception:
        pass

    # Fallback: Spotify URI öffnen
    encoded = urllib.parse.quote(query)
    uri     = f"spotify:search:{encoded}"
    try:
        os.startfile(uri)
        return f"Spotify geöffnet mit Suche nach: '{query}'"
    except Exception:
        webbrowser.open(f"https://open.spotify.com/search/{encoded}")
        return f"Spotify im Browser geöffnet: '{query}'"


def _spotify_via_api(query: str, client_id: str, client_secret: str) -> str:
    """Nutzt Spotify Web API für direkte Wiedergabe."""
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth

        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://localhost:8888/callback",
            scope="user-modify-playback-state user-read-playback-state",
            open_browser=False
        ))

        results = sp.search(q=query, limit=1, type="track,artist,playlist")

        # Track gefunden?
        tracks = results.get("tracks", {}).get("items", [])
        if tracks:
            track = tracks[0]
            sp.start_playback(uris=[track["uri"]])
            return f"Spiele: '{track['name']}' von {track['artists'][0]['name']}"

        return f"Nichts gefunden für '{query}'"
    except Exception as e:
        # Fallback auf URI
        encoded = urllib.parse.quote(query)
        try:
            os.startfile(f"spotify:search:{encoded}")
        except Exception:
            webbrowser.open(f"https://open.spotify.com/search/{encoded}")
        return f"Spotify geöffnet für: '{query}'"


def spotify_control(action: str) -> str:
    """Steuert Spotify-Wiedergabe (pause, play, next, previous)."""
    try:
        from vadox.core import settings
        cfg           = settings.load()
        client_id     = cfg.get("spotify_client_id", "")
        client_secret = cfg.get("spotify_client_secret", "")

        if client_id and client_secret:
            return _spotify_control_api(action, client_id, client_secret)
    except Exception:
        pass

    # Fallback: Tastenkürzel via Spotify-Fenster
    return _spotify_hotkey(action)


def _spotify_control_api(action: str, client_id: str, client_secret: str) -> str:
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id, client_secret=client_secret,
            redirect_uri="http://localhost:8888/callback",
            scope="user-modify-playback-state user-read-playback-state",
            open_browser=False
        ))
        if action == "pause":
            sp.pause_playback()
            return "Spotify pausiert."
        elif action in ("play", "weiter", "resume"):
            sp.start_playback()
            return "Spotify läuft weiter."
        elif action in ("next", "weiter", "nächster"):
            sp.next_track()
            return "Nächster Song."
        elif action in ("previous", "zurück", "vorheriger"):
            sp.previous_track()
            return "Vorheriger Song."
        elif action in ("volume_up", "lauter"):
            current = sp.current_playback()
            vol = min(100, (current or {}).get("device", {}).get("volume_percent", 50) + 10)
            sp.volume(vol)
            return f"Spotify Lautstärke: {vol}%"
        elif action in ("volume_down", "leiser"):
            current = sp.current_playback()
            vol = max(0, (current or {}).get("device", {}).get("volume_percent", 50) - 10)
            sp.volume(vol)
            return f"Spotify Lautstärke: {vol}%"
        return f"Unbekannte Aktion: {action}"
    except Exception as e:
        return _spotify_hotkey(action)


def _spotify_hotkey(action: str) -> str:
    """Steuert Spotify via Tastenkürzel (pyautogui)."""
    try:
        import pyautogui
        import time

        key_map = {
            "pause":     "space",
            "play":      "space",
            "next":      "right",
            "previous":  "left",
            "nächster":  "right",
            "vorheriger":"left",
        }
        key = key_map.get(action.lower())
        if key:
            # Spotify-Fenster aktivieren
            import subprocess
            subprocess.Popen(["powershell", "-Command",
                "(Get-Process Spotify -ErrorAction SilentlyContinue | ForEach-Object { $_.MainWindowHandle }) | ForEach-Object { [void][System.Runtime.InteropServices.Marshal]::ThrowExceptionForHR([user32]::SetForegroundWindow($_)) }"
            ])
            time.sleep(0.3)
            pyautogui.hotkey("ctrl", key) if key in ("right", "left") else pyautogui.press(key)
            return f"Spotify: {action}"
    except Exception:
        pass
    return f"Spotify-Steuerung: '{action}' — Spotify-App öffnen und manuell steuern."
