from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

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


def _lbl(text, size=10, color=TEXT, bold=False):
    l = QLabel(text)
    l.setFont(QFont("Courier New", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    l.setStyleSheet(f"color:{color}; background:transparent;")
    return l


def _fix_btn(label="Beheben"):
    btn = QPushButton(label)
    btn.setFixedHeight(24)
    btn.setFixedWidth(80)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
    btn.setStyleSheet(f"""
        QPushButton {{ background:#1a0a0a; border:1px solid {RED};
            color:{RED}; border-radius:5px; }}
        QPushButton:hover {{ background:#2a1010; color:#ff6666; border-color:#ff6666; }}
        QPushButton:disabled {{ background:{CARD}; border-color:{BORDER}; color:{TEXTD}; }}
    """)
    return btn


class ScanWorker(QThread):
    done = pyqtSignal(dict)

    def run(self):
        from vadox.tools.security_scanner import run_full_scan
        self.done.emit(run_full_scan())


class FixWorker(QThread):
    done = pyqtSignal(bool, str)

    def __init__(self, fn, *args):
        super().__init__()
        self._fn = fn
        self._args = args

    def run(self):
        ok, msg = self._fn(*self._args)
        self.done.emit(ok, msg)


class SecurityPanel(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VADOX — IT Security")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background:{BG}; }}")
        self._worker = None
        self._fix_workers = []
        self._last_result = None
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
        b_lay.addWidget(_lbl("IT SECURITY SCANNER", size=13, color=CYAN, bold=True))
        b_lay.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"background:transparent; color:{TEXTD}; font-size:14px; border:none;")
        close_btn.clicked.connect(self.reject)
        b_lay.addWidget(close_btn)
        lay.addWidget(bar)

        # Status-Banner
        sb = QFrame()
        sb.setFixedHeight(52)
        sb.setStyleSheet(f"background:#040f1a; border-bottom:1px solid {BORDER};")
        sb_lay = QHBoxLayout(sb)
        sb_lay.setContentsMargins(20, 0, 20, 0)
        self._risk_lbl = _lbl("● BEREIT", size=11, color=CYAN, bold=True)
        self._scan_info = _lbl("Klicke auf 'Scan starten' um den PC zu prüfen.", size=9, color=TEXTD)
        sb_lay.addWidget(self._risk_lbl)
        sb_lay.addSpacing(16)
        sb_lay.addWidget(self._scan_info)
        sb_lay.addStretch()

        self._fix_all_btn = QPushButton("✔  Alles beheben")
        self._fix_all_btn.setFixedHeight(34)
        self._fix_all_btn.setVisible(False)
        self._fix_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fix_all_btn.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self._fix_all_btn.setStyleSheet(f"""
            QPushButton {{ background:#200a0a; border:1px solid {RED};
                color:{RED}; border-radius:7px; padding:0 14px; }}
            QPushButton:hover {{ background:#300f0f; color:#ff6666; }}
        """)
        self._fix_all_btn.clicked.connect(self._fix_all)
        sb_lay.addWidget(self._fix_all_btn)
        sb_lay.addSpacing(8)

        self._scan_btn = QPushButton("⟳  Scan starten")
        self._scan_btn.setFixedHeight(34)
        self._scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scan_btn.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self._scan_btn.setStyleSheet(f"""
            QPushButton {{ background:#0a2a4a; border:1px solid {CYAN};
                color:{CYAN}; border-radius:7px; padding:0 16px; }}
            QPushButton:hover {{ background:#0f3a60; }}
            QPushButton:disabled {{ background:{CARD}; border-color:{BORDER}; color:{TEXTD}; }}
        """)
        self._scan_btn.clicked.connect(self._start_scan)
        sb_lay.addWidget(self._scan_btn)
        lay.addWidget(sb)

        # Fortschrittsbalken
        self._progress = QProgressBar()
        self._progress.setFixedHeight(3)
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background:{BG}; border:none; }}
            QProgressBar::chunk {{ background:{CYAN}; }}
        """)
        lay.addWidget(self._progress)

        # Scroll-Bereich
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{BG}; }}
            QScrollBar:vertical {{ width:4px; background:{BG}; }}
            QScrollBar::handle:vertical {{ background:{CYAN_D}; border-radius:2px; }}
        """)
        self._results_container = QWidget()
        self._results_container.setStyleSheet(f"background:{BG};")
        self._results_layout = QVBoxLayout(self._results_container)
        self._results_layout.setContentsMargins(16, 12, 16, 12)
        self._results_layout.setSpacing(6)

        placeholder = _lbl(
            "Noch kein Scan durchgeführt.\nKlicke auf 'Scan starten' um deinen PC zu analysieren.",
            size=10, color=TEXTD
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setWordWrap(True)
        self._results_layout.addStretch()
        self._results_layout.addWidget(placeholder, alignment=Qt.AlignmentFlag.AlignCenter)
        self._results_layout.addStretch()

        scroll.setWidget(self._results_container)
        lay.addWidget(scroll, stretch=1)

        # Fußzeile
        foot = QFrame()
        foot.setFixedHeight(40)
        foot.setStyleSheet(f"background:#040c18; border-top:1px solid {BORDER};")
        f_lay = QHBoxLayout(foot)
        f_lay.setContentsMargins(20, 0, 20, 0)
        self._footer_lbl = _lbl("Vadox IT Security — Schutz für deinen PC", size=9, color=TEXTD)
        f_lay.addWidget(self._footer_lbl)
        f_lay.addStretch()
        lay.addWidget(foot)

        # Fix-Aktionen speichern für "Alles beheben"
        self._pending_fixes = []

    # ── Scan ─────────────────────────────────────────────────────────────────

    def _start_scan(self):
        self._scan_btn.setEnabled(False)
        self._scan_btn.setText("Scan läuft...")
        self._fix_all_btn.setVisible(False)
        self._progress.setVisible(True)
        self._risk_lbl.setText("● SCAN LÄUFT")
        self._risk_lbl.setStyleSheet(f"color:{AMBER}; background:transparent; font-weight:bold;")
        self._scan_info.setText("PC wird analysiert — bitte warten...")
        self._pending_fixes = []

        for i in reversed(range(self._results_layout.count())):
            item = self._results_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self._worker = ScanWorker()
        self._worker.done.connect(self._on_scan_done)
        self._worker.start()

    def _on_scan_done(self, result: dict):
        self._last_result = result
        self._progress.setVisible(False)
        self._scan_btn.setEnabled(True)
        self._scan_btn.setText("⟳  Erneut scannen")

        level = result["risk_level"]
        issues = result["issues"]
        duration = result.get("duration_s", 0)

        colors = {"SICHER": GREEN, "MITTEL": AMBER, "HOCH": RED}
        color = colors.get(level, CYAN)
        self._risk_lbl.setText(f"● {level}")
        self._risk_lbl.setStyleSheet(f"color:{color}; font-weight:bold; background:transparent;")
        self._scan_info.setText(
            f"{len(issues)} Problem(e)  ·  Scan: {duration}s  ·  "
            f"{result.get('timestamp','')[:16].replace('T',' ')}"
        )

        if self._pending_fixes or issues:
            self._fix_all_btn.setVisible(True)

        lay = self._results_layout

        # Defender
        ok_d = result["defender"].get("realtime", False)
        self._add_status_card(
            lay, "Windows Defender", ok_d,
            f"Echtzeit-Schutz  ·  Letzte Signatur: {result['defender'].get('last_update','?')}",
            fix_fn=None if ok_d else ("Echtzeit-Schutz aktivieren",
                                      self._fix_defender)
        )

        # Firewall
        ok_f = result["firewall"].get("enabled", False)
        self._add_status_card(
            lay, "Windows Firewall", ok_f,
            result["firewall"].get("detail", ""),
            fix_fn=None if ok_f else ("Firewall aktivieren", self._fix_firewall)
        )

        # Überschrift Probleme
        if issues:
            lay.addWidget(_lbl(f"GEFUNDENE PROBLEME ({len(issues)})", size=9, color=TEXTD))

        # Prozesse
        for p in result.get("processes", []):
            self._add_fix_card(
                lay,
                f"Prozess: {p['name']}  (PID {p['pid']})",
                p["reason"],
                RED,
                btn_label="Beenden",
                fix_fn=lambda pid=p["pid"], name=p["name"]: self._fix_process(pid, name)
            )

        # Autostart
        for a in result.get("autostart", []):
            self._add_fix_card(
                lay,
                f"Autostart: {a['name']}  [{a['hive']}]",
                a["reason"],
                AMBER,
                btn_label="Entfernen",
                fix_fn=lambda n=a["name"], h=a["hive"]: self._fix_autostart(n, h)
            )

        # Netzwerk
        for n in result.get("network", []):
            self._add_fix_card(
                lay,
                f"Verbindung: {n['remote']}  ({n['process']})",
                n["reason"],
                AMBER,
                btn_label="Trennen",
                fix_fn=lambda pid=n.get("pid"), r=n["remote"]: self._fix_network(pid, r)
            )

        # TEMP-Dateien
        for t in result.get("temp_files", []):
            from pathlib import Path
            self._add_fix_card(
                lay,
                f"TEMP-Datei: {Path(t['path']).name}  ({t['size']})",
                t["reason"],
                AMBER,
                btn_label="Löschen",
                fix_fn=lambda path=t["path"]: self._fix_temp(path)
            )

        if not issues and not result.get("processes") and not result.get("autostart") \
                and not result.get("network") and not result.get("temp_files"):
            ok_lbl = _lbl("Keine Bedrohungen gefunden. Dein PC ist sicher.", size=11, color=GREEN)
            ok_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(ok_lbl)
            self._fix_all_btn.setVisible(False)

        lay.addStretch()
        self._footer_lbl.setText(
            f"Letzter Scan: {result.get('timestamp','')[:16].replace('T',' ')}  ·  "
            f"Risiko: {level}")

    # ── Karten ────────────────────────────────────────────────────────────────

    def _add_status_card(self, lay, title, ok, detail, fix_fn=None):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background:{CARD}; border:1px solid {'#1a4a2a' if ok else '#4a1a1a'};
                     border-radius:8px; }}
        """)
        c_lay = QHBoxLayout(card)
        c_lay.setContentsMargins(14, 10, 14, 10)
        dot = QFrame()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background:{GREEN if ok else RED}; border-radius:5px;")
        c_lay.addWidget(dot)
        c_lay.addSpacing(8)
        c_lay.addWidget(_lbl(title, size=10, color=GREEN if ok else RED, bold=True))
        c_lay.addSpacing(10)
        c_lay.addWidget(_lbl(detail, size=9, color=TEXTD))
        c_lay.addStretch()
        c_lay.addWidget(_lbl("OK" if ok else "PROBLEM", size=9,
                             color=GREEN if ok else RED, bold=True))
        if fix_fn:
            label_text, fn = fix_fn
            btn = _fix_btn(label_text)
            status = QLabel()
            status.setFont(QFont("Courier New", 8))
            status.setStyleSheet(f"color:{GREEN}; background:transparent;")
            btn.clicked.connect(lambda: self._run_fix(fn, btn, status))
            c_lay.addSpacing(8)
            c_lay.addWidget(btn)
            c_lay.addWidget(status)
            self._pending_fixes.append((fn, btn, status))
        lay.addWidget(card)

    def _add_fix_card(self, lay, title, reason, color, btn_label, fix_fn):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background:{CARD}; border-left:3px solid {color};
                border-top:1px solid {BORDER}; border-right:1px solid {BORDER};
                border-bottom:1px solid {BORDER}; border-radius:6px; }}
        """)
        outer = QVBoxLayout(card)
        outer.setContentsMargins(12, 8, 12, 8)
        outer.setSpacing(4)

        top = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color:{color}; background:transparent;")
        top.addWidget(title_lbl)
        top.addStretch()

        status_lbl = QLabel()
        status_lbl.setFont(QFont("Courier New", 8))
        status_lbl.setStyleSheet(f"color:{GREEN}; background:transparent;")
        top.addWidget(status_lbl)

        btn = _fix_btn(btn_label)
        btn.clicked.connect(lambda: self._run_fix(fix_fn, btn, status_lbl))
        top.addSpacing(6)
        top.addWidget(btn)
        outer.addLayout(top)

        reason_lbl = QLabel(reason)
        reason_lbl.setFont(QFont("Courier New", 8))
        reason_lbl.setStyleSheet(f"color:{TEXTD}; background:transparent;")
        reason_lbl.setWordWrap(True)
        outer.addWidget(reason_lbl)

        lay.addWidget(card)
        self._pending_fixes.append((fix_fn, btn, status_lbl))

    # ── Fix-Ausführung ────────────────────────────────────────────────────────

    def _run_fix(self, fn, btn, status_lbl, silent=False):
        btn.setEnabled(False)
        btn.setText("...")
        status_lbl.setText("Wird behoben...")
        status_lbl.setStyleSheet(f"color:{AMBER}; background:transparent;")

        worker = FixWorker(fn)
        worker.done.connect(lambda ok, msg: self._on_fix_done(ok, msg, btn, status_lbl, silent))
        worker.start()
        self._fix_workers.append(worker)

    def _on_fix_done(self, ok: bool, msg: str, btn, status_lbl, silent: bool):
        color = GREEN if ok else RED
        icon = "✔" if ok else "✖"
        short = msg[:50] + ("..." if len(msg) > 50 else "")
        status_lbl.setText(f"{icon} {short}")
        status_lbl.setStyleSheet(f"color:{color}; background:transparent;")
        btn.setText("Erledigt" if ok else "Fehler")
        btn.setStyleSheet(f"""
            QPushButton {{ background:{CARD}; border:1px solid {color};
                color:{color}; border-radius:5px; font-family:'Courier New'; font-size:8px; }}
        """)
        if not silent and not ok:
            QMessageBox.warning(self, "Fehler beim Beheben", msg)

    def _fix_defender(self):
        from vadox.tools.security_fixer import fix_defender
        return fix_defender()

    def _fix_firewall(self):
        from vadox.tools.security_fixer import fix_firewall
        return fix_firewall()

    def _fix_process(self, pid, name):
        from vadox.tools.security_fixer import fix_kill_process
        return fix_kill_process(pid, name)

    def _fix_autostart(self, name, hive):
        from vadox.tools.security_fixer import fix_autostart
        return fix_autostart(name, hive)

    def _fix_network(self, pid, remote):
        from vadox.tools.security_fixer import fix_network_connection
        return fix_network_connection(pid, remote)

    def _fix_temp(self, path):
        from vadox.tools.security_fixer import fix_delete_temp_file
        return fix_delete_temp_file(path)

    def _fix_all(self):
        reply = QMessageBox.question(
            self, "Alles beheben?",
            f"Vadox wird alle {len(self._pending_fixes)} gefundenen Probleme automatisch beheben.\n\n"
            "Fortfahren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        for fn, btn, status in self._pending_fixes:
            if btn.isEnabled():
                self._run_fix(fn, btn, status, silent=True)
