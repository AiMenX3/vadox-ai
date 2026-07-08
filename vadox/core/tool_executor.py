from vadox.tools.weather import get_weather
from vadox.tools.search import web_search, news_search
from vadox.tools.files import search_files, list_directory, read_file, create_file, delete_file
from vadox.tools.pc_control import take_screenshot, open_application, open_url, get_system_info
from vadox.tools.email_tool import read_emails, send_email, search_emails, get_unread_count
from vadox.tools.calendar_tool import get_calendar_events, get_todays_events, create_calendar_event
from vadox.tools.presentation import create_presentation_from_text
from vadox.tools.browser import (
    browser_navigate, browser_click, browser_type, browser_get_text,
    browser_search_google, browser_scroll, browser_screenshot, browser_close
)
from vadox.core import memory


def execute_tool(name: str, inputs: dict) -> str:
    try:
        if name == "get_weather":
            return get_weather(
                city=inputs.get("city", "Berlin"),
                days=inputs.get("days", 1)
            )
        elif name == "web_search":
            return web_search(
                query=inputs.get("query", ""),
                max_results=inputs.get("max_results", 5)
            )
        elif name == "news_search":
            return news_search(query=inputs.get("query", ""))
        elif name == "search_files":
            return search_files(
                name=inputs.get("name", ""),
                search_path=inputs.get("search_path")
            )
        elif name == "list_directory":
            return list_directory(path=inputs.get("path"))
        elif name == "read_file":
            return read_file(path=inputs.get("path", ""))
        elif name == "create_file":
            return create_file(
                path=inputs.get("path", ""),
                content=inputs.get("content", "")
            )
        elif name == "delete_file":
            return delete_file(path=inputs.get("path", ""))
        elif name == "take_screenshot":
            return take_screenshot(save_path=inputs.get("save_path"))
        elif name == "open_application":
            return open_application(app_name=inputs.get("app_name", ""))
        elif name == "open_url":
            return open_url(url=inputs.get("url", ""))
        elif name == "get_system_info":
            return get_system_info()
        elif name == "browser_navigate":
            return browser_navigate(url=inputs.get("url", ""))
        elif name == "browser_click":
            return browser_click(selector=inputs.get("selector", ""))
        elif name == "browser_type":
            return browser_type(selector=inputs.get("selector", ""), text=inputs.get("text", ""))
        elif name == "browser_get_text":
            return browser_get_text()
        elif name == "browser_search_google":
            return browser_search_google(query=inputs.get("query", ""))
        elif name == "browser_scroll":
            return browser_scroll(direction=inputs.get("direction", "down"), amount=inputs.get("amount", 500))
        elif name == "browser_screenshot":
            return browser_screenshot(save_path=inputs.get("save_path"))
        elif name == "browser_close":
            return browser_close()
        elif name == "read_emails":
            return read_emails(
                count=inputs.get("count", 5),
                folder=inputs.get("folder", "INBOX"),
                unread_only=inputs.get("unread_only", False)
            )
        elif name == "send_email":
            return send_email(
                to=inputs.get("to", ""),
                subject=inputs.get("subject", ""),
                body=inputs.get("body", "")
            )
        elif name == "search_emails":
            return search_emails(keyword=inputs.get("keyword", ""), count=inputs.get("count", 5))
        elif name == "get_unread_count":
            return get_unread_count()
        elif name == "create_presentation":
            return create_presentation_from_text(
                topic=inputs.get("topic", ""),
                outline=inputs.get("outline", "[]"),
                save_path=inputs.get("save_path")
            )
        elif name == "get_calendar_events":
            return get_calendar_events(days=inputs.get("days", 7))
        elif name == "get_todays_events":
            return get_todays_events()
        elif name == "create_calendar_event":
            return create_calendar_event(
                title=inputs.get("title", ""),
                start=inputs.get("start", ""),
                end=inputs.get("end", ""),
                location=inputs.get("location", ""),
                description=inputs.get("description", "")
            )
        elif name == "remember_fact":
            memory.remember_fact(inputs.get("fact", ""))
            return f"Gespeichert: {inputs.get('fact', '')}"
        elif name == "translate_text":
            from vadox.tools.translator import translate_text
            return translate_text(
                inputs.get("text", ""),
                inputs.get("target_lang", "en"),
                inputs.get("source_lang", "auto")
            )
        elif name == "smarthome_command":
            from vadox.tools.smarthome import smarthome_command
            return smarthome_command(inputs.get("command", ""))

        # ── WhatsApp ──────────────────────────────────────────────────────────
        elif name == "send_whatsapp":
            from vadox.tools.whatsapp import send_whatsapp_now, send_whatsapp
            contact = inputs.get("contact", "")
            message = inputs.get("message", "")
            # Versuche sofort senden, Fallback auf Link
            if contact.replace("+", "").replace(" ", "").isdigit():
                return send_whatsapp_now(contact, message)
            return send_whatsapp(contact, message)

        # ── Screen AI ─────────────────────────────────────────────────────────
        elif name == "analyze_screen":
            from vadox.tools.screen_ai import analyze_screen as _analyze
            return _analyze(inputs.get("question", "Was siehst du auf dem Bildschirm?"))
        elif name == "read_screen_text":
            from vadox.tools.screen_ai import read_screen_text
            return read_screen_text()

        # ── YouTube ───────────────────────────────────────────────────────────
        elif name == "search_youtube":
            from vadox.tools.youtube import search_youtube
            return search_youtube(inputs.get("query", ""), inputs.get("count", 5))
        elif name == "open_youtube":
            from vadox.tools.youtube import open_youtube
            return open_youtube(inputs.get("query", ""))

        # ── Live-Webcams ──────────────────────────────────────────────────────
        elif name == "show_webcams":
            from vadox.tools.webcams import open_webcams
            return open_webcams(inputs.get("location", ""))

        # ── Flugsuche ─────────────────────────────────────────────────────────
        elif name == "search_flights":
            from vadox.tools.flights import search_flights
            return search_flights(
                origin=inputs.get("origin", ""),
                destination=inputs.get("destination", ""),
                date=inputs.get("date", ""),
                return_date=inputs.get("return_date", ""),
                passengers=inputs.get("passengers", 1),
            )
        elif name == "check_flight_status":
            from vadox.tools.flights import check_flight_status
            return check_flight_status(inputs.get("flight_number", ""))

        # ── Gaming ────────────────────────────────────────────────────────────
        elif name == "launch_game":
            from vadox.tools.gaming import launch_game
            return launch_game(inputs.get("game_name", ""))
        elif name == "list_installed_steam_games":
            from vadox.tools.gaming import list_installed_steam_games
            return list_installed_steam_games()
        elif name == "get_steam_game_info":
            from vadox.tools.gaming import get_steam_game_info
            return get_steam_game_info(inputs.get("game_name", ""))
        elif name == "launch_steam":
            from vadox.tools.gaming import launch_steam
            return launch_steam()
        elif name == "launch_epic":
            from vadox.tools.gaming import launch_epic
            return launch_epic()

        # ── System-Steuerung ──────────────────────────────────────────────────
        elif name == "set_volume":
            from vadox.tools.system_control import set_volume as _sv
            return _sv(inputs.get("level", 50))
        elif name == "get_volume":
            from vadox.tools.system_control import get_volume
            return get_volume()
        elif name == "volume_up":
            from vadox.tools.system_control import volume_up
            return volume_up(inputs.get("amount", 10))
        elif name == "volume_down":
            from vadox.tools.system_control import volume_down
            return volume_down(inputs.get("amount", 10))
        elif name == "mute_volume":
            from vadox.tools.system_control import mute_volume
            return mute_volume()
        elif name == "unmute_volume":
            from vadox.tools.system_control import unmute_volume
            return unmute_volume()
        elif name == "empty_recycle_bin":
            from vadox.tools.system_control import empty_recycle_bin
            return empty_recycle_bin()
        elif name == "get_recycle_bin_size":
            from vadox.tools.system_control import get_recycle_bin_size
            return get_recycle_bin_size()
        elif name == "delete_old_files":
            from vadox.tools.system_control import delete_old_files
            return delete_old_files(
                folder=inputs.get("folder", "Downloads"),
                days=inputs.get("days", 30)
            )
        elif name == "clean_temp_files":
            from vadox.tools.system_control import clean_temp_files
            return clean_temp_files()
        elif name == "get_disk_usage":
            from vadox.tools.system_control import get_disk_usage
            return get_disk_usage()
        elif name == "get_large_files":
            from vadox.tools.system_control import get_large_files
            return get_large_files(
                folder=inputs.get("folder", "Downloads"),
                min_size_mb=inputs.get("min_size_mb", 100)
            )
        elif name == "list_running_apps":
            from vadox.tools.system_control import list_running_apps
            return list_running_apps()
        elif name == "kill_application":
            from vadox.tools.system_control import kill_application
            return kill_application(inputs.get("app_name", ""))
        elif name == "shutdown_pc":
            from vadox.tools.system_control import shutdown_pc
            return shutdown_pc(inputs.get("minutes", 0))
        elif name == "restart_pc":
            from vadox.tools.system_control import restart_pc
            return restart_pc(inputs.get("minutes", 0))
        elif name == "cancel_shutdown":
            from vadox.tools.system_control import cancel_shutdown
            return cancel_shutdown()
        elif name == "sleep_pc":
            from vadox.tools.system_control import sleep_pc
            return sleep_pc()
        elif name == "lock_screen":
            from vadox.tools.system_control import lock_screen
            return lock_screen()
        elif name == "set_brightness":
            from vadox.tools.system_control import set_brightness
            return set_brightness(inputs.get("level", 80))
        elif name == "get_clipboard":
            from vadox.tools.system_control import get_clipboard
            return get_clipboard()
        elif name == "set_clipboard":
            from vadox.tools.system_control import set_clipboard
            return set_clipboard(inputs.get("text", ""))

        # ── Telegram ──────────────────────────────────────────────────────────
        elif name == "send_telegram":
            from vadox.tools.telegram_bot import send_telegram
            return send_telegram(inputs.get("message", ""))
        elif name == "get_telegram_updates":
            from vadox.tools.telegram_bot import get_telegram_updates
            return get_telegram_updates()

        # ── PDF-Analyse ───────────────────────────────────────────────────────
        elif name == "analyze_pdf":
            from vadox.tools.pdf_analyzer import analyze_pdf
            result = analyze_pdf(
                pdf_path=inputs.get("pdf_path", ""),
                question=inputs.get("question", "")
            )
            # Präfix-Marker wird vom AI-Engine erkannt und direkt weitergegeben
            if result.startswith("__PDF_ANALYZE__"):
                return result[len("__PDF_ANALYZE__"):]
            return result
        elif name == "find_pdfs":
            from vadox.tools.pdf_analyzer import find_pdfs_on_desktop
            return find_pdfs_on_desktop()

        # ── Spotify ───────────────────────────────────────────────────────────
        elif name == "spotify_play":
            from vadox.tools.spotify import spotify_play
            return spotify_play(inputs.get("query", ""))
        elif name == "spotify_control":
            from vadox.tools.spotify import spotify_control
            return spotify_control(inputs.get("action", "play"))

        # ── Selbstentwicklung ──────────────────────────────────────────────────
        elif name == "create_new_tool":
            from vadox.core.dynamic_tools import register_new_tool
            return register_new_tool(
                tool_name   = inputs.get("tool_name", ""),
                description = inputs.get("description", ""),
                python_code = inputs.get("python_code", ""),
                parameters  = inputs.get("parameters", {}),
            )
        elif name == "list_custom_tools":
            from vadox.core.dynamic_tools import list_custom_tools
            return list_custom_tools()

        # ── Nutzer-Regeln ──────────────────────────────────────────────────────
        elif name == "add_user_rule":
            from vadox.core.user_rules import add_rule
            return add_rule(inputs.get("trigger", ""), inputs.get("action", ""))
        elif name == "add_user_instruction":
            from vadox.core.user_rules import add_instruction
            return add_instruction(inputs.get("instruction", ""))
        elif name == "list_user_rules":
            from vadox.core.user_rules import list_rules
            return list_rules()
        elif name == "remove_user_rule":
            from vadox.core.user_rules import remove_rule
            return remove_rule(inputs.get("trigger", ""))

        # ── Feedback ───────────────────────────────────────────────────────────
        elif name == "get_feedback_stats":
            from vadox.core.feedback import get_stats
            return get_stats()

        # ── Computer Use — Desktop & Browser ──────────────────────────────────
        elif name == "computer_find_and_click":
            from vadox.tools.computer_use import computer_find_and_click
            return computer_find_and_click(
                element_description=inputs.get("element_description", ""),
                double_click=inputs.get("double_click", False)
            )
        elif name == "computer_click":
            from vadox.tools.computer_use import computer_click
            return computer_click(
                x=inputs.get("x", -1), y=inputs.get("y", -1),
                button=inputs.get("button", "left"),
                double=inputs.get("double", False)
            )
        elif name == "computer_type":
            from vadox.tools.computer_use import computer_type
            return computer_type(
                text=inputs.get("text", ""),
                delay=inputs.get("delay", 0.05)
            )
        elif name == "computer_key":
            from vadox.tools.computer_use import computer_key
            return computer_key(inputs.get("key", ""))
        elif name == "computer_scroll":
            from vadox.tools.computer_use import computer_scroll
            return computer_scroll(
                direction=inputs.get("direction", "down"),
                amount=inputs.get("amount", 3)
            )
        elif name == "computer_drag":
            from vadox.tools.computer_use import computer_drag
            return computer_drag(
                from_x=inputs.get("from_x", 0), from_y=inputs.get("from_y", 0),
                to_x=inputs.get("to_x", 0), to_y=inputs.get("to_y", 0),
                duration=inputs.get("duration", 0.5)
            )
        elif name == "computer_read_screen":
            from vadox.tools.computer_use import computer_read_screen
            return computer_read_screen(inputs.get("region_description", ""))
        elif name == "computer_screenshot":
            from vadox.tools.computer_use import computer_screenshot
            return computer_screenshot(inputs.get("save_path", ""))
        elif name == "computer_wait":
            from vadox.tools.computer_use import computer_wait
            return computer_wait(inputs.get("seconds", 1.0))
        elif name == "browser_computer_use":
            from vadox.tools.computer_use import browser_computer_use
            return browser_computer_use(
                url=inputs.get("url", ""),
                task=inputs.get("task", "")
            )

        else:
            return f"Unbekanntes Tool: {name}"
    except Exception as e:
        return f"Tool-Fehler ({name}): {e}"
