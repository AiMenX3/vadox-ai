# -*- coding: utf-8 -*-
"""
Vadox Live-Webcam Panel
-----------------------
Zeigt bis zu 6 echte oeffentliche Live-Video-Streams (YouTube-Livestreams) in
einem Grid — abgespielt per VLC (native Codecs). Die Stream-URLs werden beim
Oeffnen live per yt-dlp ermittelt, damit keine veralteten Streams auftauchen.
"""
import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QWidget,
    QGridLayout, QComboBox, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from vadox.tools.webcams import get_webcams, CITIES
from vadox.ui.vlc_player import VlcTile, vlc_available

BG     = "#050d1a"
CARD   = "#071525"
BORDER = "#0a2540"
CYAN   = "#00c8ff"
GREEN  = "#00ff88"
TEXT   = "#5ab4d8"
TEXTD  = "#3a8aaa"


class _LoadWorker(QThread):
    done = pyqtSignal(dict)

    def __init__(self, location):
        super().__init__()
        self._location = location

    def run(self):
        try:
            data = get_webcams(self._location, max_cams=6)
        except Exception as e:
            data = {"title": f"Fehler: {e}", "cams": []}
        self.done.emit(data)


class WebcamPanel(QDialog):
    def __init__(self, parent=None, location: str = ""):
        super().__init__(parent)
        self.setWindowTitle("VADOX — Live-Webcams")
        self.resize(1100, 720)
        self.setStyleSheet(f"background:{BG};")
        self._worker = None
        self._tiles = []
        self._closed = False
        self._current_location = location or ""
        self._build()
        self.load_location(location)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"background:#040c18; border-bottom:1px solid {BORDER};")
        b_lay = QHBoxLayout(bar)
        b_lay.setContentsMargins(20, 0, 20, 0)

        self._title = QLabel("🌍  Live-Kameras")
        self._title.setFont(QFont("Courier New", 13, QFont.Weight.Bold))
        self._title.setStyleSheet(f"color:{CYAN}; letter-spacing:1px; background:transparent;")
        b_lay.addWidget(self._title)
        b_lay.addStretch()

        self._combo = QComboBox()
        self._combo.setFixedWidth(220)
        self._combo.setFont(QFont("Courier New", 10))
        self._combo.setStyleSheet(f"""
            QComboBox {{ background:{CARD}; border:1px solid {BORDER};
                color:{CYAN}; border-radius:6px; padding:4px 10px; }}
            QComboBox QAbstractItemView {{ background:{CARD}; color:{TEXT};
                selection-background-color:{BORDER}; }}
        """)
        self._combo.addItem("🌍  Aus aller Welt", "")
        for key, (name, flag, _q) in CITIES.items():
            self._combo.addItem(f"{flag}  {name}", key)
        self._combo.currentIndexChanged.connect(
            lambda: self.load_location(self._combo.currentData())
        )
        b_lay.addWidget(self._combo)
        lay.addWidget(bar)

        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(10, 10, 10, 10)
        self._grid.setSpacing(8)
        lay.addWidget(self._grid_host, stretch=1)

        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setFont(QFont("Courier New", 12))
        self._status.setStyleSheet(f"color:{TEXTD}; background:transparent;")
        lay.addWidget(self._status)

    def _clear_grid(self):
        for t in self._tiles:
            try:
                if hasattr(t, "stop"):
                    t.stop()
            except Exception:
                pass
            t.setParent(None)
            t.deleteLater()
        self._tiles = []
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

    def load_location(self, location: str = ""):
        self._current_location = location or ""
        self._clear_grid()
        if not vlc_available():
            self._status.setText(
                "🎬  VLC wird für Live-Video benötigt.\n\n"
                "Bitte installiere den kostenlosen VLC Media Player von videolan.org,\n"
                "danach funktionieren die Live-Streams automatisch."
            )
            return
        self._status.setText("⏳  Live-Streams werden gesucht …")
        self._combo.setEnabled(False)
        self._worker = _LoadWorker(location or "")
        self._worker.done.connect(self._on_loaded)
        self._worker.start()

    def _on_loaded(self, data: dict):
        if self._closed:
            return  # Fenster wurde waehrend des Ladens geschlossen — keine Player mehr starten
        self._combo.setEnabled(True)
        self._title.setText(data.get("title", "Live-Kameras"))
        cams = data.get("cams", [])
        if not cams:
            self._status.setText("⚠  Gerade keine Live-Streams für diesen Ort gefunden — bitte erneut versuchen.")
            return
        self._status.setText("")
        cols = 3 if len(cams) > 2 else max(1, len(cams))
        for i, cam in enumerate(cams):
            self._grid.addWidget(self._make_tile(cam), i // cols, i % cols)

    def _make_tile(self, cam: dict) -> QWidget:
        box = QFrame()
        box.setStyleSheet(f"background:{CARD}; border:1px solid {BORDER}; border-radius:8px;")
        v = QVBoxLayout(box)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(4)

        row = QHBoxLayout()
        cap = QLabel(f"{cam['flag']}  {cam['city']} · 🔴 LIVE — {cam['title']}")
        cap.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        cap.setStyleSheet(f"color:{CYAN}; background:transparent;")
        cap.setWordWrap(True)
        row.addWidget(cap, stretch=1)

        # Fallback: im echten Browser oeffnen (volle Qualitaet/Ton)
        watch = cam.get("watch_url", "")
        if watch:
            btn = QPushButton("↗")
            btn.setToolTip("Im Browser öffnen")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(f"""
                QPushButton {{ background:{BORDER}; border:none; color:{CYAN};
                    border-radius:4px; }}
                QPushButton:hover {{ background:{CYAN}; color:#000; }}
            """)
            btn.clicked.connect(lambda: webbrowser.open(watch))
            row.addWidget(btn)
        v.addLayout(row)

        tile = VlcTile(cam["stream_url"])
        self._tiles.append(tile)
        v.addWidget(tile, stretch=1)
        return box

    def closeEvent(self, event):
        self._closed = True
        self._clear_grid()
        super().closeEvent(event)
