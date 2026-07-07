"""
Screen AI — macht Screenshot und lässt die KI beschreiben was auf dem Bildschirm ist.
Nutzt mss für schnelle Screenshots + KI-Vision für Analyse.
"""
import base64
import io
import os
import time
from pathlib import Path

from vadox.core import settings


def take_screenshot(monitor: int = 0) -> str:
    """Macht einen Screenshot und speichert ihn temporär."""
    try:
        import mss
        import mss.tools

        with mss.mss() as sct:
            monitors = sct.monitors
            # monitor 0 = alle Bildschirme, 1 = erster Monitor
            mon = monitors[monitor] if monitor < len(monitors) else monitors[1]
            img = sct.grab(mon)

            # Als PNG speichern
            tmp = Path(os.environ.get("TEMP", "/tmp")) / "vadox_screen.png"
            mss.tools.to_png(img.rgb, img.size, output=str(tmp))
            return str(tmp)

    except Exception as e:
        return f"Screenshot Fehler: {e}"


def analyze_screen(question: str = "Was siehst du auf dem Bildschirm?") -> str:
    """
    Macht Screenshot und analysiert ihn mit KI.
    question: Was soll die KI über den Bildschirm beantworten?
    """
    try:
        # Screenshot machen
        path = take_screenshot()
        if path.startswith("Screenshot Fehler"):
            return path

        # Bild als Base64 kodieren
        img_data = Path(path).read_bytes()
        b64      = base64.standard_b64encode(img_data).decode("utf-8")

        cfg    = settings.load()
        engine = cfg.get("ai_engine", "claude")

        # Je nach KI-Engine unterschiedliche Vision-API nutzen
        if engine == "claude":
            return _analyze_claude(b64, question, cfg)
        elif engine == "gemini":
            return _analyze_gemini(b64, question, cfg)
        elif engine == "gpt4":
            return _analyze_gpt4(b64, question, cfg)
        else:
            return _analyze_claude(b64, question, cfg)

    except Exception as e:
        return f"Screen AI Fehler: {e}"


def _analyze_claude(b64: str, question: str, cfg: dict) -> str:
    try:
        import anthropic
        api_key = cfg.get("api_key", "") or cfg.get("claude_api_key", "") or os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return "Kein Claude API-Key hinterlegt."

        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type":       "image",
                        "source":     {"type": "base64", "media_type": "image/png", "data": b64},
                    },
                    {"type": "text", "text": question},
                ],
            }],
        )
        return msg.content[0].text

    except Exception as e:
        return f"Claude Vision Fehler: {e}"


def _analyze_gemini(b64: str, question: str, cfg: dict) -> str:
    try:
        import google.generativeai as genai
        api_key = cfg.get("gemini_api_key", "") or os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return "Kein Gemini API-Key hinterlegt."

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        import PIL.Image
        img = PIL.Image.open(io.BytesIO(base64.b64decode(b64)))
        response = model.generate_content([question, img])
        return response.text

    except Exception as e:
        return f"Gemini Vision Fehler: {e}"


def _analyze_gpt4(b64: str, question: str, cfg: dict) -> str:
    try:
        from openai import OpenAI
        api_key = cfg.get("openai_api_key", "") or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            return "Kein OpenAI API-Key hinterlegt."

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }],
            max_tokens=1024,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"GPT-4 Vision Fehler: {e}"


def find_on_screen(what: str) -> str:
    """Sucht ein bestimmtes Element auf dem Bildschirm und gibt Position zurück."""
    return analyze_screen(
        f"Suche auf dem Bildschirm nach: '{what}'. "
        f"Beschreibe wo es sich befindet (oben/unten/links/rechts, ungefähre Position). "
        f"Falls nicht vorhanden, sage das klar."
    )


def read_screen_text() -> str:
    """Liest den gesamten Text vom Bildschirm."""
    return analyze_screen(
        "Lies allen sichtbaren Text vom Bildschirm ab und gib ihn strukturiert zurück. "
        "Ignoriere Hintergründe und Dekorationen, nur der eigentliche Textinhalt."
    )
