"""
System-Check
------------
Prueft beim Start, ob alle externen Voraussetzungen vorhanden sind (VLC, ffmpeg,
Wake-Word-Modelle). Fehlendes wird dem Nutzer freundlich angezeigt — was sicher
automatisch nachinstalliert werden kann (Wake-Word-Modelle), bietet einen
Ein-Klick-Fix; System-Software (VLC/ffmpeg) wird mit Download-Link angeleitet.

Die App laeuft immer weiter — der Check blockiert nichts, er hilft nur.
"""
import shutil
import sys


def _vlc_ok() -> bool:
    """libVLC ladbar? (VLC installiert) — noetig fuer Live-Webcams."""
    try:
        import vlc
        return vlc.Instance("--quiet") is not None
    except Exception:
        return False


def _ffmpeg_ok() -> bool:
    return shutil.which("ffmpeg") is not None


def _wakeword_models_ok() -> bool:
    try:
        from pathlib import Path
        import openwakeword
        base = Path(openwakeword.__file__).parent / "resources" / "models"
        return base.exists() and any(base.glob("*.onnx"))
    except Exception:
        return False


def _download_wakeword_models() -> bool:
    try:
        import openwakeword.utils as u
        u.download_models()
        return True
    except Exception as e:
        print(f"[SystemCheck] Wake-Word-Download fehlgeschlagen: {e}")
        return False


_VLC_URL     = "https://www.videolan.org/vlc/"
_FFMPEG_URL  = "https://ffmpeg.org/download.html"


def check() -> list:
    """Gibt eine Liste offener Punkte zurueck. Leere Liste = alles ok.

    Jeder Punkt: {
        "name": str, "hint": str,
        "fix": callable|None (automatischer Fix, gibt bool zurueck),
        "url": str|None (Download-Seite fuer manuelle Installation),
    }
    """
    issues = []

    if not _wakeword_models_ok():
        issues.append({
            "name": "Wake-Word-Modelle",
            "hint": "Die 'Hey Jarvis'-Modelle fehlen. Vadox kann sie automatisch laden.",
            "fix": _download_wakeword_models,
            "url": None,
        })

    if not _vlc_ok():
        issues.append({
            "name": "VLC Media Player",
            "hint": "Wird für die Live-Webcams benötigt. Bitte kostenlos installieren.",
            "fix": None,
            "url": _VLC_URL,
        })

    if not _ffmpeg_ok():
        issues.append({
            "name": "FFmpeg",
            "hint": "Empfohlen für Audio/Video-Verarbeitung. Bitte installieren.",
            "fix": None,
            "url": _FFMPEG_URL,
        })

    return issues
