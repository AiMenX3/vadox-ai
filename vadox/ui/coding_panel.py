# -*- coding: utf-8 -*-
"""
Vadox Coding Assistant Panel
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget, QTextEdit, QComboBox, QTabWidget,
    QLineEdit, QFileDialog, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
import threading

BG     = "#050d1a"
CARD   = "#071525"
BORDER = "#0a2540"
CYAN   = "#00c8ff"
CYAN_D = "#2a7aaa"
GREEN  = "#00ff88"
AMBER  = "#ffaa00"
RED    = "#ff3333"
TEXT   = "#5ab4d8"
TEXTD  = "#3a8aaa"
PINK   = "#ff6ec7"
PURPLE = "#a855f7"
ORANGE = "#ff8800"

LANGUAGES = [
    "Automatisch erkennen", "Python", "JavaScript", "TypeScript",
    "Java", "C#", "C++", "C", "Go", "Rust", "PHP", "Ruby",
    "Swift", "Kotlin", "HTML/CSS", "SQL", "Bash/Shell", "PowerShell"
]


def _lbl(text, size=10, color=TEXT, bold=False):
    l = QLabel(text)
    l.setFont(QFont("Courier New", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    l.setStyleSheet(f"color:{color}; background:transparent;")
    l.setWordWrap(True)
    return l


def _btn(label, color=CYAN, bg="transparent", w=None, h=34):
    b = QPushButton(label)
    b.setFixedHeight(h)
    if w:
        b.setFixedWidth(w)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
    b.setStyleSheet(f"""
        QPushButton {{ background:{bg}; border:1px solid {color};
            color:{color}; border-radius:7px; padding:0 14px; }}
        QPushButton:hover {{ background:{color}22; }}
    """)
    return b


class CodeWorker(QThread):
    chunk = pyqtSignal(str)
    done  = pyqtSignal()

    def __init__(self, prompt):
        super().__init__()
        self._prompt = prompt

    def run(self):
        try:
            from vadox.core.ai_engine import AIEngine
            from vadox.core import settings
            cfg = settings.load()
            engine = AIEngine(
                provider=cfg.get("provider", "claude"),
                api_key=cfg.get("api_key", ""),
                model=cfg.get("model", "claude-sonnet-5"),
            )
            engine.chat(
                self._prompt,
                on_chunk=lambda c: self.chunk.emit(c),
                on_done=lambda _: self.done.emit()
            )
        except Exception as e:
            self.chunk.emit(f"\n[Fehler] {e}")
            self.done.emit()


class CodingPanel(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VADOX — Coding Assistant")
        self.setMinimumSize(1000, 700)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background:{BG}; }}")
        self._loaded_file = None
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
        b_lay.addWidget(_lbl("CODING ASSISTANT", size=13, color=CYAN, bold=True))
        b_lay.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"background:transparent; color:{TEXTD}; font-size:14px; border:none;")
        close_btn.clicked.connect(self.accept)
        b_lay.addWidget(close_btn)
        lay.addWidget(bar)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border:none; background:{BG}; }}
            QTabBar::tab {{ background:{BG}; color:{TEXTD}; font-family:'Courier New';
                font-size:10px; padding:8px 20px; border:1px solid {BORDER};
                border-bottom:none; border-top-left-radius:6px; border-top-right-radius:6px; }}
            QTabBar::tab:selected {{ background:{CARD}; color:{CYAN}; }}
        """)
        tabs.addTab(self._tab_explain(),   "🔍  ERKLÄREN")
        tabs.addTab(self._tab_debug(),     "🐛  DEBUGGEN")
        self._gen_tab_index = tabs.addTab(self._tab_generate(),  "⚡  GENERIEREN")
        tabs.addTab(self._tab_review(),    "✅  REVIEW")
        tabs.addTab(self._tab_convert(),   "🔄  UMWANDELN")
        self._tabs = tabs
        lay.addWidget(tabs, stretch=1)

    def _code_editor(self, placeholder="Code hier einfügen...") -> QTextEdit:
        e = QTextEdit()
        e.setPlaceholderText(placeholder)
        e.setFont(QFont("Courier New", 11))
        e.setStyleSheet(f"""
            QTextEdit {{
                background:{CARD}; border:1px solid {BORDER}; color:{GREEN};
                font-family:'Courier New'; font-size:11px;
                border-radius:8px; padding:12px;
            }}
        """)
        return e

    def _result_box(self) -> QTextEdit:
        e = QTextEdit()
        e.setReadOnly(True)
        e.setFont(QFont("Courier New", 11))
        e.setStyleSheet(f"""
            QTextEdit {{
                background:#040d18; border:1px solid {CYAN_D}; color:{TEXT};
                font-family:'Courier New'; font-size:11px;
                border-radius:8px; padding:12px;
            }}
        """)
        return e

    def _lang_combo(self) -> QComboBox:
        c = QComboBox()
        for lang in LANGUAGES:
            c.addItem(lang)
        c.setFixedHeight(32)
        c.setStyleSheet(f"""
            QComboBox {{ background:{CARD}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:10px; padding:0 10px; border-radius:6px; }}
            QComboBox QAbstractItemView {{ background:{CARD}; color:{CYAN}; border:1px solid {BORDER};
                selection-background-color:{CYAN_D}; }}
        """)
        return c

    def _file_btn(self, editor: QTextEdit) -> QPushButton:
        b = _btn("📂 Datei laden", color=TEXTD, h=32)
        b.clicked.connect(lambda: self._load_file(editor))
        return b

    def _load_file(self, editor: QTextEdit):
        path, _ = QFileDialog.getOpenFileName(
            self, "Code-Datei öffnen", "",
            "Code-Dateien (*.py *.js *.ts *.java *.cs *.cpp *.c *.go *.rs *.php *.rb *.swift *.kt *.html *.css *.sql *.sh *.ps1 *.txt);;Alle Dateien (*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                editor.setPlainText(content)
                self._loaded_file = path
            except Exception as e:
                editor.setPlainText(f"Fehler beim Laden: {e}")

    def _run_worker(self, prompt: str, result_box: QTextEdit, btn: QPushButton):
        result_box.setPlainText("")
        btn.setEnabled(False)
        btn.setText("⏳ Läuft...")
        worker = CodeWorker(prompt)
        worker.chunk.connect(lambda c: result_box.insertPlainText(c))
        def on_done():
            btn.setEnabled(True)
            btn.setText(btn._original_text)
            # Scroll to bottom
            sb = result_box.verticalScrollBar()
            sb.setValue(sb.maximum())
        worker.done.connect(on_done)
        worker.start()
        self._worker = worker

    # ── Tab: Erklären ─────────────────────────────────────────────────────────
    def _tab_explain(self) -> QWidget:
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        top = QHBoxLayout()
        top.addWidget(_lbl("Sprache:", size=9, color=TEXTD))
        lang = self._lang_combo()
        top.addWidget(lang)
        top.addSpacing(10)
        detail = QComboBox()
        for d in ["Einfach (Anfänger)", "Normal", "Detailliert (Experte)"]:
            detail.addItem(d)
        detail.setFixedHeight(32)
        detail.setStyleSheet(lang.styleSheet())
        top.addWidget(detail)
        top.addStretch()
        editor = self._code_editor()
        top.addWidget(self._file_btn(editor))
        lay.addLayout(top)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background: " + BORDER + "; height: 2px; }")
        splitter.addWidget(editor)
        result = self._result_box()
        result.setPlaceholderText("Erklärung erscheint hier...")
        splitter.addWidget(result)
        splitter.setSizes([300, 300])
        lay.addWidget(splitter, stretch=1)

        btn = _btn("🔍  Code erklären", color=CYAN, h=38)
        btn._original_text = "🔍  Code erklären"
        def run():
            code = editor.toPlainText().strip()
            if not code:
                return
            lang_str = lang.currentText()
            detail_str = detail.currentText().split("(")[0].strip()
            prompt = (
                f"Erklaere den folgenden {lang_str}-Code auf Deutsch. "
                f"Erklaerungstiefe: {detail_str}.\n"
                f"Gehe auf folgendes ein:\n"
                f"- Was macht der Code insgesamt?\n"
                f"- Wie funktionieren die wichtigsten Teile?\n"
                f"- Was sind moegliche Probleme oder Verbesserungen?\n\n"
                f"Code:\n```\n{code}\n```"
            )
            self._run_worker(prompt, result, btn)
        btn.clicked.connect(run)
        lay.addWidget(btn)
        return w

    # ── Tab: Debuggen ─────────────────────────────────────────────────────────
    def _tab_debug(self) -> QWidget:
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        top = QHBoxLayout()
        top.addWidget(_lbl("Sprache:", size=9, color=TEXTD))
        lang = self._lang_combo()
        top.addWidget(lang)
        top.addStretch()
        editor_code = self._code_editor()
        top.addWidget(self._file_btn(editor_code))
        lay.addLayout(top)

        lay.addWidget(_lbl("Code mit Fehler:", size=9, color=TEXTD))
        editor_code.setMaximumHeight(200)
        lay.addWidget(editor_code)

        lay.addWidget(_lbl("Fehlermeldung (optional):", size=9, color=TEXTD))
        error_input = QTextEdit()
        error_input.setPlaceholderText("Fehlermeldung / Traceback hier einfügen...")
        error_input.setMaximumHeight(80)
        error_input.setStyleSheet(f"""
            QTextEdit {{ background:{CARD}; border:1px solid {RED}44; color:{RED};
                font-family:'Courier New'; font-size:10px; border-radius:6px; padding:8px; }}
        """)
        lay.addWidget(error_input)

        result = self._result_box()
        result.setPlaceholderText("Debug-Analyse erscheint hier...")
        lay.addWidget(result, stretch=1)

        btn = _btn("🐛  Fehler finden & beheben", color=RED, h=38)
        btn._original_text = "🐛  Fehler finden & beheben"
        def run():
            code = editor_code.toPlainText().strip()
            if not code:
                return
            error_msg = error_input.toPlainText().strip()
            lang_str = lang.currentText()
            prompt = (
                f"Du bist ein erfahrener {lang_str}-Entwickler. Analysiere diesen Code auf Fehler.\n\n"
                f"Code:\n```\n{code}\n```\n"
            )
            if error_msg:
                prompt += f"\nFehlermeldung:\n```\n{error_msg}\n```\n"
            prompt += (
                f"\nAufgaben:\n"
                f"1. Identifiziere alle Fehler (Bug, Logikfehler, Syntaxfehler)\n"
                f"2. Erklaere warum der Fehler auftritt\n"
                f"3. Zeige den korrigierten Code\n"
                f"4. Erklaere die Korrektur\n"
            )
            self._run_worker(prompt, result, btn)
        btn.clicked.connect(run)
        lay.addWidget(btn)
        return w

    # ── Tab: Generieren ───────────────────────────────────────────────────────
    def _tab_generate(self) -> QWidget:
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        top = QHBoxLayout()
        top.addWidget(_lbl("Sprache:", size=9, color=TEXTD))
        lang = self._lang_combo()
        lang.setCurrentText("Python")
        top.addWidget(lang)
        top.addStretch()
        lay.addLayout(top)

        # Schnell-Vorlagen
        lay.addWidget(_lbl("Schnell-Vorlagen:", size=9, color=TEXTD))
        template_row = QHBoxLayout()
        templates = [
            ("API-Endpoint", "Erstelle einen REST API Endpoint"),
            ("Datenbank-Query", "Erstelle eine Datenbankabfrage"),
            ("Unit-Test", "Schreibe Unit-Tests fuer"),
            ("Klasse/Objekt", "Erstelle eine Klasse fuer"),
            ("Datei lesen/schreiben", "Code zum Lesen und Schreiben von Dateien"),
        ]
        desc_input_ref = [None]
        for label, tmpl in templates:
            b = _btn(label, color=PURPLE, h=30)
            b.setFont(QFont("Courier New", 9))
            b.clicked.connect(lambda _, t=tmpl: desc_input_ref[0] and desc_input_ref[0].setPlainText(t + ": "))
            template_row.addWidget(b)
        lay.addLayout(template_row)

        lay.addWidget(_lbl("Beschreibung was generiert werden soll:", size=9, color=TEXTD))
        desc_input = QTextEdit()
        desc_input.setPlaceholderText("Beschreibe was der Code tun soll...\nz.B. 'Eine Funktion die eine CSV-Datei liest und die Daten als Dictionary zurückgibt'")
        desc_input.setMaximumHeight(100)
        desc_input.setStyleSheet(f"""
            QTextEdit {{ background:{CARD}; border:1px solid {BORDER}; color:{TEXT};
                font-family:'Courier New'; font-size:11px; border-radius:6px; padding:8px; }}
        """)
        desc_input_ref[0] = desc_input
        lay.addWidget(desc_input)

        result = self._result_box()
        result.setPlaceholderText("Generierter Code erscheint hier...")
        lay.addWidget(result, stretch=1)

        btn_row = QHBoxLayout()
        btn = _btn("⚡  Code generieren", color=GREEN, h=38)
        btn._original_text = "⚡  Code generieren"
        copy_btn = _btn("📋  Kopieren", color=TEXTD, h=38)
        copy_btn.clicked.connect(lambda: self._copy(result.toPlainText()))
        btn_row.addWidget(btn)
        btn_row.addWidget(copy_btn)
        lay.addLayout(btn_row)

        def run():
            desc = desc_input.toPlainText().strip()
            if not desc:
                return
            lang_str = lang.currentText()
            prompt = (
                f"Generiere {lang_str}-Code fuer folgende Aufgabe:\n{desc}\n\n"
                f"Anforderungen:\n"
                f"- Sauberer, gut strukturierter Code\n"
                f"- Kurze Kommentare fuer wichtige Teile\n"
                f"- Fehlerbehandlung wo sinnvoll\n"
                f"- Beispiel-Verwendung am Ende\n"
            )
            self._run_worker(prompt, result, btn)
        btn.clicked.connect(run)

        # Referenzen fuer programmatischen Auto-Start (per Sprachbefehl)
        self._gen_desc = desc_input
        self._gen_lang = lang
        self._gen_run  = run
        return w

    def start_generation(self, task: str, language: str = ""):
        """Oeffnet den Generieren-Tab, fuellt die Aufgabe ein und startet die
        Code-Generierung sofort — fuer den Auto-Start per Sprach-/Textbefehl."""
        try:
            self._tabs.setCurrentIndex(self._gen_tab_index)
            if language:
                idx = self._gen_lang.findText(language, Qt.MatchFlag.MatchContains)
                if idx >= 0:
                    self._gen_lang.setCurrentIndex(idx)
            self._gen_desc.setPlainText(task)
            QTimer.singleShot(400, self._gen_run)
        except Exception as e:
            print(f"[CodingPanel] Auto-Start Fehler: {e}")

    # ── Tab: Review ───────────────────────────────────────────────────────────
    def _tab_review(self) -> QWidget:
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        top = QHBoxLayout()
        top.addWidget(_lbl("Sprache:", size=9, color=TEXTD))
        lang = self._lang_combo()
        top.addWidget(lang)
        top.addStretch()
        editor = self._code_editor()
        top.addWidget(self._file_btn(editor))
        lay.addLayout(top)

        lay.addWidget(_lbl("Code zum Reviewen:", size=9, color=TEXTD))
        editor.setMaximumHeight(280)
        lay.addWidget(editor)

        result = self._result_box()
        result.setPlaceholderText("Code Review erscheint hier...")
        lay.addWidget(result, stretch=1)

        btn = _btn("✅  Code Review starten", color=AMBER, h=38)
        btn._original_text = "✅  Code Review starten"
        def run():
            code = editor.toPlainText().strip()
            if not code:
                return
            lang_str = lang.currentText()
            prompt = (
                f"Fuehre ein professionelles Code Review fuer diesen {lang_str}-Code durch.\n\n"
                f"Code:\n```\n{code}\n```\n\n"
                f"Bewerte und kommentiere:\n"
                f"1. Code-Qualitaet und Lesbarkeit (Note 1-10)\n"
                f"2. Performance und Effizienz\n"
                f"3. Sicherheitsrisiken\n"
                f"4. Best Practices (werden sie eingehalten?)\n"
                f"5. Verbesserungsvorschlaege mit konkretem Code\n"
                f"6. Gesamtbewertung\n"
            )
            self._run_worker(prompt, result, btn)
        btn.clicked.connect(run)
        lay.addWidget(btn)
        return w

    # ── Tab: Umwandeln ────────────────────────────────────────────────────────
    def _tab_convert(self) -> QWidget:
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        top = QHBoxLayout()
        top.addWidget(_lbl("Von:", size=9, color=TEXTD))
        src_lang = self._lang_combo()
        src_lang.setCurrentText("Python")
        top.addWidget(src_lang)
        top.addWidget(_lbl("→", size=12, color=CYAN))
        top.addWidget(_lbl("Nach:", size=9, color=TEXTD))
        tgt_lang = self._lang_combo()
        tgt_lang.setCurrentText("JavaScript")
        top.addWidget(tgt_lang)
        top.addStretch()
        editor = self._code_editor()
        top.addWidget(self._file_btn(editor))
        lay.addLayout(top)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background: " + BORDER + "; height: 2px; }")
        splitter.addWidget(editor)
        result = self._result_box()
        result.setPlaceholderText("Umgewandelter Code erscheint hier...")
        splitter.addWidget(result)
        splitter.setSizes([280, 280])
        lay.addWidget(splitter, stretch=1)

        btn_row = QHBoxLayout()
        btn = _btn("🔄  Code umwandeln", color=ORANGE, h=38)
        btn._original_text = "🔄  Code umwandeln"
        copy_btn = _btn("📋  Kopieren", color=TEXTD, h=38)
        copy_btn.clicked.connect(lambda: self._copy(result.toPlainText()))
        btn_row.addWidget(btn)
        btn_row.addWidget(copy_btn)
        lay.addLayout(btn_row)

        def run():
            code = editor.toPlainText().strip()
            if not code:
                return
            from_l = src_lang.currentText()
            to_l   = tgt_lang.currentText()
            prompt = (
                f"Wandle diesen {from_l}-Code in aequivalenten {to_l}-Code um.\n\n"
                f"Original ({from_l}):\n```\n{code}\n```\n\n"
                f"Anforderungen:\n"
                f"- Gleiche Funktionalitaet behalten\n"
                f"- {to_l}-spezifische Best Practices verwenden\n"
                f"- Kurze Erklaerung der wichtigsten Unterschiede\n"
            )
            self._run_worker(prompt, result, btn)
        btn.clicked.connect(run)
        return w

    def _copy(self, text: str):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
