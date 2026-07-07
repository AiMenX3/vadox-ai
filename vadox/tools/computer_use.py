"""
Vadox Computer Use — Browser & Desktop vollständig steuern
Kombiniert Screenshot-KI + pyautogui für komplette PC-Kontrolle
"""
import time
import base64
import platform
import subprocess
from pathlib import Path

_pl = platform.system()


def _screenshot_base64() -> str:
    """Screenshot als base64 für KI-Analyse — nutzt mss für Zuverlässigkeit."""
    try:
        import mss
        import mss.tools
        import io
        from PIL import Image
        with mss.mss() as sct:
            mon = sct.monitors[1]
            img = sct.grab(mon)
            # mss gibt BGRA zurück → PIL konvertieren
            pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        # Fallback pyautogui
        import pyautogui
        import io
        img = pyautogui.screenshot()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()


def _log(msg: str):
    """Schreibt Debugging-Infos in Log-Datei."""
    import sys
    try:
        log = (Path(sys.executable).parent / "vadox_computer_use.log"
               if getattr(sys, 'frozen', False)
               else Path(__file__).parent.parent.parent / "vadox_computer_use.log")
        from datetime import datetime
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def _ask_ai_for_coordinates(screenshot_b64: str, task: str) -> dict:
    """
    Sendet Screenshot an Claude und fragt nach Koordinaten für eine Aktion.
    """
    from vadox.core import settings as _settings
    import anthropic

    cfg = _settings.load()
    api_key = cfg.get("api_key", "")
    if not api_key:
        _log("FEHLER: Kein API-Key in settings")
        return {"error": "Kein API-Key"}

    client = anthropic.Anthropic(api_key=api_key)

    import pyautogui
    screen_w, screen_h = pyautogui.size()

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": screenshot_b64,
                    }
                },
                {
                    "type": "text",
                    "text": (
                        f"Bildschirmauflösung: {screen_w}x{screen_h}px.\n"
                        f"Aufgabe: {task}\n\n"
                        "Antworte NUR mit JSON im Format:\n"
                        '{"x": <pixel_x>, "y": <pixel_y>, "confidence": <0-100>, "element": "<was du siehst>"}\n'
                        "Gib die exakten Pixel-Koordinaten des gesuchten Elements an. "
                        "Wenn das Element nicht sichtbar ist: {\"x\": -1, \"y\": -1, \"confidence\": 0, \"element\": \"nicht gefunden\"}"
                    )
                }
            ]
        }]
    )

    import json, re
    text = response.content[0].text
    _log(f"KI Antwort: {text[:200]}")
    match = re.search(r'\{[^}]+\}', text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            _log(f"Koordinaten: x={result.get('x')}, y={result.get('y')}, conf={result.get('confidence')}")
            return result
        except Exception as e:
            _log(f"JSON Parsing Fehler: {e} — Text: {match.group()}")
    _log(f"Kein JSON gefunden in: {text}")
    return {"x": -1, "y": -1, "confidence": 0, "element": "Parsing-Fehler"}


# ── Desktop Computer Use Tools ────────────────────────────────────────────────

def computer_screenshot(save_path: str = "") -> str:
    """Screenshot machen und optional speichern."""
    try:
        import pyautogui
        img = pyautogui.screenshot()
        if save_path:
            img.save(save_path)
            return f"Screenshot gespeichert: {save_path}"
        else:
            p = Path.home() / "Desktop" / f"vadox_screenshot_{int(time.time())}.png"
            img.save(str(p))
            return f"Screenshot gespeichert: {p}"
    except Exception as e:
        return f"Fehler: {e}"


def computer_click(x: int = -1, y: int = -1, element_description: str = "",
                   button: str = "left", double: bool = False) -> str:
    """
    Klickt auf Koordinaten oder sucht Element per KI.
    """
    try:
        import pyautogui
        pyautogui.FAILSAFE = False  # Kein Abbruch wenn Maus in Ecke

        if x == -1 and element_description:
            _log(f"computer_click: suche '{element_description}'")
            b64 = _screenshot_base64()
            result = _ask_ai_for_coordinates(b64, f"Finde und zeige mir die Koordinaten von: {element_description}")
            x = result.get("x", -1)
            y = result.get("y", -1)
            conf = result.get("confidence", 0)
            _log(f"Gefunden: x={x}, y={y}, conf={conf}")
            if x == -1 or conf < 30:
                return f"Element '{element_description}' nicht gefunden (Konfidenz: {conf}%)"

        _log(f"computer_click: klicke ({x}, {y}), button={button}, double={double}")
        if double:
            pyautogui.doubleClick(x, y)
        elif button == "right":
            pyautogui.rightClick(x, y)
        else:
            pyautogui.click(x, y)

        time.sleep(0.3)
        _log(f"computer_click: Klick auf ({x}, {y}) erfolgreich")
        return f"Geklickt auf ({x}, {y})"
    except Exception as e:
        _log(f"FEHLER in computer_click: {e}")
        import traceback
        _log(traceback.format_exc())
        return f"Fehler beim Klicken: {e}"


def computer_type(text: str, delay: float = 0.05) -> str:
    """Text tippen (in aktives Fenster/Feld)."""
    try:
        import pyautogui
        time.sleep(0.2)
        pyautogui.write(text, interval=delay)
        return f"Text eingegeben: {text[:50]}{'...' if len(text) > 50 else ''}"
    except Exception as e:
        return f"Fehler beim Tippen: {e}"


def computer_key(key: str) -> str:
    """
    Taste oder Tastenkombination drücken.
    Beispiele: 'enter', 'tab', 'ctrl+c', 'ctrl+v', 'alt+f4', 'win'
    """
    try:
        import pyautogui
        time.sleep(0.1)
        if '+' in key:
            keys = [k.strip() for k in key.split('+')]
            pyautogui.hotkey(*keys)
        else:
            pyautogui.press(key)
        return f"Taste gedrückt: {key}"
    except Exception as e:
        return f"Fehler: {e}"


def computer_scroll(direction: str = "down", amount: int = 3,
                    x: int = -1, y: int = -1) -> str:
    """Scrollen. direction: 'up' oder 'down'."""
    try:
        import pyautogui
        clicks = -amount if direction == "down" else amount
        if x != -1 and y != -1:
            pyautogui.scroll(clicks, x=x, y=y)
        else:
            pyautogui.scroll(clicks)
        return f"Gescrollt {direction} ({amount}x)"
    except Exception as e:
        return f"Fehler: {e}"


def computer_drag(from_x: int, from_y: int, to_x: int, to_y: int,
                  duration: float = 0.5) -> str:
    """Drag & Drop von einer Position zu einer anderen."""
    try:
        import pyautogui
        pyautogui.moveTo(from_x, from_y, duration=0.2)
        pyautogui.dragTo(to_x, to_y, duration=duration, button='left')
        return f"Drag & Drop: ({from_x},{from_y}) → ({to_x},{to_y})"
    except Exception as e:
        return f"Fehler: {e}"


def computer_move_mouse(x: int, y: int) -> str:
    """Maus zu Position bewegen ohne zu klicken."""
    try:
        import pyautogui
        pyautogui.moveTo(x, y, duration=0.2)
        return f"Maus bewegt zu ({x}, {y})"
    except Exception as e:
        return f"Fehler: {e}"


def computer_find_and_click(element_description: str, double_click: bool = False) -> str:
    """
    KI sucht Element auf dem Bildschirm und klickt es an.
    """
    try:
        import pyautogui
        _log(f"computer_find_and_click: '{element_description}'")
        b64 = _screenshot_base64()
        _log(f"Screenshot erstellt, Laenge: {len(b64)}")
        result = _ask_ai_for_coordinates(
            b64,
            f"Finde das Element: '{element_description}'. Gib exakte Klick-Koordinaten."
        )
        x = result.get("x", -1)
        y = result.get("y", -1)
        conf = result.get("confidence", 0)
        elem = result.get("element", "")
        _log(f"Koordinaten: x={x}, y={y}, conf={conf}, elem={elem}")

        if x == -1 or conf < 25:
            return f"Element '{element_description}' nicht auf dem Bildschirm gefunden (Konfidenz: {conf}%)."

        _log(f"Klicke jetzt auf ({x}, {y})")
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)
        if double_click:
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.click(x, y)

        time.sleep(0.5)
        _log(f"Klick erfolgreich!")
        return f"Geklickt auf '{elem}' an Position ({x}, {y}) — Konfidenz: {conf}%"
    except Exception as e:
        _log(f"FEHLER in computer_find_and_click: {e}")
        import traceback
        _log(traceback.format_exc())
        return f"Fehler beim Klicken: {e}"


def computer_read_screen(region_description: str = "") -> str:
    """Bildschirminhalt per KI lesen und beschreiben."""
    try:
        from vadox.core import settings as _settings
        import anthropic

        cfg = _settings.load()
        api_key = cfg.get("api_key", "")
        if not api_key:
            return "Kein API-Key konfiguriert."

        b64 = _screenshot_base64()
        client = anthropic.Anthropic(api_key=api_key)

        question = region_description if region_description else "Was siehst du auf dem Bildschirm? Beschreibe alle wichtigen Elemente, Texte und Buttons."

        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
                    {"type": "text", "text": question}
                ]
            }]
        )
        return response.content[0].text
    except Exception as e:
        return f"Fehler beim Lesen: {e}"


def computer_upload_file(file_path: str) -> str:
    """
    Datei hochladen — drückt Strg+V oder füllt einen Datei-Dialog aus.
    Vorher muss ein Upload-Dialog offen sein.
    """
    try:
        import pyautogui
        path = Path(file_path)
        if not path.exists():
            return f"Datei nicht gefunden: {file_path}"

        # In offenen Datei-Dialog eintippen
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.write(str(path), interval=0.02)
        time.sleep(0.2)
        pyautogui.press('enter')
        return f"Datei-Pfad eingegeben: {path.name}"
    except Exception as e:
        return f"Fehler: {e}"


def computer_wait(seconds: float = 1.0) -> str:
    """Warten bis eine Aktion abgeschlossen ist."""
    time.sleep(seconds)
    return f"Gewartet {seconds} Sekunden"


def computer_get_screen_size() -> str:
    """Bildschirmgröße abfragen."""
    try:
        import pyautogui
        w, h = pyautogui.size()
        return f"Bildschirmgröße: {w}x{h} Pixel"
    except Exception as e:
        return f"Fehler: {e}"


# ── Browser Computer Use (Playwright) ────────────────────────────────────────

def browser_computer_use(url: str, task: str) -> str:
    """
    Öffnet Browser und führt eine komplexe Aufgabe per KI-Vision aus.
    Beispiel: url='https://facebook.com', task='Poste in der Gruppe Affiliate Marketing: Hallo!'
    """
    try:
        from playwright.sync_api import sync_playwright
        import anthropic
        from vadox.core.settings import settings
        import io, json, re

        cfg = settings.load()
        api_key = cfg.get("api_key", "")
        if not api_key:
            return "Kein API-Key konfiguriert."

        client = anthropic.Anthropic(api_key=api_key)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=100)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)

            steps_done = []
            max_steps = 15

            for step in range(max_steps):
                # Screenshot der aktuellen Seite
                buf = io.BytesIO()
                page.screenshot(path=None)
                screenshot_bytes = page.screenshot()
                b64 = base64.b64encode(screenshot_bytes).decode()

                # KI entscheidet nächste Aktion
                response = client.messages.create(
                    model="claude-opus-4-8",
                    max_tokens=512,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
                            {"type": "text", "text": (
                                f"Aufgabe: {task}\n"
                                f"Bisher erledigt: {'; '.join(steps_done) if steps_done else 'Nichts'}\n\n"
                                "Was ist der nächste Schritt? Antworte mit JSON:\n"
                                '{"action": "click|type|scroll|wait|done", '
                                '"selector": "<CSS-Selektor oder leer>", '
                                '"text": "<Text zum Tippen oder leer>", '
                                '"x": <x oder -1>, "y": <y oder -1>, '
                                '"reason": "<warum dieser Schritt>", '
                                '"done": <true wenn Aufgabe erledigt>}'
                            )}
                        ]
                    }]
                )

                text = response.content[0].text
                match = re.search(r'\{[^}]+\}', text, re.DOTALL)
                if not match:
                    break

                try:
                    action = json.loads(match.group())
                except Exception:
                    break

                if action.get("done") or action.get("action") == "done":
                    steps_done.append("Aufgabe abgeschlossen")
                    break

                act = action.get("action", "")
                reason = action.get("reason", "")

                if act == "click":
                    sel = action.get("selector", "")
                    ax = action.get("x", -1)
                    ay = action.get("y", -1)
                    try:
                        if sel:
                            page.click(sel, timeout=5000)
                        elif ax != -1:
                            page.mouse.click(ax, ay)
                        steps_done.append(f"Geklickt: {reason}")
                    except Exception:
                        if ax != -1:
                            page.mouse.click(ax, ay)
                        steps_done.append(f"Geklickt (Koordinaten): {reason}")

                elif act == "type":
                    txt = action.get("text", "")
                    sel = action.get("selector", "")
                    try:
                        if sel:
                            page.fill(sel, txt)
                        else:
                            page.keyboard.type(txt)
                        steps_done.append(f"Eingegeben: {txt[:30]}")
                    except Exception as e:
                        steps_done.append(f"Tipp-Fehler: {e}")

                elif act == "scroll":
                    page.mouse.wheel(0, 500)
                    steps_done.append("Gescrollt")

                elif act == "wait":
                    time.sleep(2)
                    steps_done.append("Gewartet")

                time.sleep(1)
                page.wait_for_load_state("domcontentloaded", timeout=10000)

            browser.close()

        return f"Browser-Aufgabe abgeschlossen:\n" + "\n".join(f"  {i+1}. {s}" for i, s in enumerate(steps_done))

    except Exception as e:
        return f"Fehler bei Browser-Steuerung: {e}"
