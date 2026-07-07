from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QCheckBox, QSpinBox,
    QTimeEdit, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QTime
from PyQt6.QtGui import QFont

from vadox.core import agent_scheduler

BG    = "#050d1a"
CARD  = "#071525"
BORDER= "#0a2540"
CYAN  = "#00c8ff"
CYAN_D= "#2a7aaa"
GREEN = "#00ff88"
PINK  = "#ff00aa"
AMBER = "#ffaa00"
TEXT  = "#5ab4d8"
TEXTD = "#3a8aaa"


def _lbl(text, size=10, color=TEXT, bold=False):
    l = QLabel(text)
    l.setFont(QFont("Courier New", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    l.setStyleSheet(f"color:{color}; background:transparent;")
    return l


class AgentCard(QFrame):
    def __init__(self, agent: dict, parent=None):
        super().__init__(parent)
        self._agent = agent
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{ background:{CARD}; border:1px solid {BORDER};
                     border-radius:10px; margin:4px 0; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        # Kopfzeile: Icon + Name + Toggle
        head = QHBoxLayout()
        icon_lbl = _lbl(self._agent.get("icon", "◆"), size=16, color=CYAN)
        name_lbl = _lbl(self._agent["name"], size=12, color=CYAN, bold=True)
        head.addWidget(icon_lbl)
        head.addSpacing(8)
        head.addWidget(name_lbl)
        head.addStretch()

        self._toggle = QCheckBox("Aktiv")
        self._toggle.setChecked(self._agent.get("enabled", False))
        self._toggle.setStyleSheet(f"""
            QCheckBox {{ color:{TEXT}; font-family:'Courier New'; font-size:10px; background:transparent; }}
            QCheckBox::indicator {{ width:18px; height:18px; border:1px solid {BORDER};
                border-radius:4px; background:{BG}; }}
            QCheckBox::indicator:checked {{ background:{CYAN}; border-color:{CYAN}; }}
        """)
        self._toggle.toggled.connect(self._on_toggle)
        head.addWidget(self._toggle)
        lay.addLayout(head)

        # Beschreibung
        desc = _lbl(self._agent["description"], size=9, color=TEXTD)
        desc.setWordWrap(True)
        lay.addWidget(desc)

        # Einstellungen je nach Intervall-Typ
        cfg_row = QHBoxLayout()
        interval = self._agent.get("interval", "minutes")

        if interval == "daily":
            cfg_row.addWidget(_lbl("Uhrzeit:", size=9, color=TEXT))
            self._time_edit = QTimeEdit()
            t = self._agent.get("time", "08:00")
            h, m = map(int, t.split(":"))
            self._time_edit.setTime(QTime(h, m))
            self._time_edit.setDisplayFormat("HH:mm")
            self._time_edit.setFixedWidth(70)
            self._time_edit.setStyleSheet(f"""
                QTimeEdit {{ background:{BG}; border:1px solid {BORDER}; color:{CYAN};
                    font-family:'Courier New'; font-size:11px; border-radius:5px; padding:2px 6px; }}
            """)
            self._time_edit.timeChanged.connect(self._on_time_change)
            cfg_row.addWidget(self._time_edit)

        elif interval == "minutes":
            cfg_row.addWidget(_lbl("Alle", size=9, color=TEXT))
            self._spin = QSpinBox()
            self._spin.setMinimum(1)
            self._spin.setMaximum(1440)
            self._spin.setValue(self._agent.get("minutes", 30))
            self._spin.setFixedWidth(65)
            self._spin.setStyleSheet(f"""
                QSpinBox {{ background:{BG}; border:1px solid {BORDER}; color:{CYAN};
                    font-family:'Courier New'; font-size:11px; border-radius:5px; padding:2px 6px; }}
                QSpinBox::up-button, QSpinBox::down-button {{ width:16px; background:{CARD}; border:none; }}
            """)
            self._spin.valueChanged.connect(self._on_minutes_change)
            cfg_row.addWidget(self._spin)
            cfg_row.addWidget(_lbl("Minuten", size=9, color=TEXT))

        cfg_row.addStretch()

        # Letzter Lauf
        last = self._agent.get("last_run")
        if last:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(last)
                last_str = dt.strftime("%d.%m.%Y %H:%M")
            except Exception:
                last_str = last
        else:
            last_str = "Noch nicht gelaufen"

        self._last_lbl = _lbl(f"Zuletzt: {last_str}", size=9, color=TEXTD)
        cfg_row.addWidget(self._last_lbl)

        # Jetzt ausführen Button
        run_btn = QPushButton("▶ Jetzt")
        run_btn.setFixedHeight(26)
        run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        run_btn.setStyleSheet(f"""
            QPushButton {{ background:transparent; border:1px solid {CYAN_D};
                color:{CYAN_D}; font-family:'Courier New'; font-size:9px; border-radius:5px; padding:0 8px; }}
            QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
        """)
        run_btn.clicked.connect(self._run_now)
        cfg_row.addWidget(run_btn)
        lay.addLayout(cfg_row)

        # Status-Zeile
        self._status_lbl = _lbl("", size=9, color=GREEN)
        lay.addWidget(self._status_lbl)

    def _on_toggle(self, checked: bool):
        agent_scheduler.set_agent_enabled(self._agent["id"], checked)
        color = GREEN if checked else TEXTD
        status = "Aktiv" if checked else "Inaktiv"
        self._status_lbl.setText(status)
        self._status_lbl.setStyleSheet(f"color:{color}; background:transparent;")

    def _on_time_change(self, t: QTime):
        agent_scheduler.set_agent_time(self._agent["id"], t.toString("HH:mm"))

    def _on_minutes_change(self, val: int):
        agent_scheduler.set_agent_minutes(self._agent["id"], val)

    def _run_now(self):
        self._status_lbl.setText("Wird ausgeführt...")
        self._status_lbl.setStyleSheet(f"color:{AMBER}; background:transparent;")
        import threading
        def _run():
            result = agent_scheduler.run_now(self._agent["id"])
            from PyQt6.QtCore import QTimer
            msg = (result[:80] + "...") if result and len(result) > 80 else (result or "Kein Ergebnis")
            QTimer.singleShot(0, lambda: self._on_run_done(msg))
        threading.Thread(target=_run, daemon=True).start()

    def _on_run_done(self, msg: str):
        self._status_lbl.setText(f"Ergebnis: {msg}")
        self._status_lbl.setStyleSheet(f"color:{GREEN}; background:transparent;")


class AgentPanel(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VADOX — Autonome Agenten")
        self.setMinimumSize(620, 560)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background:{BG}; }}")
        self._build()

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
        title = _lbl("AUTONOME AGENTEN", size=13, color=CYAN, bold=True)
        b_lay.addWidget(title)
        b_lay.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"background:transparent; color:{TEXTD}; font-size:14px; border:none;")
        close_btn.clicked.connect(self.reject)
        b_lay.addWidget(close_btn)
        lay.addWidget(bar)

        # Info-Banner
        info = QFrame()
        info.setFixedHeight(44)
        info.setStyleSheet(f"background:#040f1a; border-bottom:1px solid {BORDER};")
        i_lay = QHBoxLayout(info)
        i_lay.setContentsMargins(20, 0, 20, 0)
        i_lay.addWidget(_lbl(
            "Agenten arbeiten automatisch im Hintergrund — auch wenn du nicht aktiv mit Vadox sprichst.",
            size=9, color=TEXTD
        ))
        lay.addWidget(info)

        # Scroll-Bereich mit Agent-Karten
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{BG}; }}
            QScrollBar:vertical {{ width:4px; background:{BG}; }}
            QScrollBar::handle:vertical {{ background:{CYAN_D}; border-radius:2px; }}
        """)
        container = QWidget()
        container.setStyleSheet(f"background:{BG};")
        c_lay = QVBoxLayout(container)
        c_lay.setContentsMargins(16, 12, 16, 12)
        c_lay.setSpacing(4)

        agents = agent_scheduler.get_agents()
        for aid, agent in agents.items():
            card = AgentCard(agent)
            c_lay.addWidget(card)

        c_lay.addStretch()
        scroll.setWidget(container)
        lay.addWidget(scroll, stretch=1)

        # Fußzeile
        foot = QFrame()
        foot.setFixedHeight(46)
        foot.setStyleSheet(f"background:#040c18; border-top:1px solid {BORDER};")
        f_lay = QHBoxLayout(foot)
        f_lay.setContentsMargins(20, 0, 20, 0)
        f_lay.addWidget(_lbl(
            "Agenten-Ergebnisse erscheinen im Chat und im Aktivitätslog.",
            size=9, color=TEXTD
        ))
        f_lay.addStretch()
        close2 = QPushButton("Schließen")
        close2.setFixedHeight(32)
        close2.setCursor(Qt.CursorShape.PointingHandCursor)
        close2.setStyleSheet(f"""
            QPushButton {{ background:{CARD}; border:1px solid {BORDER}; color:{CYAN_D};
                font-family:'Courier New'; font-size:10px; border-radius:6px; padding:0 16px; }}
            QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
        """)
        close2.clicked.connect(self.accept)
        f_lay.addWidget(close2)
        lay.addWidget(foot)
