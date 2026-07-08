# -*- coding: utf-8 -*-
"""
VLC-Video-Kachel
----------------
Spielt einen direkten Video-Stream (HLS/H.264) per libVLC ab und rendert ihn in
ein Qt-Widget. Nutzt die System-Codecs von VLC — anders als der eingebaute
Chromium (QWebEngine) kann VLC H.264-Live-Streams abspielen.
"""
import sys
from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt, QTimer

_instance = None
_available = None


def vlc_available() -> bool:
    """True, wenn libVLC geladen werden kann (VLC installiert)."""
    global _available
    if _available is None:
        _available = _get_instance() is not None
    return _available


def _get_instance():
    global _instance, _available
    if _instance is not None:
        return _instance
    try:
        import vlc
        _instance = vlc.Instance("--quiet", "--no-xlib", "--network-caching=1500")
        _available = _instance is not None
    except Exception:
        _instance = None
        _available = False
    return _instance


class VlcTile(QFrame):
    """Ein Kachel-Widget, das einen Stream per VLC abspielt."""

    def __init__(self, stream_url: str, parent=None):
        super().__init__(parent)
        self._url = stream_url
        self._player = None
        self._stopped = False
        self.setStyleSheet("background:#000;")
        self.setMinimumHeight(240)
        # Klick/Interaktion an das native Fenster durchreichen
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        # Nach dem Anzeigen starten (native Fenster-ID muss existieren)
        QTimer.singleShot(150, self._start)

    def _start(self):
        # Wurde die Kachel schon geschlossen, bevor der Timer feuerte? Dann NICHT
        # mehr starten — sonst spielt ein verwaister Player weiter (Ton-Bug).
        if self._stopped:
            return
        inst = _get_instance()
        if inst is None or not self._url:
            return
        try:
            self._player = inst.media_player_new()
            media = inst.media_new(self._url)
            self._player.set_media(media)
            self._bind_window()
            self._player.play()
        except Exception:
            self._player = None

    def _bind_window(self):
        wid = int(self.winId())
        p = self._player
        if sys.platform.startswith("linux"):
            p.set_xwindow(wid)
        elif sys.platform == "win32":
            p.set_hwnd(wid)
        elif sys.platform == "darwin":
            p.set_nsobject(wid)

    def stop(self):
        # Merken, dass gestoppt wurde — verhindert einen spaeter feuernden
        # _start-Timer (sonst verwaister Player mit weiterlaufendem Ton).
        self._stopped = True
        if self._player is not None:
            try:
                self._player.stop()
            except Exception:
                pass
            try:
                self._player.release()   # Ressourcen/Audio vollstaendig freigeben
            except Exception:
                pass
            self._player = None
