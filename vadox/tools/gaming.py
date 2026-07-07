"""
Gaming Tool — Steam & Epic Games Info, Updates, Launcher.
Nutzt Steam Web API (kein Key nötig für öffentliche Daten) + Launcher-Integration.
"""
import webbrowser
import subprocess
import os
import urllib.parse


# Steam App-IDs häufiger Spiele (für direkte Links)
KNOWN_GAMES = {
    "cs2":              730,
    "counter-strike":   730,
    "csgo":             730,
    "dota":             570,
    "dota 2":           570,
    "pubg":             578080,
    "rust":             252490,
    "gta v":            271590,
    "gta5":             271590,
    "cyberpunk":        1091500,
    "elden ring":       1245620,
    "valheim":          892970,
    "minecraft":        None,  # Nicht auf Steam
    "fortnite":         None,  # Epic only
    "rocket league":    252950,
    "among us":         945360,
    "hollow knight":    367520,
    "stardew valley":   413150,
    "terraria":         105600,
}


def launch_steam() -> str:
    """Startet Steam."""
    try:
        steam_paths = [
            r"C:\Program Files (x86)\Steam\Steam.exe",
            r"C:\Program Files\Steam\Steam.exe",
        ]
        for path in steam_paths:
            if os.path.exists(path):
                subprocess.Popen([path])
                return "Steam wird gestartet..."
        # Via URI
        subprocess.Popen(["start", "steam://"], shell=True)
        return "Steam über URI gestartet."
    except Exception as e:
        return f"Steam konnte nicht gestartet werden: {e}"


def launch_epic() -> str:
    """Startet Epic Games Launcher."""
    try:
        epic_paths = [
            r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
            r"C:\Program Files\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
        ]
        for path in epic_paths:
            if os.path.exists(path):
                subprocess.Popen([path])
                return "Epic Games Launcher wird gestartet..."
        subprocess.Popen(["start", "com.epicgames.launcher://"], shell=True)
        return "Epic Games Launcher gestartet."
    except Exception as e:
        return f"Epic Launcher konnte nicht gestartet werden: {e}"


def launch_game(game_name: str) -> str:
    """Startet ein Spiel direkt über Steam oder Epic."""
    try:
        name_lower = game_name.lower().strip()

        # Steam-Spiel über App-ID starten
        app_id = KNOWN_GAMES.get(name_lower)
        if app_id:
            subprocess.Popen(["start", f"steam://rungameid/{app_id}"], shell=True)
            return f"'{game_name}' wird über Steam gestartet..."

        # Suche in installierten Steam-Spielen
        steam_result = _find_steam_game(game_name)
        if steam_result:
            return steam_result

        # Fallback: Steam-Suche öffnen
        encoded = urllib.parse.quote(game_name)
        webbrowser.open(f"https://store.steampowered.com/search/?term={encoded}")
        return f"Spiel '{game_name}' nicht gefunden. Steam-Store geöffnet zur Suche."

    except Exception as e:
        return f"Spiel-Start Fehler: {e}"


def _find_steam_game(name: str) -> str | None:
    """Sucht installierte Steam-Spiele in den Standard-Verzeichnissen."""
    steam_dirs = [
        r"C:\Program Files (x86)\Steam\steamapps\common",
        r"C:\Program Files\Steam\steamapps\common",
        r"D:\Steam\steamapps\common",
        r"D:\SteamLibrary\steamapps\common",
        r"E:\Steam\steamapps\common",
        r"E:\SteamLibrary\steamapps\common",
    ]
    name_lower = name.lower()
    for steam_dir in steam_dirs:
        if os.path.exists(steam_dir):
            try:
                games = os.listdir(steam_dir)
                for game_folder in games:
                    if name_lower in game_folder.lower():
                        # Exe finden
                        game_path = os.path.join(steam_dir, game_folder)
                        for f in os.listdir(game_path):
                            if f.endswith(".exe") and "unins" not in f.lower():
                                exe = os.path.join(game_path, f)
                                subprocess.Popen([exe])
                                return f"'{game_folder}' gestartet von {game_path}"
            except Exception:
                pass
    return None


def get_steam_game_info(game_name: str) -> str:
    """Holt Spielinformationen von Steam ohne API-Key."""
    try:
        import requests

        name_lower = game_name.lower().strip()
        app_id = KNOWN_GAMES.get(name_lower)

        if not app_id:
            # Steam-Suche nach App-ID
            search_url = f"https://store.steampowered.com/api/storesearch/?term={urllib.parse.quote(game_name)}&l=german&cc=DE"
            r = requests.get(search_url, timeout=10)
            data = r.json()
            items = data.get("items", [])
            if not items:
                return f"Spiel '{game_name}' nicht auf Steam gefunden."
            app_id = items[0]["id"]
            game_name = items[0]["name"]

        # Spiel-Details holen
        detail_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=german&cc=DE"
        r = requests.get(detail_url, timeout=10)
        data = r.json()

        game_data = data.get(str(app_id), {}).get("data", {})
        if not game_data:
            return f"Keine Details für '{game_name}' (ID: {app_id}) gefunden."

        name       = game_data.get("name", game_name)
        desc       = game_data.get("short_description", "Keine Beschreibung")[:200]
        developers = ", ".join(game_data.get("developers", []))
        price_info = game_data.get("price_overview", {})
        price      = price_info.get("final_formatted", "Kostenlos / Unbekannt")
        genres     = ", ".join(g["description"] for g in game_data.get("genres", []))
        rating     = game_data.get("metacritic", {}).get("score", "?")

        return (
            f"Steam: {name}\n"
            f"Entwickler: {developers}\n"
            f"Genre: {genres}\n"
            f"Preis: {price}\n"
            f"Metacritic: {rating}/100\n"
            f"Beschreibung: {desc}\n"
            f"Store: https://store.steampowered.com/app/{app_id}"
        )

    except Exception as e:
        return f"Steam-Info Fehler: {e}"


def check_steam_status() -> str:
    """Prüft ob Steam-Server online sind."""
    try:
        import requests
        r = requests.get("https://store.steampowered.com/api/steamstatus/", timeout=8)
        data = r.json()
        online = data.get("steamStatus", {}).get("store", "?")
        return f"Steam-Status: Store={online}"
    except Exception:
        webbrowser.open("https://steamstat.us/")
        return "Steam-Status im Browser geöffnet: steamstat.us"


def list_installed_steam_games() -> str:
    """Listet installierte Steam-Spiele auf."""
    steam_dirs = [
        r"C:\Program Files (x86)\Steam\steamapps\common",
        r"C:\Program Files\Steam\steamapps\common",
        r"D:\Steam\steamapps\common",
        r"D:\SteamLibrary\steamapps\common",
        r"E:\SteamLibrary\steamapps\common",
    ]
    found = []
    for d in steam_dirs:
        if os.path.exists(d):
            try:
                games = [f for f in os.listdir(d) if os.path.isdir(os.path.join(d, f))]
                found.extend(games)
            except Exception:
                pass

    if not found:
        return "Keine installierten Steam-Spiele gefunden (Standard-Pfade geprüft)."

    found.sort()
    return f"Installierte Steam-Spiele ({len(found)}):\n" + "\n".join(f"• {g}" for g in found[:30])


def open_steam_store(game: str = "") -> str:
    """Öffnet den Steam-Store, optional mit Suche."""
    if game:
        encoded = urllib.parse.quote(game)
        url = f"https://store.steampowered.com/search/?term={encoded}"
    else:
        url = "https://store.steampowered.com/"
    webbrowser.open(url)
    return f"Steam-Store geöffnet{f' für: {game}' if game else ''}."
