# -*- coding: utf-8 -*-
"""
Vadox JARVIS-HUD
----------------
Cinematischer Vollbild-Modus: reaktiver Energie-Ring in der Mitte, Live-Uhr,
Datum und System-Werte, plus Schnellzugriff auf die Vadox-Funktionen.

Das klassische UI bleibt unveraendert bestehen — der HUD ist ein zusaetzlicher
Modus, in den der Nutzer per Button wechselt (und per ESC/Button zurueck).
"""
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from vadox.ui.ring_widget import RingWidget

BG     = "#050d1a"
CARD   = "#071525"
BORDER = "#0a2540"
CYAN   = "#00c8ff"
CYAND  = "#2a7aaa"
GREEN  = "#00ff88"
PINK   = "#ff3c78"
TEXT   = "#5ab4d8"

_WD = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
_MO = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
       "September", "Oktober", "November", "Dezember"]


def _lbl(text, size, color, bold=False, spacing=0):
    l = QLabel(text)
    f = QFont("Courier New", size, QFont.Weight.Bold if bold else QFont.Weight.Normal)
    if spacing:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    l.setFont(f)
    l.setStyleSheet(f"color:{color}; background:transparent;")
    return l


class HudWindow(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._mw = main_window
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(f"background:{BG};")
        self._build()

        # Live-Uhr
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        # Sprech-/Zuhoer-Status vom Hauptfenster spiegeln
        self._state_timer = QTimer(self)
        self._state_timer.timeout.connect(self._sync_state)
        self._state_timer.start(120)

        # System-Werte
        try:
            self._mw._monitor.stats_updated.connect(self._on_stats)
        except Exception:
            pass

        # Tool-Ausfuehrung + live mitlaufende Antwort
        self._seen_user_msg = ""
        try:
            self._mw._tool_use_signal.connect(self._on_tool)
            self._mw._chat_chunk_signal.connect(self._on_chunk)
        except Exception:
            pass

        # Ticker/Chip nach kurzer Zeit automatisch ausblenden
        self._ticker_timer = QTimer(self); self._ticker_timer.setSingleShot(True)
        self._ticker_timer.timeout.connect(lambda: self._ticker.setText(""))
        self._chip_timer = QTimer(self); self._chip_timer.setSingleShot(True)
        self._chip_timer.timeout.connect(lambda: self._chip.setText(""))

    def showEvent(self, event):
        super().showEvent(event)
        self._play_boot_intro()

    # ── Aufbau ────────────────────────────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(0)

        # Kopfzeile: links Uhr/Datum, rechts System, ganz rechts Zurueck
        top = QHBoxLayout()
        col_l = QVBoxLayout(); col_l.setSpacing(2)
        self._clock = _lbl("--:--:--", 34, CYAN, bold=True, spacing=2)
        self._date  = _lbl("", 12, CYAND, spacing=1)
        col_l.addWidget(self._clock)
        col_l.addWidget(self._date)
        top.addLayout(col_l)
        top.addStretch()

        col_r = QVBoxLayout(); col_r.setSpacing(2); col_r.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._cpu  = _lbl("CPU  --%", 12, TEXT, spacing=1)
        self._mem  = _lbl("RAM  --%", 12, TEXT, spacing=1)
        self._disk = _lbl("DISK --%", 12, TEXT, spacing=1)
        for w in (self._cpu, self._mem, self._disk):
            w.setAlignment(Qt.AlignmentFlag.AlignRight)
            col_r.addWidget(w)
        top.addLayout(col_r)

        back = QPushButton("✕  KLASSIK  (ESC)")
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        back.setFixedHeight(30)
        back.setStyleSheet(f"""
            QPushButton {{ background:{CARD}; border:1px solid {BORDER};
                color:{CYAND}; border-radius:6px; padding:0 12px; }}
            QPushButton:hover {{ border:1px solid {CYAN}; color:{CYAN}; }}
        """)
        back.clicked.connect(self.close)
        top.addSpacing(16)
        top.addWidget(back, alignment=Qt.AlignmentFlag.AlignTop)
        root.addLayout(top)

        # Tool-Ausfuehrungs-Ticker (erscheint waehrend Vadox ein Tool nutzt)
        self._ticker = _lbl("", 12, "#ffcf5a", bold=True, spacing=1)
        self._ticker.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ticker.setFixedHeight(22)
        root.addSpacing(6)
        root.addWidget(self._ticker)

        # Mitte: Titel + Ring + Status
        root.addStretch()
        self._title = _lbl("V A D O X", 20, CYAN, bold=True, spacing=8)
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._title)
        root.addSpacing(6)

        self._ring = RingWidget()
        self._ring.setFixedSize(360, 360)
        root.addWidget(self._ring, alignment=Qt.AlignmentFlag.AlignCenter)

        self._status = _lbl("● SYSTEM BEREIT", 13, GREEN, bold=True, spacing=3)
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addSpacing(6)
        root.addWidget(self._status)

        # Grosser Mikrofon-Button — startet das Zuhoeren (wie im klassischen UI)
        self._mic_btn = QPushButton("🎙  SPRECHEN")
        self._mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mic_btn.setFont(QFont("Courier New", 13, QFont.Weight.Bold))
        self._mic_btn.setFixedSize(220, 48)
        self._mic_btn.setStyleSheet(f"""
            QPushButton {{ background:#0a2a4a; border:1px solid {CYAN};
                color:{CYAN}; border-radius:24px; letter-spacing:2px; }}
            QPushButton:hover {{ background:#0f3a60; }}
        """)
        self._mic_btn.clicked.connect(self._on_mic)
        root.addSpacing(10)
        root.addWidget(self._mic_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addStretch()

        # Letzte Konversation (DU / VADOX) + Event-Chip
        conv = QVBoxLayout(); conv.setSpacing(3)
        self._q_lbl = _lbl("", 12, CYAND)
        self._q_lbl.setWordWrap(True)
        self._a_lbl = _lbl("", 12, "#7fd0ee", bold=True)
        self._a_lbl.setWordWrap(True)
        conv.addWidget(self._q_lbl)
        conv.addWidget(self._a_lbl)

        chip_row = QHBoxLayout()
        chip_row.addLayout(conv, stretch=1)
        self._chip = _lbl("", 11, GREEN, bold=True, spacing=1)
        self._chip.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        chip_row.addWidget(self._chip)
        root.addLayout(chip_row)
        root.addSpacing(8)

        # Unten: Schnellzugriff-Kacheln
        tiles = [
            ("📹  Live-Cams", lambda: self._open("webcam")),
            ("👨‍💻  Coding",    lambda: self._open("coding")),
            ("🌍  Übersetzer", lambda: self._open("translator")),
            ("🏠  Smart Home", lambda: self._open("smarthome")),
            ("🎓  Lernen",     lambda: self._open("learn")),
            ("⚙️  Einstellungen", lambda: self._open("settings")),
        ]
        grid = QHBoxLayout(); grid.setSpacing(10)
        for label, cb in tiles:
            grid.addWidget(self._tile(label, cb))
        root.addLayout(grid)

    def _tile(self, label, cb) -> QWidget:
        b = QPushButton(label)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        b.setFixedHeight(52)
        b.setStyleSheet(f"""
            QPushButton {{ background:{CARD}; border:1px solid {BORDER};
                color:{CYAN}; border-radius:10px; }}
            QPushButton:hover {{ background:#0a2033; border:1px solid {CYAN}; }}
        """)
        b.clicked.connect(cb)
        return b

    # ── Aktionen ──────────────────────────────────────────────────────────────
    def _open(self, which):
        m = self._mw
        try:
            if which == "webcam":      m._open_webcam_panel("")
            elif which == "coding":    m._open_coding_panel()
            elif which == "translator":m._open_translator_panel()
            elif which == "smarthome": m._open_smarthome_panel()
            elif which == "learn":     m._open_learn_panel()
            elif which == "settings":  m._open_settings()
        except Exception as e:
            print(f"[HUD] Panel-Fehler: {e}")

    def _on_mic(self):
        """Startet das Zuhoeren ueber die vorhandene Mikrofon-Funktion."""
        try:
            self._mw._toggle_mic()
        except Exception as e:
            print(f"[HUD] Mikrofon-Fehler: {e}")

    _TOOL_LABELS = {
        "get_weather": "WETTER ABRUFEN", "web_search": "WEBSUCHE", "news_search": "NACHRICHTEN",
        "search_files": "DATEISUCHE", "read_file": "DATEI LESEN", "create_file": "DATEI ERSTELLEN",
        "take_screenshot": "SCREENSHOT", "open_application": "APP ÖFFNEN", "open_url": "WEBSEITE",
        "show_webcams": "LIVE-KAMERAS", "translate_text": "ÜBERSETZUNG", "send_email": "E-MAIL",
        "get_calendar_events": "KALENDER", "spotify_play": "MUSIK", "smarthome_command": "SMART HOME",
    }

    def _on_tool(self, tool_name: str):
        label = self._TOOL_LABELS.get(tool_name, tool_name.replace("_", " ").upper())
        self._ticker.setText(f"▸ {label} LÄUFT …")
        self._ticker_timer.start(6000)
        # Event-Chip fuer erledigte Aktion
        self._chip.setText(f"✓ {label.title()}")
        self._chip_timer.start(4000)

    def _on_chunk(self, chunk: str):
        # Neue Frage erkannt -> Antwort zuruecksetzen und Frage anzeigen
        cur = getattr(self._mw, "_last_user_msg", "")
        if cur and cur != self._seen_user_msg:
            self._seen_user_msg = cur
            self._q_lbl.setText(f"DU:  {cur[:110]}")
            self._a_lbl.setText("VADOX:  ")
        # Antwort live anhaengen (Schreibmaschinen-Effekt entsteht von selbst)
        txt = self._a_lbl.text()
        if len(txt) < 320:
            self._a_lbl.setText(txt + chunk)

    def _play_boot_intro(self):
        """Kurzes cinematisches Intro: Titel tippt sich Zeichen fuer Zeichen ein."""
        full = "V A D O X"
        self._title.setText("")
        self._status.setText("◇ SYSTEM WIRD HOCHGEFAHREN …")
        self._status.setStyleSheet(f"color:{CYAN}; background:transparent;")

        def _type(i=0):
            if i <= len(full):
                self._title.setText(full[:i])
                QTimer.singleShot(70, lambda: _type(i + 1))
        _type()

    def _update_clock(self):
        now = datetime.now()
        self._clock.setText(now.strftime("%H:%M:%S"))
        self._date.setText(f"{_WD[now.weekday()]}, {now.day}. {_MO[now.month-1]} {now.year}")

    def _sync_state(self):
        speaking  = bool(getattr(self._mw, "_speaking", False))
        listening = bool(getattr(self._mw, "_listening", False))
        thinking  = bool(getattr(self._mw, "_processing", False)) and not speaking
        self._ring.set_state(listening=listening, speaking=speaking, thinking=thinking)
        if speaking:
            self._status.setText("◆ VADOX SPRICHT")
            self._status.setStyleSheet(f"color:{GREEN}; background:transparent;")
            self._mic_btn.setText("🎙  SPRECHEN")
        elif listening:
            self._status.setText("▶ HÖRT ZU …")
            self._status.setStyleSheet(f"color:{PINK}; background:transparent;")
            self._mic_btn.setText("●  HÖRT ZU …")
        elif thinking:
            self._status.setText("◆ VADOX ARBEITET …")
            self._status.setStyleSheet(f"color:{CYAN}; background:transparent;")
            self._mic_btn.setText("🎙  SPRECHEN")
        else:
            self._status.setText("● SYSTEM BEREIT")
            self._status.setStyleSheet(f"color:{GREEN}; background:transparent;")
            self._mic_btn.setText("🎙  SPRECHEN")

    def _on_stats(self, s: dict):
        self._cpu.setText(f"CPU  {int(s.get('cpu', 0))}%")
        self._mem.setText(f"RAM  {int(s.get('mem', 0))}%")
        self._disk.setText(f"DISK {int(s.get('disk', 0))}%")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
