"""
Vadox Smart Home Panel — Philips Hue, Shelly, Home Assistant
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QLineEdit, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import threading

BG    = "#050d1a"
CARD  = "#071525"
BORDER= "#0a2540"
CYAN  = "#00c8ff"
CYAN_D= "#2a7aaa"
GREEN = "#00ff88"
AMBER = "#ffaa00"
RED   = "#ff3333"
TEXT  = "#5ab4d8"
TEXTD = "#3a8aaa"
PINK  = "#ff6ec7"
PURPLE= "#a855f7"


def _lbl(text, size=10, color=TEXT, bold=False):
    l = QLabel(text)
    l.setFont(QFont("Courier New", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    l.setStyleSheet(f"color:{color}; background:transparent;")
    return l


def _btn(label, color=CYAN, bg="transparent", size=9):
    b = QPushButton(label)
    b.setFixedHeight(32)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFont(QFont("Courier New", size, QFont.Weight.Bold))
    b.setStyleSheet(f"""
        QPushButton {{ background:{bg}; border:1px solid {color};
            color:{color}; border-radius:6px; padding:0 12px; }}
        QPushButton:hover {{ background:{color}22; }}
    """)
    return b


class ScanWorker(QThread):
    done = pyqtSignal(dict)

    def run(self):
        from vadox.tools.smarthome import hue_list_lights, ha_list_devices, _shelly_devices, _hue_base, _cfg
        result = {"hue": [], "shelly": [], "ha": "", "hue_ok": False, "ha_ok": False}
        try:
            if _hue_base():
                lights = hue_list_lights()
                result["hue"] = lights
                result["hue_ok"] = True
        except Exception:
            pass
        try:
            cfg = _cfg()
            if cfg.get("ha_token"):
                result["ha"] = ha_list_devices()
                result["ha_ok"] = True
        except Exception:
            pass
        try:
            result["shelly"] = _shelly_devices()
        except Exception:
            pass
        self.done.emit(result)


class SmartHomePanel(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VADOX — Smart Home")
        self.setMinimumSize(780, 600)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background:{BG}; }}")
        self._build()
        QTimer.singleShot(300, self._scan_devices)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Titelleiste
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"background:#040c18; border-bottom:1px solid {BORDER};")
        b_lay = QHBoxLayout(bar)
        b_lay.setContentsMargins(20, 0, 20, 0)
        b_lay.addWidget(_lbl("SMART HOME", size=13, color=CYAN, bold=True))
        b_lay.addSpacing(16)
        self._status_dot = QFrame()
        self._status_dot.setFixedSize(8, 8)
        self._status_dot.setStyleSheet(f"background:{AMBER}; border-radius:4px;")
        b_lay.addWidget(self._status_dot)
        self._status_lbl = _lbl("Suche Geräte...", size=9, color=AMBER)
        b_lay.addWidget(self._status_lbl)
        b_lay.addStretch()
        refresh_btn = _btn("↻  Aktualisieren", color=CYAN_D, size=9)
        refresh_btn.setFixedWidth(130)
        refresh_btn.clicked.connect(self._scan_devices)
        b_lay.addWidget(refresh_btn)
        b_lay.addSpacing(8)
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"background:transparent; color:{TEXTD}; font-size:14px; border:none;")
        close_btn.clicked.connect(self.accept)
        b_lay.addWidget(close_btn)
        lay.addWidget(bar)

        # Scroll-Inhalt
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{BG}; }}
            QScrollBar:vertical {{ width:4px; background:{BG}; }}
            QScrollBar::handle:vertical {{ background:{CYAN_D}; border-radius:2px; }}
        """)
        self._content = QWidget()
        self._content.setStyleSheet(f"background:{BG};")
        self._content_lay = QVBoxLayout(self._content)
        self._content_lay.setContentsMargins(20, 20, 20, 20)
        self._content_lay.setSpacing(20)
        scroll.setWidget(self._content)
        lay.addWidget(scroll, stretch=1)

        # Fußzeile
        foot = QFrame()
        foot.setFixedHeight(44)
        foot.setStyleSheet(f"background:#040c18; border-top:1px solid {BORDER};")
        f_lay = QHBoxLayout(foot)
        f_lay.setContentsMargins(20, 0, 20, 0)
        self._log_lbl = _lbl("", size=9, color=TEXTD)
        f_lay.addWidget(self._log_lbl)
        f_lay.addStretch()
        close2 = _btn("Schließen", color=CYAN_D)
        close2.setFixedWidth(110)
        close2.clicked.connect(self.accept)
        f_lay.addWidget(close2)
        lay.addWidget(foot)

    def _clear_content(self):
        while self._content_lay.count():
            item = self._content_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _scan_devices(self):
        self._status_lbl.setText("Suche Geräte...")
        self._status_lbl.setStyleSheet(f"color:{AMBER}; background:transparent;")
        self._status_dot.setStyleSheet(f"background:{AMBER}; border-radius:4px;")
        self._clear_content()
        self._content_lay.addWidget(_lbl("Geräte werden gesucht...", size=10, color=TEXTD))
        worker = ScanWorker(self)
        worker.done.connect(self._on_scan_done)
        worker.start()
        self._worker = worker

    def _on_scan_done(self, result: dict):
        self._clear_content()
        has_any = result["hue_ok"] or result["ha_ok"] or result["shelly"]

        if not has_any:
            self._build_not_configured()
            self._status_lbl.setText("Nicht konfiguriert")
            self._status_lbl.setStyleSheet(f"color:{AMBER}; background:transparent;")
            self._status_dot.setStyleSheet(f"background:{AMBER}; border-radius:4px;")
        else:
            total = len(result["hue"]) + len(result["shelly"])
            self._status_lbl.setText(f"Verbunden — {total} Geräte gefunden")
            self._status_lbl.setStyleSheet(f"color:{GREEN}; background:transparent;")
            self._status_dot.setStyleSheet(f"background:{GREEN}; border-radius:4px;")

        # Schnell-Aktionen (immer anzeigen)
        self._build_quick_actions()

        # Philips Hue
        if result["hue"] or result["hue_ok"]:
            self._build_hue_section(result["hue"])

        # Shelly
        if result["shelly"]:
            self._build_shelly_section(result["shelly"])

        # Home Assistant
        if result["ha"]:
            self._build_ha_section(result["ha"])

        # Einrichtungs-Hilfe falls nichts verbunden
        if not has_any:
            self._build_setup_guide()

        self._content_lay.addStretch()

    def _build_quick_actions(self):
        section = self._section_frame("⚡  SCHNELL-AKTIONEN")
        grid = QGridLayout()
        grid.setSpacing(10)

        actions = [
            ("💡 Alles AN",     GREEN,  lambda: self._run_cmd("Licht an")),
            ("🌙 Alles AUS",    CYAN_D, lambda: self._run_cmd("Licht aus")),
            ("🎬 Film-Modus",   PURPLE, lambda: self._run_cmd("Szene Film")),
            ("😴 Schlafen",     AMBER,  lambda: self._run_cmd("Szene Nacht")),
            ("☀️ Tageslicht",   CYAN,   lambda: self._run_cmd("Szene Tageslicht")),
            ("🎉 Party",        PINK,   lambda: self._run_cmd("Szene Party")),
        ]
        for i, (label, color, fn) in enumerate(actions):
            b = _btn(label, color=color, size=10)
            b.setFixedHeight(42)
            b.clicked.connect(fn)
            grid.addWidget(b, i // 3, i % 3)

        section.layout().addLayout(grid)
        self._content_lay.addWidget(section)

    def _build_hue_section(self, lights: list):
        section = self._section_frame(f"💡  PHILIPS HUE  ({len(lights)} Lampen)")
        if not lights:
            section.layout().addWidget(_lbl("Keine Lampen gefunden — Bridge erreichbar?", size=9, color=AMBER))
            self._content_lay.addWidget(section)
            return

        grid = QGridLayout()
        grid.setSpacing(8)
        for i, light in enumerate(lights):
            card = QFrame()
            is_on = light["on"]
            border_color = CYAN if is_on else BORDER
            card.setStyleSheet(f"background:{CARD}; border:1px solid {border_color}; border-radius:8px;")
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(12, 10, 12, 10)
            c_lay.setSpacing(6)

            top = QHBoxLayout()
            icon = "💡" if is_on else "🔴"
            top.addWidget(_lbl(f"{icon}  {light['name']}", size=10, color=CYAN if is_on else TEXTD, bold=True))
            top.addStretch()
            top.addWidget(_lbl("AN" if is_on else "AUS", size=9, color=GREEN if is_on else RED))
            c_lay.addLayout(top)

            bri = int(light["brightness"] / 2.54)
            c_lay.addWidget(_lbl(f"Helligkeit: {bri}%", size=8, color=TEXTD))

            btn_row = QHBoxLayout()
            on_btn = _btn("AN", color=GREEN, size=8)
            off_btn = _btn("AUS", color=RED, size=8)
            lid = light["id"]
            on_btn.clicked.connect(lambda _, i=lid: self._hue_toggle(i, True))
            off_btn.clicked.connect(lambda _, i=lid: self._hue_toggle(i, False))
            btn_row.addWidget(on_btn)
            btn_row.addWidget(off_btn)
            c_lay.addLayout(btn_row)

            grid.addWidget(card, i // 2, i % 2)

        section.layout().addLayout(grid)
        self._content_lay.addWidget(section)

    def _build_shelly_section(self, devices: list):
        section = self._section_frame(f"🔌  SHELLY GERÄTE  ({len(devices)})")
        for d in devices:
            card = QFrame()
            card.setStyleSheet(f"background:{CARD}; border:1px solid {BORDER}; border-radius:8px;")
            c_lay = QHBoxLayout(card)
            c_lay.setContentsMargins(14, 10, 14, 10)
            c_lay.addWidget(_lbl(f"🔌  {d['name']}", size=10, color=CYAN))
            c_lay.addWidget(_lbl(f"IP: {d.get('ip','?')}", size=8, color=TEXTD))
            c_lay.addStretch()
            on_btn  = _btn("AN",  color=GREEN, size=9)
            off_btn = _btn("AUS", color=RED,   size=9)
            name = d["name"]
            on_btn.clicked.connect(lambda _, n=name: self._shelly_toggle(n, True))
            off_btn.clicked.connect(lambda _, n=name: self._shelly_toggle(n, False))
            c_lay.addWidget(on_btn)
            c_lay.addWidget(off_btn)
            section.layout().addWidget(card)
        self._content_lay.addWidget(section)

    def _build_ha_section(self, ha_text: str):
        section = self._section_frame("🏠  HOME ASSISTANT")
        section.layout().addWidget(_lbl(ha_text, size=9, color=TEXT))
        self._content_lay.addWidget(section)

    def _build_not_configured(self):
        card = QFrame()
        card.setStyleSheet(f"background:{CARD}; border:1px solid {AMBER}; border-radius:10px;")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(8)
        c_lay.addWidget(_lbl("⚠️  Noch kein Smart Home konfiguriert", size=11, color=AMBER, bold=True))
        c_lay.addWidget(_lbl(
            "Verbinde dein Smart Home in den Einstellungen → SMART HOME\n"
            "Unterstützt: Philips Hue · Shelly · Home Assistant",
            size=9, color=TEXTD
        ))
        self._content_lay.addWidget(card)

    def _build_setup_guide(self):
        section = self._section_frame("📋  EINRICHTUNGS-ANLEITUNG")
        guides = [
            ("💡 Philips Hue",
             "1. Hue Bridge mit LAN verbinden\n2. Bridge-IP in Einstellungen eingeben\n3. Bridge-Knopf drücken → API-Key wird automatisch erstellt"),
            ("🔌 Shelly",
             "1. Shelly Gerät im WLAN einrichten (Shelly App)\n2. IP-Adresse des Geräts herausfinden\n3. In Vadox Einstellungen Namen + IP eingeben"),
            ("🏠 Home Assistant",
             "1. Home Assistant auf Raspberry Pi oder PC installieren\n2. Einstellungen → Profil → Langzeit-Zugriffstoken erstellen\n3. IP + Token in Vadox eingeben"),
        ]
        for title, text in guides:
            card = QFrame()
            card.setStyleSheet(f"background:{CARD}; border:1px solid {BORDER}; border-radius:8px;")
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(14, 10, 14, 10)
            c_lay.addWidget(_lbl(title, size=10, color=CYAN, bold=True))
            c_lay.addWidget(_lbl(text, size=9, color=TEXTD))
            section.layout().addWidget(card)
        self._content_lay.addWidget(section)

    def _section_frame(self, title: str) -> QFrame:
        f = QFrame()
        f.setStyleSheet(f"background:transparent;")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.addWidget(_lbl(title, size=10, color=CYAN, bold=True))
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{BORDER};")
        lay.addWidget(sep)
        return f

    def _run_cmd(self, cmd: str):
        self._log_lbl.setText(f"Ausführe: {cmd}...")
        def _do():
            from vadox.tools.smarthome import smarthome_command
            result = smarthome_command(cmd)
            QTimer.singleShot(0, lambda: self._on_cmd_done(result))
        threading.Thread(target=_do, daemon=True).start()

    def _on_cmd_done(self, result: str):
        self._log_lbl.setText(result[:80])
        QTimer.singleShot(500, self._scan_devices)

    def _hue_toggle(self, light_id: str, on: bool):
        def _do():
            from vadox.tools.smarthome import hue_set_light
            hue_set_light(light_id, on)
            QTimer.singleShot(0, self._scan_devices)
        threading.Thread(target=_do, daemon=True).start()

    def _shelly_toggle(self, name: str, on: bool):
        def _do():
            from vadox.tools.smarthome import shelly_set
            result = shelly_set(name, on)
            QTimer.singleShot(0, lambda: self._log_lbl.setText(result[:80]))
        threading.Thread(target=_do, daemon=True).start()
