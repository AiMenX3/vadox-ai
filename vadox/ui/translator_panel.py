# -*- coding: utf-8 -*-
"""
Vadox Übersetzer & KI Sprachlehrer Panel
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget, QTextEdit, QComboBox, QTabWidget, QScrollArea,
    QLineEdit, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
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


class TranslateWorker(QThread):
    done = pyqtSignal(str)

    def __init__(self, text, target, source="auto"):
        super().__init__()
        self._text = text
        self._target = target
        self._source = source

    def run(self):
        from vadox.tools.translator import translate_text
        result = translate_text(self._text, self._target, self._source)
        self.done.emit(result)


class LessonWorker(QThread):
    done = pyqtSignal(str)

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
            result = []
            done_flag = [False]

            def on_chunk(c):
                result.append(c)

            def on_done(_):
                done_flag[0] = True

            engine.chat(self._prompt, on_chunk=on_chunk, on_done=on_done)

            import time
            waited = 0
            while not done_flag[0] and waited < 30:
                time.sleep(0.1)
                waited += 0.1

            self.done.emit("".join(result))
        except Exception as e:
            self.done.emit(f"Fehler: {e}")


LANGUAGE_OPTS = [
    ("Englisch 🇬🇧",     "en", "englisch"),
    ("Spanisch 🇪🇸",     "es", "spanisch"),
    ("Franzoesisch 🇫🇷", "fr", "franzoesisch"),
    ("Italienisch 🇮🇹",  "it", "italienisch"),
    ("Japanisch 🇯🇵",    "ja", "japanisch"),
    ("Chinesisch 🇨🇳",   "zh-CN", "chinesisch"),
    ("Arabisch 🇸🇦",     "ar", "arabisch"),
    ("Russisch 🇷🇺",     "ru", "russisch"),
    ("Tuerkisch 🇹🇷",    "tr", "tuerkisch"),
    ("Portugiesisch 🇵🇹","pt", "portugiesisch"),
]


class TranslatorPanel(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VADOX — Übersetzer & Sprachlehrer")
        self.setMinimumSize(800, 620)
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
        b_lay.addWidget(_lbl("ÜBERSETZER  &  KI SPRACHLEHRER", size=13, color=CYAN, bold=True))
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
        tabs.addTab(self._tab_translator(), "🌍  ÜBERSETZER")
        tabs.addTab(self._tab_teacher(),    "📚  SPRACHLEHRER")
        tabs.addTab(self._tab_vocabulary(), "🃏  VOKABELN")
        lay.addWidget(tabs, stretch=1)

    # ── Tab 1: Übersetzer ─────────────────────────────────────────────────────
    def _tab_translator(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        # Sprach-Auswahl Zeile
        lang_row = QHBoxLayout()
        lang_row.addWidget(_lbl("Von:", size=9, color=TEXTD))
        self._src_combo = QComboBox()
        self._src_combo.addItem("Automatisch erkennen", "auto")
        for name, code, _ in LANGUAGE_OPTS:
            self._src_combo.addItem(name, code)
        self._src_combo.setFixedHeight(34)
        self._src_combo.setStyleSheet(f"""
            QComboBox {{ background:{CARD}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:10px; padding:0 10px; border-radius:6px; }}
            QComboBox QAbstractItemView {{ background:{CARD}; color:{CYAN}; border:1px solid {BORDER}; }}
        """)
        lang_row.addWidget(self._src_combo)

        swap_btn = _btn("⇄", color=CYAN_D, w=40)
        swap_btn.clicked.connect(self._swap_languages)
        lang_row.addWidget(swap_btn)

        lang_row.addWidget(_lbl("Nach:", size=9, color=TEXTD))
        self._tgt_combo = QComboBox()
        for name, code, _ in LANGUAGE_OPTS:
            self._tgt_combo.addItem(name, code)
        self._tgt_combo.setFixedHeight(34)
        self._tgt_combo.setStyleSheet(self._src_combo.styleSheet())
        lang_row.addWidget(self._tgt_combo)
        lay.addLayout(lang_row)

        # Eingabe / Ausgabe nebeneinander
        text_row = QHBoxLayout()
        text_row.setSpacing(12)

        # Eingabe
        in_col = QVBoxLayout()
        in_col.addWidget(_lbl("Eingabe:", size=9, color=TEXTD))
        self._input_text = QTextEdit()
        self._input_text.setPlaceholderText("Text zum Übersetzen eingeben...")
        self._input_text.setMinimumHeight(180)
        self._input_text.setStyleSheet(f"""
            QTextEdit {{ background:{CARD}; border:1px solid {BORDER}; color:{TEXT};
                font-family:'Courier New'; font-size:11px; border-radius:8px; padding:10px; }}
        """)
        in_col.addWidget(self._input_text)
        text_row.addLayout(in_col)

        # Ausgabe
        out_col = QVBoxLayout()
        out_col.addWidget(_lbl("Übersetzung:", size=9, color=TEXTD))
        self._output_text = QTextEdit()
        self._output_text.setReadOnly(True)
        self._output_text.setMinimumHeight(180)
        self._output_text.setStyleSheet(f"""
            QTextEdit {{ background:{CARD}; border:1px solid {CYAN_D}; color:{CYAN};
                font-family:'Courier New'; font-size:11px; border-radius:8px; padding:10px; }}
        """)
        out_col.addWidget(self._output_text)
        text_row.addLayout(out_col)
        lay.addLayout(text_row)

        # Buttons
        btn_row = QHBoxLayout()
        translate_btn = _btn("🌍  Übersetzen", color=CYAN, h=40)
        translate_btn.clicked.connect(self._do_translate)
        speak_in_btn  = _btn("🔊  Eingabe vorlesen", color=TEXTD, h=40)
        speak_in_btn.clicked.connect(lambda: self._speak(
            self._input_text.toPlainText(),
            self._src_combo.currentData() or "de"
        ))
        speak_out_btn = _btn("🔊  Übersetzung vorlesen", color=GREEN, h=40)
        speak_out_btn.clicked.connect(lambda: self._speak(
            self._output_text.toPlainText(),
            self._tgt_combo.currentData() or "de"
        ))
        copy_btn = _btn("📋  Kopieren", color=TEXTD, h=40)
        copy_btn.clicked.connect(self._copy_output)
        btn_row.addWidget(translate_btn)
        btn_row.addWidget(speak_in_btn)
        btn_row.addWidget(speak_out_btn)
        btn_row.addWidget(copy_btn)
        lay.addLayout(btn_row)

        self._translate_status = _lbl("", size=9, color=TEXTD)
        lay.addWidget(self._translate_status)

        # Enter-Shortcut
        self._input_text.textChanged.connect(self._on_input_changed)
        return w

    # ── Tab 2: Sprachlehrer ───────────────────────────────────────────────────
    def _tab_teacher(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        # Sprache + Level wählen
        top_row = QHBoxLayout()
        top_row.addWidget(_lbl("Sprache:", size=9, color=TEXTD))
        self._teach_lang = QComboBox()
        for name, _, _ in LANGUAGE_OPTS:
            self._teach_lang.addItem(name)
        self._teach_lang.setFixedHeight(34)
        self._teach_lang.setStyleSheet(f"""
            QComboBox {{ background:{CARD}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:10px; padding:0 10px; border-radius:6px; }}
            QComboBox QAbstractItemView {{ background:{CARD}; color:{CYAN}; border:1px solid {BORDER}; }}
        """)
        top_row.addWidget(self._teach_lang)

        top_row.addSpacing(16)
        top_row.addWidget(_lbl("Level:", size=9, color=TEXTD))
        self._teach_level = QComboBox()
        for lvl in ["A1 — Anfänger", "A2 — Grundlagen", "B1 — Mittelstufe",
                    "B2 — Obere Mittelstufe", "C1 — Fortgeschritten", "C2 — Experte"]:
            self._teach_level.addItem(lvl)
        self._teach_level.setFixedHeight(34)
        self._teach_level.setStyleSheet(self._teach_lang.styleSheet())
        top_row.addWidget(self._teach_level)
        top_row.addStretch()
        lay.addLayout(top_row)

        # Lektion-Buttons
        lay.addWidget(_lbl("Lektion wählen:", size=9, color=TEXTD))
        grid = QGridLayout()
        grid.setSpacing(8)
        lessons = [
            ("📖 Einführung & Begrüßung",   "Erklaere mir eine typische Begrüssung und Vorstellung"),
            ("🔢 Zahlen & Zeiten",           "Erklaere mir Zahlen von 1-100 und wie man die Uhrzeit sagt"),
            ("🍕 Essen & Restaurantbesuch",  "Erklaere mir Vokabeln rund ums Essen und wie man im Restaurant bestellt"),
            ("✈️ Reisen & Navigation",       "Erklaere mir wichtige Saetze fuers Reisen, Flughafen und Navigation"),
            ("💼 Business & Arbeit",         "Erklaere mir wichtige Business-Ausdruecke und Businesskommunikation"),
            ("💬 Smalltalk & Allgemein",     "Erklaere mir typische Smalltalk-Saetze und alltaegliche Gespraeche"),
            ("🏥 Notfall & Gesundheit",      "Erklaere mir wichtige Saetze fuer Notfaelle und Gesundheitssituationen"),
            ("🛒 Einkaufen & Preise",        "Erklaere mir wie man einkauft, nach Preisen fragt und verhandelt"),
        ]
        for i, (label, _) in enumerate(lessons):
            b = _btn(label, color=CYAN_D if i % 2 == 0 else PURPLE, h=38)
            lesson_text = lessons[i][1]
            b.clicked.connect(lambda _, lt=lesson_text: self._start_lesson(lt))
            grid.addWidget(b, i // 2, i % 2)
        lay.addLayout(grid)

        # Eigene Frage
        lay.addWidget(_lbl("Oder eigene Frage an den Sprachlehrer:", size=9, color=TEXTD))
        custom_row = QHBoxLayout()
        self._custom_question = QLineEdit()
        self._custom_question.setPlaceholderText('z.B. "Wie sage ich auf Englisch: Ich hätte gerne..."')
        self._custom_question.setFixedHeight(34)
        self._custom_question.setStyleSheet(f"""
            QLineEdit {{ background:{CARD}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:10px; border-radius:6px; padding:0 10px; }}
            QLineEdit:focus {{ border-color:{CYAN}; }}
        """)
        ask_btn = _btn("Fragen", color=GREEN, w=100)
        ask_btn.clicked.connect(self._ask_custom)
        self._custom_question.returnPressed.connect(self._ask_custom)
        custom_row.addWidget(self._custom_question)
        custom_row.addWidget(ask_btn)
        lay.addLayout(custom_row)

        # Antwort-Feld
        self._lesson_output = QTextEdit()
        self._lesson_output.setReadOnly(True)
        self._lesson_output.setMinimumHeight(160)
        self._lesson_output.setStyleSheet(f"""
            QTextEdit {{ background:{CARD}; border:1px solid {BORDER}; color:{TEXT};
                font-family:'Courier New'; font-size:11px; border-radius:8px; padding:12px; }}
        """)
        self._lesson_output.setPlaceholderText("Hier erscheint deine Lektion...")
        lay.addWidget(self._lesson_output, stretch=1)

        speak_lesson_btn = _btn("🔊  Lektion vorlesen", color=CYAN_D, h=34)
        speak_lesson_btn.clicked.connect(lambda: self._speak(self._lesson_output.toPlainText()))
        lay.addWidget(speak_lesson_btn)

        return w

    # ── Tab 3: Vokabeln ───────────────────────────────────────────────────────
    def _tab_vocabulary(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        top = QHBoxLayout()
        top.addWidget(_lbl("Sprache:", size=9, color=TEXTD))
        self._vocab_lang = QComboBox()
        for name, _, _ in LANGUAGE_OPTS:
            self._vocab_lang.addItem(name)
        self._vocab_lang.setFixedHeight(34)
        self._vocab_lang.setStyleSheet(f"""
            QComboBox {{ background:{CARD}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:10px; padding:0 10px; border-radius:6px; }}
            QComboBox QAbstractItemView {{ background:{CARD}; color:{CYAN}; border:1px solid {BORDER}; }}
        """)
        top.addWidget(self._vocab_lang)
        top.addSpacing(16)
        top.addWidget(_lbl("Thema:", size=9, color=TEXTD))
        self._vocab_topic = QLineEdit()
        self._vocab_topic.setPlaceholderText("z.B. Essen, Sport, Familie...")
        self._vocab_topic.setFixedHeight(34)
        self._vocab_topic.setStyleSheet(f"""
            QLineEdit {{ background:{CARD}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:10px; border-radius:6px; padding:0 10px; }}
        """)
        top.addWidget(self._vocab_topic)
        gen_btn = _btn("Generieren", color=PURPLE, w=120)
        gen_btn.clicked.connect(self._generate_vocab)
        top.addWidget(gen_btn)
        lay.addLayout(top)

        self._vocab_output = QTextEdit()
        self._vocab_output.setReadOnly(True)
        self._vocab_output.setStyleSheet(f"""
            QTextEdit {{ background:{CARD}; border:1px solid {BORDER}; color:{TEXT};
                font-family:'Courier New'; font-size:11px; border-radius:8px; padding:12px; }}
        """)
        self._vocab_output.setPlaceholderText("Vokabelliste wird hier angezeigt...")
        lay.addWidget(self._vocab_output, stretch=1)

        btn_row = QHBoxLayout()
        quiz_btn  = _btn("🎯  Quiz starten", color=AMBER, h=36)
        speak_btn = _btn("🔊  Vorlesen", color=CYAN_D, h=36)
        quiz_btn.clicked.connect(self._start_quiz)
        speak_btn.clicked.connect(lambda: self._speak(self._vocab_output.toPlainText()))
        btn_row.addWidget(quiz_btn)
        btn_row.addWidget(speak_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        return w

    # ── Aktionen ──────────────────────────────────────────────────────────────
    def _on_input_changed(self):
        # Auto-Übersetzung nach kurzer Pause
        if hasattr(self, '_auto_timer'):
            self._auto_timer.stop()
        self._auto_timer = QTimer()
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._do_translate)
        self._auto_timer.start(1200)  # 1.2 Sek nach letzter Eingabe

    def _do_translate(self):
        text = self._input_text.toPlainText().strip()
        if not text:
            return
        src  = self._src_combo.currentData()
        tgt  = self._tgt_combo.currentData()
        self._translate_status.setText("Übersetze...")
        self._translate_status.setStyleSheet(f"color:{AMBER}; background:transparent;")
        self._output_text.setPlainText("")
        worker = TranslateWorker(text, tgt, src)
        worker.done.connect(self._on_translate_done)
        worker.start()
        self._translate_worker = worker

    def _on_translate_done(self, result: str):
        # "[Englisch] " Prefix entfernen für saubere Anzeige
        if "] " in result:
            result = result.split("] ", 1)[1]
        self._output_text.setPlainText(result)
        self._translate_status.setText("Übersetzt")
        self._translate_status.setStyleSheet(f"color:{GREEN}; background:transparent;")

    def _swap_languages(self):
        src_idx = self._src_combo.currentIndex()
        tgt_idx = self._tgt_combo.currentIndex()
        # Eingabe ↔ Ausgabe tauschen
        in_text  = self._input_text.toPlainText()
        out_text = self._output_text.toPlainText()
        self._input_text.setPlainText(out_text)
        self._output_text.setPlainText(in_text)
        # Sprachen tauschen (src startet bei index 1 weil "auto" an 0)
        if src_idx > 0:
            self._src_combo.setCurrentIndex(tgt_idx + 1)
        self._tgt_combo.setCurrentIndex(max(0, src_idx - 1))

    def _copy_output(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._output_text.toPlainText())
        self._translate_status.setText("Kopiert!")
        self._translate_status.setStyleSheet(f"color:{GREEN}; background:transparent;")

    def _start_lesson(self, lesson_text: str):
        lang_name = self._teach_lang.currentText().split(" ")[0].split(" ")[0].strip()
        level_str = self._teach_level.currentText().split("—")[0].strip()
        prompt = (
            f"Du bist ein erfahrener Sprachlehrer. Der Schüler lernt {lang_name} auf Niveau {level_str}.\n"
            f"Aufgabe: {lesson_text} auf {lang_name}.\n\n"
            f"Gib:\n"
            f"1. Eine kurze Erklärung auf Deutsch\n"
            f"2. 8-10 wichtige Wörter/Sätze mit Aussprache-Hilfe\n"
            f"3. Ein kurzes Beispieldialog\n"
            f"4. Einen Tipp zum Lernen\n\n"
            f"Format: übersichtlich, mit Emojis, leicht verständlich."
        )
        self._lesson_output.setPlainText("⏳ Lektion wird vorbereitet...")
        worker = LessonWorker(prompt)
        worker.done.connect(self._lesson_output.setPlainText)
        worker.start()
        self._lesson_worker = worker

    def _ask_custom(self):
        question = self._custom_question.text().strip()
        if not question:
            return
        lang_name = self._teach_lang.currentText().split(" ")[0]
        level_str = self._teach_level.currentText().split("—")[0].strip()
        prompt = (
            f"Du bist ein Sprachlehrer für {lang_name} (Niveau {level_str}).\n"
            f"Beantworte diese Frage des Schülers klar und hilfreich auf Deutsch:\n{question}"
        )
        self._lesson_output.setPlainText("⏳ Antwort wird vorbereitet...")
        self._custom_question.clear()
        worker = LessonWorker(prompt)
        worker.done.connect(self._lesson_output.setPlainText)
        worker.start()
        self._lesson_worker = worker

    def _generate_vocab(self):
        lang_name = self._vocab_lang.currentText().split(" ")[0]
        topic = self._vocab_topic.text().strip() or "Alltag"
        prompt = (
            f"Erstelle eine Vokabelliste mit 15 wichtigen Wörtern zum Thema '{topic}' auf {lang_name}.\n"
            f"Format pro Zeile: Deutsch | {lang_name} | Aussprache-Hilfe\n"
            f"Dann 3 kurze Beispielsätze mit dem Thema."
        )
        self._vocab_output.setPlainText("⏳ Vokabeln werden generiert...")
        worker = LessonWorker(prompt)
        worker.done.connect(self._vocab_output.setPlainText)
        worker.start()
        self._vocab_worker = worker

    def _start_quiz(self):
        content = self._vocab_output.toPlainText()
        if not content or "⏳" in content:
            return
        lang_name = self._vocab_lang.currentText().split(" ")[0]
        prompt = (
            f"Erstelle ein kurzes Quiz mit 5 Fragen basierend auf diesen Vokabeln:\n{content[:500]}\n\n"
            f"Format: Frage auf Deutsch, dann 3 Antwortmöglichkeiten auf {lang_name}, "
            f"dann die richtige Antwort markieren. Mach es spielerisch!"
        )
        self._vocab_output.setPlainText("⏳ Quiz wird erstellt...")
        worker = LessonWorker(prompt)
        worker.done.connect(self._vocab_output.setPlainText)
        worker.start()
        self._vocab_worker = worker

    # Stimme je nach Sprache auswählen
    _LANG_VOICES = {
        "en": "en-US-AriaNeural",
        "es": "es-ES-ElviraNeural",
        "fr": "fr-FR-DeniseNeural",
        "it": "it-IT-ElsaNeural",
        "pt": "pt-PT-RaquelNeural",
        "nl": "nl-NL-ColetteNeural",
        "pl": "pl-PL-AgnieszkaNeural",
        "ru": "ru-RU-SvetlanaNeural",
        "zh-CN": "zh-CN-XiaoxiaoNeural",
        "ja": "ja-JP-NanamiNeural",
        "ko": "ko-KR-SunHiNeural",
        "ar": "ar-EG-SalmaNeural",
        "tr": "tr-TR-EmelNeural",
        "sv": "sv-SE-SofieNeural",
        "no": "nb-NO-PernilleNeural",
        "da": "da-DK-ChristelNeural",
        "fi": "fi-FI-NooraNeural",
        "el": "el-GR-AthinaNeural",
        "hu": "hu-HU-NoemiNeural",
        "cs": "cs-CZ-VlastaNeural",
        "ro": "ro-RO-AlinaNeural",
        "uk": "uk-UA-PolinaNeural",
        "hi": "hi-IN-SwaraNeural",
        "vi": "vi-VN-HoaiMyNeural",
        "id": "id-ID-GadisNeural",
        "th": "th-TH-PremwadeeNeural",
        "de": "de-DE-KatjaNeural",
    }

    def _speak(self, text: str, lang_code: str = "de"):
        if not text.strip():
            return
        import threading
        def _do():
            try:
                from vadox.core.tts_engine import TTSEngine, clean_for_speech
                from vadox.core import settings
                cfg = settings.load()
                voice = self._LANG_VOICES.get(lang_code, cfg.get("voice", "de-DE-KatjaNeural"))
                cleaned = clean_for_speech(text[:600])
                if not cleaned:
                    return
                tts = TTSEngine(voice=voice)
                tts.speak(cleaned)
            except Exception as e:
                print(f"[TTS Fehler] {e}")
        threading.Thread(target=_do, daemon=True).start()
