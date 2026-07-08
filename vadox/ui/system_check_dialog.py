# -*- coding: utf-8 -*-
"""
System-Check-Dialog
-------------------
Zeigt beim Start freundlich an, was noch fehlt, und bietet Ein-Klick-Fixes bzw.
Download-Links. Die App laeuft danach normal weiter.
"""
import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

BG     = "#050d1a"
CARD   = "#071525"
BORDER = "#0a2540"
CYAN   = "#00c8ff"
GREEN  = "#00ff88"
AMBER  = "#ffaa00"
TEXT   = "#5ab4d8"
TEXTD  = "#2a7aaa"


class _FixWorker(QThread):
    done = pyqtSignal(bool)

    def __init__(self, fix_fn):
        super().__init__()
        self._fix = fix_fn

    def run(self):
        try:
            ok = bool(self._fix())
        except Exception:
            ok = False
        self.done.emit(ok)


class SystemCheckDialog(QDialog):
    def __init__(self, issues: list, parent=None):
        super().__init__(parent)
        self._issues = issues
        self._workers = []
        self.setWindowTitle("VADOX — Systemprüfung")
        self.setFixedWidth(520)
        self.setStyleSheet(f"background:{BG};")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        bar = QFrame(); bar.setFixedHeight(50)
        bar.setStyleSheet(f"background:#040c18; border-bottom:1px solid {BORDER};")
        bl = QHBoxLayout(bar); bl.setContentsMargins(22, 0, 22, 0)
        t = QLabel("⚙  SYSTEMPRÜFUNG")
        t.setFont(QFont("Courier New", 12, QFont.Weight.Bold))
        t.setStyleSheet(f"color:{CYAN}; letter-spacing:2px; background:transparent;")
        bl.addWidget(t)
        lay.addWidget(bar)

        body = QVBoxLayout()
        body.setContentsMargins(26, 20, 26, 20)
        body.setSpacing(12)

        intro = QLabel("Ein paar Dinge fehlen noch für den vollen Funktionsumfang. "
                       "Vadox läuft trotzdem — du kannst das jetzt oder später erledigen.")
        intro.setWordWrap(True)
        intro.setFont(QFont("Courier New", 10))
        intro.setStyleSheet(f"color:{TEXT}; background:transparent;")
        body.addWidget(intro)

        for issue in self._issues:
            body.addWidget(self._row(issue))

        body.addSpacing(6)
        close_btn = QPushButton("Weiter zu Vadox  ▸")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        close_btn.setFixedHeight(40)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background:#0a2a4a; border:1px solid {CYAN};
                color:{CYAN}; border-radius:8px; letter-spacing:1px; }}
            QPushButton:hover {{ background:#0f3a60; }}
        """)
        close_btn.clicked.connect(self.accept)
        body.addWidget(close_btn)
        lay.addLayout(body)

    def _row(self, issue: dict) -> QWidget:
        box = QFrame()
        box.setStyleSheet(f"background:{CARD}; border:1px solid {BORDER}; border-radius:8px;")
        v = QVBoxLayout(box); v.setContentsMargins(14, 10, 14, 10); v.setSpacing(6)

        name = QLabel(f"●  {issue['name']}")
        name.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        name.setStyleSheet(f"color:{AMBER}; background:transparent;")
        v.addWidget(name)

        hint = QLabel(issue["hint"])
        hint.setWordWrap(True)
        hint.setFont(QFont("Courier New", 9))
        hint.setStyleSheet(f"color:{TEXT}; background:transparent;")
        v.addWidget(hint)

        row = QHBoxLayout(); row.addStretch()
        status = QLabel("")
        status.setFont(QFont("Courier New", 9))
        status.setStyleSheet(f"color:{TEXTD}; background:transparent;")
        row.addWidget(status)

        if issue.get("fix"):
            btn = QPushButton("Automatisch installieren")
            btn.setStyleSheet(self._btn_style(GREEN))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda: self._auto_fix(issue, btn, status, name))
            row.addWidget(btn)
        elif issue.get("url"):
            btn = QPushButton("Download-Seite öffnen")
            btn.setStyleSheet(self._btn_style(CYAN))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda: webbrowser.open(issue["url"]))
            row.addWidget(btn)

        v.addLayout(row)
        return box

    def _btn_style(self, color):
        return (f"QPushButton {{ background:transparent; border:1px solid {color};"
                f" color:{color}; border-radius:6px; padding:6px 12px;"
                f" font-family:'Courier New'; font-size:9px; }}"
                f" QPushButton:hover {{ background:{color}22; }}")

    def _auto_fix(self, issue, btn, status, name):
        btn.setEnabled(False)
        status.setText("Wird geladen …")
        status.setStyleSheet(f"color:{AMBER}; background:transparent;")
        worker = _FixWorker(issue["fix"])

        def on_done(ok):
            if ok:
                status.setText("✓ Erledigt")
                status.setStyleSheet(f"color:{GREEN}; background:transparent;")
                name.setStyleSheet(f"color:{GREEN}; background:transparent;")
                btn.setText("✓ Installiert")
            else:
                status.setText("✗ Fehlgeschlagen — bitte später erneut")
                status.setStyleSheet(f"color:#ff6b8a; background:transparent;")
                btn.setEnabled(True)

        worker.done.connect(on_done)
        worker.start()
        self._workers.append(worker)


def run_system_check(parent=None):
    """Prueft das System und zeigt bei Bedarf den Dialog. Blockiert nie dauerhaft."""
    try:
        from vadox.core.system_check import check
        issues = check()
        if issues:
            SystemCheckDialog(issues, parent).exec()
    except Exception as e:
        print(f"[SystemCheck] übersprungen: {e}")
