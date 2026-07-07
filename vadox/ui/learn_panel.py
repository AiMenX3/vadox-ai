# -*- coding: utf-8 -*-
"""
Vadox Lern-Modus — PDFs, Dokumente, Webseiten zusammenfassen & befragen
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget, QTextEdit, QTabWidget, QLineEdit,
    QFileDialog, QScrollArea, QProgressBar, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

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
PURPLE = "#a855f7"
ORANGE = "#ff8800"


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
        QPushButton:disabled {{ border-color:{BORDER}; color:{BORDER}; }}
    """)
    return b


def _result_box(placeholder="") -> QTextEdit:
    e = QTextEdit()
    e.setReadOnly(True)
    e.setPlaceholderText(placeholder)
    e.setFont(QFont("Courier New", 11))
    e.setStyleSheet(f"""
        QTextEdit {{
            background:#040d18; border:1px solid {CYAN_D};
            color:{TEXT}; font-family:'Courier New'; font-size:11px;
            border-radius:8px; padding:12px;
        }}
    """)
    return e


def extract_text_from_file(path: str) -> str:
    """Liest Text aus PDF, Word oder TXT."""
    import os
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        try:
            import fitz  # pymupdf
            doc = fitz.open(path)
            pages = []
            for i, page in enumerate(doc):
                pages.append(f"[Seite {i+1}]\n{page.get_text()}")
            return "\n\n".join(pages)
        except Exception as e:
            return f"PDF-Fehler: {e}"

    elif ext in (".docx", ".doc"):
        try:
            import docx
            d = docx.Document(path)
            return "\n".join(p.text for p in d.paragraphs if p.text.strip())
        except ImportError:
            return "python-docx nicht installiert. Bitte als .txt oder .pdf speichern."
        except Exception as e:
            return f"Word-Fehler: {e}"

    elif ext in (".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm"):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            return f"Lesefehler: {e}"

    else:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return f"Dateiformat '{ext}' wird nicht unterstützt."


def truncate_for_ai(text: str, max_chars: int = 12000) -> str:
    """Kürzt Text für AI-Kontext — nimmt Anfang + Ende."""
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + f"\n\n[... {len(text) - max_chars} Zeichen übersprungen ...]\n\n" + text[-half:]


class AIWorker(QThread):
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


class LearnPanel(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VADOX — Lern-Modus")
        self.setMinimumSize(950, 680)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background:{BG}; }}")
        self._doc_text  = ""
        self._doc_name  = ""
        self._worker    = None
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
        b_lay.addWidget(_lbl("LERN-MODUS", size=13, color=CYAN, bold=True))
        b_lay.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"background:transparent; color:{TEXTD}; font-size:14px; border:none;")
        close_btn.clicked.connect(self.accept)
        b_lay.addWidget(close_btn)
        lay.addWidget(bar)

        # Dokument-Lade-Leiste
        doc_bar = QFrame()
        doc_bar.setFixedHeight(56)
        doc_bar.setStyleSheet(f"background:{CARD}; border-bottom:1px solid {BORDER};")
        d_lay = QHBoxLayout(doc_bar)
        d_lay.setContentsMargins(16, 0, 16, 0)
        d_lay.setSpacing(10)

        load_btn = _btn("📂  Dokument laden", color=CYAN, h=36)
        load_btn.clicked.connect(self._load_document)
        d_lay.addWidget(load_btn)

        self._doc_label = _lbl("Kein Dokument geladen", size=9, color=TEXTD)
        d_lay.addWidget(self._doc_label)
        d_lay.addStretch()

        self._doc_info = _lbl("", size=9, color=GREEN)
        d_lay.addWidget(self._doc_info)
        lay.addWidget(doc_bar)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border:none; background:{BG}; }}
            QTabBar::tab {{ background:{BG}; color:{TEXTD}; font-family:'Courier New';
                font-size:10px; padding:8px 20px; border:1px solid {BORDER};
                border-bottom:none; border-top-left-radius:6px; border-top-right-radius:6px; }}
            QTabBar::tab:selected {{ background:{CARD}; color:{CYAN}; }}
        """)
        tabs.addTab(self._tab_summary(),    "📋  ZUSAMMENFASSUNG")
        tabs.addTab(self._tab_qa(),         "💬  FRAGEN & ANTWORTEN")
        tabs.addTab(self._tab_quiz(),       "🎯  QUIZ")
        tabs.addTab(self._tab_mindmap(),    "🧠  KERNPUNKTE")
        tabs.addTab(self._tab_flashcards(), "🃏  LERNKARTEN")
        lay.addWidget(tabs, stretch=1)

    # ── Dokument laden ────────────────────────────────────────────────────────
    def _load_document(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Dokument öffnen", "",
            "Dokumente (*.pdf *.txt *.md *.docx *.csv *.json *.html *.htm);;Alle Dateien (*)"
        )
        if not path:
            return
        import os
        self._doc_label.setText(f"⏳ Lade {os.path.basename(path)}...")
        self._doc_label.setStyleSheet(f"color:{AMBER}; background:transparent;")

        def _load():
            text = extract_text_from_file(path)
            self._doc_text = text
            self._doc_name = os.path.basename(path)
            chars = len(text)
            words = len(text.split())

            from PyQt6.QtCore import QMetaObject, Q_ARG, Qt
            from PyQt6.QtCore import pyqtSlot

            self._doc_label.setText(f"✅  {self._doc_name}")
            self._doc_label.setStyleSheet(f"color:{GREEN}; background:transparent;")
            self._doc_info.setText(f"{words:,} Wörter  ·  {chars:,} Zeichen")

        import threading
        threading.Thread(target=_load, daemon=True).start()

    # ── Hilfsmethode: Worker starten ──────────────────────────────────────────
    def _run(self, prompt: str, result_box: QTextEdit, btn: QPushButton):
        if not self._doc_text:
            result_box.setPlainText("⚠️  Bitte zuerst ein Dokument laden.")
            return
        result_box.setPlainText("")
        original_text = btn.text()
        btn.setEnabled(False)
        btn.setText("⏳ Läuft...")
        worker = AIWorker(prompt)
        worker.chunk.connect(lambda c: result_box.insertPlainText(c))
        def on_done():
            btn.setEnabled(True)
            btn.setText(original_text)
            sb = result_box.verticalScrollBar()
            sb.setValue(sb.maximum())
        worker.done.connect(on_done)
        worker.start()
        self._worker = worker

    def _doc_context(self, max_chars=12000) -> str:
        return truncate_for_ai(self._doc_text, max_chars)

    # ── Tab: Zusammenfassung ──────────────────────────────────────────────────
    def _tab_summary(self) -> QWidget:
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        # Länge wählen
        top = QHBoxLayout()
        top.addWidget(_lbl("Zusammenfassungs-Länge:", size=9, color=TEXTD))
        from PyQt6.QtWidgets import QComboBox
        length_combo = QComboBox()
        for opt in ["Kurz (3-5 Sätze)", "Mittel (1 Absatz)", "Detailliert (mehrere Absätze)", "Executive Summary"]:
            length_combo.addItem(opt)
        length_combo.setCurrentIndex(1)
        length_combo.setFixedHeight(32)
        length_combo.setStyleSheet(f"""
            QComboBox {{ background:{CARD}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:10px; padding:0 10px; border-radius:6px; }}
            QComboBox QAbstractItemView {{ background:{CARD}; color:{CYAN}; border:1px solid {BORDER}; }}
        """)
        top.addWidget(length_combo)
        top.addStretch()
        lay.addLayout(top)

        # Schnell-Buttons
        quick_row = QHBoxLayout()
        quick_actions = [
            ("📋 Zusammenfassen",    "zusammenfassen"),
            ("🔑 Schlüsselpunkte",   "schluessel"),
            ("📊 Statistiken",       "statistiken"),
            ("🎯 Fazit",             "fazit"),
        ]
        result = _result_box("Zusammenfassung erscheint hier...")
        for label, action in quick_actions:
            b = _btn(label, color=CYAN_D, h=34)
            b.setFont(QFont("Courier New", 9))
            def make_run(act, btn_ref=b):
                def run():
                    doc = self._doc_context()
                    name = self._doc_name or "Dokument"
                    length_str = length_combo.currentText()
                    if act == "zusammenfassen":
                        prompt = (
                            f"Fasse das folgende Dokument '{name}' auf Deutsch zusammen.\n"
                            f"Laenge: {length_str}\n\n"
                            f"Dokument:\n{doc}"
                        )
                    elif act == "schluessel":
                        prompt = (
                            f"Extrahiere die 5-10 wichtigsten Schluessel-Punkte aus diesem Dokument '{name}'.\n"
                            f"Format: nummerierte Liste, jeder Punkt ein klarer Satz.\n\n"
                            f"Dokument:\n{doc}"
                        )
                    elif act == "statistiken":
                        prompt = (
                            f"Extrahiere alle wichtigen Zahlen, Statistiken und Fakten aus diesem Dokument '{name}'.\n"
                            f"Format: uebersichtliche Liste mit Kontext.\n\n"
                            f"Dokument:\n{doc}"
                        )
                    else:  # fazit
                        prompt = (
                            f"Schreibe ein praegnantes Fazit fuer das Dokument '{name}'.\n"
                            f"Was sind die wichtigsten Erkenntnisse und Schlussfolgerungen?\n\n"
                            f"Dokument:\n{doc}"
                        )
                    self._run(prompt, result, btn_ref)
                return run
            b.clicked.connect(make_run(action))
            quick_row.addWidget(b)
        lay.addLayout(quick_row)

        lay.addWidget(result, stretch=1)

        btn_row = QHBoxLayout()
        speak_btn = _btn("🔊 Vorlesen", color=TEXTD, h=34)
        speak_btn.clicked.connect(lambda: self._speak(result.toPlainText()))
        copy_btn = _btn("📋 Kopieren", color=TEXTD, h=34)
        copy_btn.clicked.connect(lambda: self._copy(result.toPlainText()))
        btn_row.addWidget(speak_btn)
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)
        return w

    # ── Tab: Fragen & Antworten ───────────────────────────────────────────────
    def _tab_qa(self) -> QWidget:
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        lay.addWidget(_lbl("Stelle Fragen zu deinem Dokument:", size=9, color=TEXTD))

        # Chat-Verlauf
        self._qa_history = _result_box("Stelle eine Frage zum geladenen Dokument...")
        lay.addWidget(self._qa_history, stretch=1)

        # Vorschlag-Fragen
        suggest_row = QHBoxLayout()
        suggestions = [
            "Was ist das Hauptthema?",
            "Was sind die Kernaussagen?",
            "Welche Probleme werden genannt?",
            "Was sind die Empfehlungen?",
        ]
        self._qa_input = QLineEdit()
        for s in suggestions:
            b = _btn(s, color=PURPLE, h=28)
            b.setFont(QFont("Courier New", 8))
            b.clicked.connect(lambda _, q=s: self._qa_input.setText(q))
            suggest_row.addWidget(b)
        lay.addLayout(suggest_row)

        # Eingabe
        input_row = QHBoxLayout()
        self._qa_input.setPlaceholderText("Frage zum Dokument eingeben...")
        self._qa_input.setFixedHeight(38)
        self._qa_input.setStyleSheet(f"""
            QLineEdit {{ background:{CARD}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:11px; border-radius:6px; padding:0 12px; }}
            QLineEdit:focus {{ border-color:{CYAN}; }}
        """)
        ask_btn = _btn("Fragen", color=GREEN, w=100, h=38)
        self._qa_input.returnPressed.connect(lambda: self._ask_question(ask_btn))
        ask_btn.clicked.connect(lambda: self._ask_question(ask_btn))
        clear_btn = _btn("Löschen", color=TEXTD, w=80, h=38)
        clear_btn.clicked.connect(lambda: self._qa_history.clear())
        input_row.addWidget(self._qa_input)
        input_row.addWidget(ask_btn)
        input_row.addWidget(clear_btn)
        lay.addLayout(input_row)
        return w

    def _ask_question(self, btn: QPushButton):
        question = self._qa_input.text().strip()
        if not question or not self._doc_text:
            if not self._doc_text:
                self._qa_history.setPlainText("⚠️  Bitte zuerst ein Dokument laden.")
            return
        self._qa_input.clear()
        self._qa_history.append(f"\n❓ Du: {question}\n")
        doc = self._doc_context(10000)
        prompt = (
            f"Beantworte diese Frage basierend NUR auf dem folgenden Dokument '{self._doc_name}'.\n"
            f"Falls die Antwort nicht im Dokument steht, sag das klar.\n\n"
            f"Frage: {question}\n\n"
            f"Dokument:\n{doc}"
        )
        original = btn.text()
        btn.setEnabled(False)
        btn.setText("⏳")
        self._qa_history.append("🤖 Vadox: ")
        worker = AIWorker(prompt)
        worker.chunk.connect(lambda c: self._qa_history.insertPlainText(c))
        def on_done():
            btn.setEnabled(True)
            btn.setText(original)
            self._qa_history.append("\n")
            sb = self._qa_history.verticalScrollBar()
            sb.setValue(sb.maximum())
        worker.done.connect(on_done)
        worker.start()
        self._worker = worker

    # ── Tab: Quiz ─────────────────────────────────────────────────────────────
    def _tab_quiz(self) -> QWidget:
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        top = QHBoxLayout()
        top.addWidget(_lbl("Anzahl Fragen:", size=9, color=TEXTD))
        from PyQt6.QtWidgets import QComboBox
        num_combo = QComboBox()
        for n in ["5 Fragen", "10 Fragen", "15 Fragen", "20 Fragen"]:
            num_combo.addItem(n)
        num_combo.setFixedHeight(32)
        num_combo.setStyleSheet(f"""
            QComboBox {{ background:{CARD}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:10px; padding:0 10px; border-radius:6px; }}
            QComboBox QAbstractItemView {{ background:{CARD}; color:{CYAN}; border:1px solid {BORDER}; }}
        """)
        top.addWidget(num_combo)

        top.addWidget(_lbl("Typ:", size=9, color=TEXTD))
        type_combo = QComboBox()
        for t in ["Multiple Choice", "Wahr/Falsch", "Offen (Freitext)", "Gemischt"]:
            type_combo.addItem(t)
        type_combo.setFixedHeight(32)
        type_combo.setStyleSheet(num_combo.styleSheet())
        top.addWidget(type_combo)
        top.addStretch()
        lay.addLayout(top)

        result = _result_box("Quiz erscheint hier nach dem Generieren...")
        lay.addWidget(result, stretch=1)

        btn = _btn("🎯  Quiz generieren", color=AMBER, h=38)
        btn_row = QHBoxLayout()
        copy_btn = _btn("📋 Kopieren", color=TEXTD, h=38)
        copy_btn.clicked.connect(lambda: self._copy(result.toPlainText()))
        btn_row.addWidget(btn)
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        def run():
            num = num_combo.currentText().split()[0]
            typ = type_combo.currentText()
            doc = self._doc_context()
            name = self._doc_name or "Dokument"
            prompt = (
                f"Erstelle {num} {typ}-Fragen basierend auf dem Dokument '{name}'.\n\n"
                f"Format:\n"
                f"- Frage klar formulieren\n"
                f"- Bei Multiple Choice: 4 Antwortmoeglichkeiten (A/B/C/D), richtige markieren\n"
                f"- Bei Wahr/Falsch: Antwort + kurze Begruendung\n"
                f"- Bei offenen Fragen: Musterloesung am Ende\n"
                f"- Schwierigkeit: abwechslungsreich\n\n"
                f"Dokument:\n{doc}"
            )
            self._run(prompt, result, btn)
        btn.clicked.connect(run)
        return w

    # ── Tab: Kernpunkte / Mind-Map ────────────────────────────────────────────
    def _tab_mindmap(self) -> QWidget:
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        result = _result_box("Strukturierte Kernpunkte erscheinen hier...")
        lay.addWidget(result, stretch=1)

        btn_row = QHBoxLayout()
        actions = [
            ("🧠 Kernpunkte", "kernpunkte", CYAN),
            ("📊 Struktur-Übersicht", "struktur", PURPLE),
            ("🔗 Zusammenhänge", "zusammenhaenge", ORANGE),
            ("📝 Lernnotizen", "notizen", GREEN),
        ]
        for label, action, color in actions:
            b = _btn(label, color=color, h=36)
            def make_run(act, btn_ref=b):
                def run():
                    doc = self._doc_context()
                    name = self._doc_name or "Dokument"
                    if act == "kernpunkte":
                        prompt = (
                            f"Erstelle eine strukturierte Kernpunkt-Uebersicht des Dokuments '{name}'.\n"
                            f"Nutze eine klare Hierarchie mit Hauptthemen und Unterpunkten.\n\n"
                            f"Dokument:\n{doc}"
                        )
                    elif act == "struktur":
                        prompt = (
                            f"Erstelle eine Struktur-Uebersicht des Dokuments '{name}'.\n"
                            f"Zeige wie das Dokument aufgebaut ist und welche Abschnitte es gibt.\n\n"
                            f"Dokument:\n{doc}"
                        )
                    elif act == "zusammenhaenge":
                        prompt = (
                            f"Analysiere die wichtigsten Zusammenhaenge und Beziehungen im Dokument '{name}'.\n"
                            f"Erklaere wie die Konzepte und Ideen miteinander verbunden sind.\n\n"
                            f"Dokument:\n{doc}"
                        )
                    else:  # notizen
                        prompt = (
                            f"Erstelle praegnante Lernnotizen fuer das Dokument '{name}'.\n"
                            f"Format: kompakte Stichpunkte, die man gut zum Wiederholen nutzen kann.\n\n"
                            f"Dokument:\n{doc}"
                        )
                    self._run(prompt, result, btn_ref)
                return run
            b.clicked.connect(make_run(action))
            btn_row.addWidget(b)
        lay.addLayout(btn_row)

        bottom_row = QHBoxLayout()
        speak_btn = _btn("🔊 Vorlesen", color=TEXTD, h=34)
        speak_btn.clicked.connect(lambda: self._speak(result.toPlainText()))
        copy_btn = _btn("📋 Kopieren", color=TEXTD, h=34)
        copy_btn.clicked.connect(lambda: self._copy(result.toPlainText()))
        bottom_row.addWidget(speak_btn)
        bottom_row.addWidget(copy_btn)
        bottom_row.addStretch()
        lay.addLayout(bottom_row)
        return w

    # ── Tab: Lernkarten ───────────────────────────────────────────────────────
    def _tab_flashcards(self) -> QWidget:
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        result = _result_box("Lernkarten erscheinen hier...")
        lay.addWidget(result, stretch=1)

        btn_row = QHBoxLayout()
        btn = _btn("🃏  Lernkarten generieren", color=PURPLE, h=38)
        copy_btn = _btn("📋 Kopieren", color=TEXTD, h=38)
        copy_btn.clicked.connect(lambda: self._copy(result.toPlainText()))
        btn_row.addWidget(btn)
        btn_row.addWidget(copy_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        def run():
            doc = self._doc_context()
            name = self._doc_name or "Dokument"
            prompt = (
                f"Erstelle 10-15 Lernkarten (Flashcards) aus dem Dokument '{name}'.\n\n"
                f"Format fuer jede Karte:\n"
                f"VORDERSEITE: [Frage oder Begriff]\n"
                f"RUECKSEITE: [Antwort oder Erklaerung]\n"
                f"---\n\n"
                f"Die Karten sollen die wichtigsten Konzepte, Definitionen und Fakten abdecken.\n\n"
                f"Dokument:\n{doc}"
            )
            self._run(prompt, result, btn)
        btn.clicked.connect(run)
        return w

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────
    def _speak(self, text: str):
        if not text.strip():
            return
        import threading
        def _do():
            try:
                from vadox.core.tts_engine import TTSEngine, clean_for_speech
                from vadox.core import settings
                cfg = settings.load()
                voice = cfg.get("voice", "de-DE-KatjaNeural")
                cleaned = clean_for_speech(text[:800])
                if cleaned:
                    TTSEngine(voice=voice).speak(cleaned)
            except Exception as e:
                print(f"[TTS] {e}")
        threading.Thread(target=_do, daemon=True).start()

    def _copy(self, text: str):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
