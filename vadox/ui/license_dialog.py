"""
Vadox Lizenz-Dialog
-------------------
Zeigt bei fehlender/abgelaufener Lizenz:
  - Trial starten (24h kostenlos)
  - Lizenzschlüssel eingeben
  - Kauflinks zu Gumroad
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from vadox.core.license import activate, start_trial, get_trial_info, get_info, start_checkout

BG     = "#050d1a"
CARD   = "#071525"
BORDER = "#0a2540"
CYAN   = "#00c8ff"
GREEN  = "#00ff88"
PINK   = "#ff00aa"
AMBER  = "#ffaa00"
TEXT   = "#5ab4d8"
TEXTD  = "#0a3a5a"


class LicenseDialog(QDialog):
    def __init__(self, parent=None, mode: str = "no_license"):
        """
        mode: 'no_license' → Trial anbieten
              'trial_expired' → Trial abgelaufen, nur Kauf/Key
        """
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle("VADOX — Lizenz")
        self.setFixedSize(520, 470)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(f"background:{BG}; border:1px solid {BORDER};")
        self._accepted = False
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
        b_lay.setContentsMargins(24, 0, 24, 0)

        logo = QLabel("V")
        logo.setFont(QFont("Courier New", 18, QFont.Weight.Bold))
        logo.setStyleSheet(f"color:{CYAN}; background:transparent;")

        title = QLabel("VADOX  LIZENZ")
        title.setFont(QFont("Courier New", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{CYAN}; letter-spacing:3px; background:transparent;")

        b_lay.addWidget(logo)
        b_lay.addSpacing(10)
        b_lay.addWidget(title)
        b_lay.addStretch()
        lay.addWidget(bar)

        # Inhalt
        content = QFrame()
        content.setStyleSheet("background:transparent;")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(30, 22, 30, 22)
        c_lay.setSpacing(12)

        if self.mode == "trial_expired":
            self._build_expired(c_lay)
        else:
            self._build_trial_offer(c_lay)

        lay.addWidget(content, stretch=1)

        # Fußzeile
        foot = QFrame()
        foot.setFixedHeight(30)
        foot.setStyleSheet(f"background:#040c18; border-top:1px solid {BORDER};")
        f_lay = QHBoxLayout(foot)
        f_lay.setContentsMargins(24, 0, 24, 0)
        f_lay.addStretch()
        lbl = QLabel("vadox.ai  |  support@vadox.ai")
        lbl.setStyleSheet(f"color:{TEXTD}; font-size:9px; background:transparent;")
        f_lay.addWidget(lbl)
        f_lay.addStretch()
        lay.addWidget(foot)

    def _build_trial_offer(self, lay):
        """Ersten Start: Trial oder Key eingeben."""
        header = QLabel("Willkommen bei Vadox!")
        header.setFont(QFont("Courier New", 13, QFont.Weight.Bold))
        header.setStyleSheet(f"color:{CYAN}; background:transparent;")
        lay.addWidget(header)

        sub = QLabel("Starte deinen kostenlosen 24h-Trial oder gib deinen Lizenzschlüssel ein.")
        sub.setFont(QFont("Courier New", 9))
        sub.setStyleSheet(f"color:{TEXT}; background:transparent;")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        lay.addSpacing(4)

        # Trial Button
        trial_btn = QPushButton("▶   24h KOSTENLOS TESTEN")
        trial_btn.setFixedHeight(48)
        trial_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        trial_btn.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        trial_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #003a5a, stop:1 #005a3a);
                border:1px solid {GREEN}; color:{GREEN};
                border-radius:8px; letter-spacing:2px;
            }}
            QPushButton:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #004a70, stop:1 #007a50); }}
        """)
        trial_btn.clicked.connect(self._start_trial)
        lay.addWidget(trial_btn)

        # 1-Monat Button
        month_btn = QPushButton("🔁   VADOX 1 MONAT  —  67 €  (Jetzt kaufen)")
        month_btn.setFixedHeight(34)
        month_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        month_btn.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        month_btn.setStyleSheet(f"""
            QPushButton {{
                background:#001a1a; border:1px solid {CYAN};
                color:{CYAN}; border-radius:8px; letter-spacing:1px;
            }}
            QPushButton:hover {{ background:#002a2a; color:#7ae0ff; }}
        """)
        month_btn.clicked.connect(lambda: self._buy("month"))
        lay.addWidget(month_btn)

        # Direkt kaufen Button
        buy_btn = QPushButton("⚡   VADOX PRO  —  197 €  Lifetime  (Jetzt kaufen)")
        buy_btn.setFixedHeight(40)
        buy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        buy_btn.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        buy_btn.setStyleSheet(f"""
            QPushButton {{
                background:#0d1a00; border:1px solid #ffaa00;
                color:#ffaa00; border-radius:8px; letter-spacing:1px;
            }}
            QPushButton:hover {{ background:#1a2a00; color:#ffd060; }}
        """)
        buy_btn.clicked.connect(lambda: self._buy("pro"))
        lay.addWidget(buy_btn)

        # Trennlinie
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color:{BORDER};")
        lay.addWidget(line)

        lbl2 = QLabel("Lizenzschlüssel eingeben:")
        lbl2.setFont(QFont("Courier New", 9))
        lbl2.setStyleSheet(f"color:{TEXT}; background:transparent;")
        lay.addWidget(lbl2)

        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("VADOX-XXXX-XXXX-XXXX-XXXX-...  oder Gumroad-Key")
        self._key_input.setFixedHeight(40)
        self._key_input.setFont(QFont("Courier New", 10))
        self._key_input.setStyleSheet(f"""
            QLineEdit {{
                background:{CARD}; border:1px solid #1a3a5a;
                color:{CYAN}; border-radius:8px; padding:0 14px;
            }}
            QLineEdit:focus {{ border-color:{CYAN}; }}
        """)
        self._key_input.returnPressed.connect(self._activate)
        lay.addWidget(self._key_input)

        self._status = QLabel("")
        self._status.setFont(QFont("Courier New", 9))
        self._status.setStyleSheet(f"color:{AMBER}; background:transparent;")
        self._status.setWordWrap(True)
        lay.addWidget(self._status)

        lay.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        exit_btn = QPushButton("Beenden")
        exit_btn.setFixedHeight(36)
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.setFont(QFont("Courier New", 9))
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:1px solid {BORDER};
                color:{TEXTD}; border-radius:8px;
            }}
            QPushButton:hover {{ border-color:{PINK}; color:{PINK}; }}
        """)
        exit_btn.clicked.connect(self.reject)

        self._activate_btn = QPushButton("Key Aktivieren")
        self._activate_btn.setFixedHeight(36)
        self._activate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._activate_btn.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self._activate_btn.setStyleSheet(f"""
            QPushButton {{
                background:#0a2a4a; border:1px solid {CYAN};
                color:{CYAN}; border-radius:8px; letter-spacing:1px;
            }}
            QPushButton:hover {{ background:#0f3a60; }}
        """)
        self._activate_btn.clicked.connect(self._activate)

        btn_row.addWidget(exit_btn)
        btn_row.addWidget(self._activate_btn, stretch=1)
        lay.addLayout(btn_row)

    def _build_expired(self, lay):
        """Trial abgelaufen — Kaufoptionen zeigen."""
        header = QLabel("⏱  Trial abgelaufen")
        header.setFont(QFont("Courier New", 13, QFont.Weight.Bold))
        header.setStyleSheet(f"color:{AMBER}; background:transparent;")
        lay.addWidget(header)

        sub = QLabel(
            "Dein 24h-Trial ist abgelaufen. Schalte Vadox jetzt frei\n"
            "und nutze alle Funktionen ohne Einschränkung."
        )
        sub.setFont(QFont("Courier New", 9))
        sub.setStyleSheet(f"color:{TEXT}; background:transparent;")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        lay.addSpacing(6)

        # 1-Monat Button
        month_btn2 = QPushButton("🔁   VADOX 1 MONAT  —  67 €  —  Jetzt kaufen")
        month_btn2.setFixedHeight(40)
        month_btn2.setCursor(Qt.CursorShape.PointingHandCursor)
        month_btn2.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        month_btn2.setStyleSheet(f"""
            QPushButton {{
                background:#001a1a; border:1px solid {CYAN};
                color:{CYAN}; border-radius:8px; letter-spacing:1px;
            }}
            QPushButton:hover {{ background:#002a2a; color:#7ae0ff; }}
        """)
        month_btn2.clicked.connect(lambda: self._buy("month"))
        lay.addWidget(month_btn2)

        lay.addSpacing(4)

        # PRO Button
        pro_btn = QPushButton("⚡   VADOX PRO  —  197 €  Lifetime  —  Jetzt kaufen")
        pro_btn.setFixedHeight(52)
        pro_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pro_btn.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
        pro_btn.setStyleSheet(f"""
            QPushButton {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #001a3a, stop:1 #002a5a);
                border:1px solid {CYAN}; color:{CYAN};
                border-radius:8px; letter-spacing:1px;
            }}
            QPushButton:hover {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #002a50, stop:1 #003a70); }}
        """)
        pro_btn.clicked.connect(lambda: self._buy("pro"))
        lay.addWidget(pro_btn)

        lay.addSpacing(4)

        lbl2 = QLabel("Bereits gekauft? Key eingeben:")
        lbl2.setFont(QFont("Courier New", 9))
        lbl2.setStyleSheet(f"color:{TEXT}; background:transparent;")
        lay.addWidget(lbl2)

        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("VADOX-XXXX-... oder Gumroad-Key")
        self._key_input.setFixedHeight(38)
        self._key_input.setFont(QFont("Courier New", 10))
        self._key_input.setStyleSheet(f"""
            QLineEdit {{
                background:{CARD}; border:1px solid #1a3a5a;
                color:{CYAN}; border-radius:8px; padding:0 14px;
            }}
            QLineEdit:focus {{ border-color:{CYAN}; }}
        """)
        self._key_input.returnPressed.connect(self._activate)
        lay.addWidget(self._key_input)

        self._status = QLabel("")
        self._status.setFont(QFont("Courier New", 9))
        self._status.setStyleSheet(f"color:{AMBER}; background:transparent;")
        lay.addWidget(self._status)

        lay.addStretch()

        btn_row = QHBoxLayout()

        exit_btn = QPushButton("Beenden")
        exit_btn.setFixedHeight(36)
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.setFont(QFont("Courier New", 9))
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:1px solid {BORDER};
                color:{TEXTD}; border-radius:8px;
            }}
            QPushButton:hover {{ border-color:{PINK}; color:{PINK}; }}
        """)
        exit_btn.clicked.connect(self.reject)

        self._activate_btn = QPushButton("Aktivieren")
        self._activate_btn.setFixedHeight(36)
        self._activate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._activate_btn.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self._activate_btn.setStyleSheet(f"""
            QPushButton {{
                background:#0a2a4a; border:1px solid {CYAN};
                color:{CYAN}; border-radius:8px;
            }}
            QPushButton:hover {{ background:#0f3a60; }}
        """)
        self._activate_btn.clicked.connect(self._activate)

        btn_row.addWidget(exit_btn)
        btn_row.addWidget(self._activate_btn, stretch=1)
        lay.addLayout(btn_row)

    def _start_trial(self):
        start_trial()
        self._accepted = True
        self.accept()

    def _open_url(self, url: str):
        import webbrowser
        webbrowser.open(url)

    def _buy(self, plan: str):
        self._status.setText("Zahlungsseite wird geladen...")
        self._status.setStyleSheet(f"color:{AMBER}; background:transparent;")
        url = start_checkout(plan)
        if url:
            self._status.setText("")
            self._open_url(url)
        else:
            self._status.setText("Konnte keine Zahlungsseite laden — prüfe deine Internetverbindung.")
            self._status.setStyleSheet(f"color:{PINK}; background:transparent;")

    def _activate(self):
        key = self._key_input.text().strip()
        if not key:
            self._status.setText("Bitte einen Lizenzschlüssel eingeben.")
            self._status.setStyleSheet(f"color:{AMBER}; background:transparent;")
            return

        self._activate_btn.setEnabled(False)
        self._status.setText("Wird geprüft...")
        self._status.setStyleSheet(f"color:{AMBER}; background:transparent;")

        ok, msg = activate(key)
        if ok:
            self._status.setText(f"✓  {msg}")
            self._status.setStyleSheet(f"color:{GREEN}; background:transparent;")
            self._accepted = True
            QTimer.singleShot(1200, self.accept)
        else:
            self._status.setText(f"✗  {msg}")
            self._status.setStyleSheet(f"color:{PINK}; background:transparent;")
            self._activate_btn.setEnabled(True)

    def was_accepted(self) -> bool:
        return self._accepted
