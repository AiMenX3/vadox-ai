from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QTabWidget, QWidget,
    QCheckBox, QSlider, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from vadox.core import settings, memory

BG      = "#050d1a"
BG_CARD = "#071525"
BORDER  = "#0a2540"
CYAN    = "#00c8ff"
CYAN_D  = "#0a4a6a"
GREEN   = "#00ff88"
PINK    = "#ff00aa"
AMBER   = "#ffaa00"
RED     = "#ff3333"
TEXT    = "#5ab4d8"
TEXT_D  = "#0a3a5a"
TEXTD   = "#3a8aaa"  # Alias für Smart Home Tab


def _lbl(text, size=11, color=CYAN, bold=False):
    l = QLabel(text)
    l.setStyleSheet(f"color:{color}; font-size:{size}px; font-weight:{'600' if bold else '400'}; background:transparent;")
    l.setFont(QFont("Courier New", size))
    return l


def _sep():
    f = QFrame()
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{BORDER};")
    return f


class SettingsPanel(QDialog):
    settings_saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VADOX — Einstellungen")
        self.setMinimumSize(600, 520)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{ background:{BG}; }}
            QTabWidget::pane {{ border:1px solid {BORDER}; background:{BG_CARD}; border-radius:8px; }}
            QTabBar::tab {{
                background:{BG}; color:{CYAN_D}; font-family:'Courier New';
                font-size:10px; letter-spacing:1px; padding:8px 16px;
                border:1px solid {BORDER}; border-bottom:none;
                border-top-left-radius:6px; border-top-right-radius:6px;
            }}
            QTabBar::tab:selected {{ background:{BG_CARD}; color:{CYAN}; border-bottom:1px solid {BG_CARD}; }}
            QComboBox {{
                background:{BG}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:11px; padding:6px 10px;
                border-radius:6px;
            }}
            QComboBox::drop-down {{ border:none; }}
            QComboBox QAbstractItemView {{
                background:{BG_CARD}; color:{CYAN}; border:1px solid {BORDER};
                selection-background-color:{CYAN_D};
            }}
            QCheckBox {{ color:{TEXT}; font-family:'Courier New'; font-size:11px; background:transparent; }}
            QCheckBox::indicator {{ width:16px; height:16px; border:1px solid {BORDER}; border-radius:3px; background:{BG}; }}
            QCheckBox::indicator:checked {{ background:{CYAN}; }}
        """)
        self._cfg = settings.load()
        self._build()

    def _input(self, placeholder="", echo_password=False, value="") -> QLineEdit:
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setText(value)
        inp.setFixedHeight(36)
        if echo_password:
            inp.setEchoMode(QLineEdit.EchoMode.Password)
        inp.setStyleSheet(f"""
            QLineEdit {{
                background:{BG}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:11px;
                border-radius:6px; padding:0 10px;
            }}
            QLineEdit:focus {{ border:1px solid {CYAN}; }}
        """)
        return inp

    def _section(self, title: str) -> QLabel:
        l = _lbl(title, size=9, color=TEXT_D)
        l.setContentsMargins(0, 12, 0, 4)
        return l

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Titelleiste
        bar = QFrame()
        bar.setFixedHeight(50)
        bar.setStyleSheet(f"background:#060e1f; border-bottom:1px solid {BORDER};")
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(20, 0, 20, 0)
        bar_lay.addWidget(_lbl("VADOX — EINSTELLUNGEN", size=13, bold=True, color=CYAN))
        bar_lay.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"background:transparent; color:{TEXT_D}; font-size:14px; border:none;")
        close_btn.clicked.connect(self.reject)
        bar_lay.addWidget(close_btn)
        outer.addWidget(bar)

        tabs = QTabWidget()
        tabs.setContentsMargins(16, 16, 16, 16)
        outer.addWidget(tabs, stretch=1)

        tabs.addTab(self._tab_ai(),         "KI-MODELL")
        tabs.addTab(self._tab_voice(),      "STIMME")
        tabs.addTab(self._tab_email(),      "E-MAIL")
        tabs.addTab(self._tab_calendar(),   "KALENDER")
        tabs.addTab(self._tab_smarthome(),  "SMART HOME")
        tabs.addTab(self._tab_telegram(),   "TELEGRAM")
        tabs.addTab(self._tab_profile(),    "PROFIL")
        tabs.addTab(self._tab_about(),      "ÜBER VADOX")

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(20, 12, 20, 16)
        btn_row.setSpacing(10)

        reset_btn = QPushButton("Zurücksetzen")
        reset_btn.setFixedHeight(38)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:1px solid {BORDER};
                color:{TEXT_D}; font-family:'Courier New'; font-size:10px;
                border-radius:8px; padding:0 20px;
            }}
            QPushButton:hover {{ border-color:{PINK}; color:{PINK}; }}
        """)
        reset_btn.clicked.connect(self._reset)

        save_btn = QPushButton("SPEICHERN  ✓")
        save_btn.setFixedHeight(38)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background:#003a1a; border:1px solid #005a2a;
                color:{GREEN}; font-family:'Courier New'; font-size:11px;
                border-radius:8px; padding:0 24px; letter-spacing:1px;
            }}
            QPushButton:hover {{ background:#004a22; }}
        """)
        save_btn.clicked.connect(self._save)

        btn_row.addStretch()
        btn_row.addWidget(reset_btn)
        btn_row.addWidget(save_btn)
        outer.addLayout(btn_row)

    # ── Tab: KI-Modell ────────────────────────────────────────────────────────
    def _tab_ai(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(6)

        lay.addWidget(self._section("KI-ANBIETER"))
        self._provider_combo = QComboBox()
        providers = [
            ("Claude (Anthropic) — Empfohlen", "claude"),
            ("GPT-4o (OpenAI)", "openai"),
            ("Gemini (Google)", "gemini"),
            ("OpenRouter — 200+ Modelle mit 1 Key", "openrouter"),
            ("Ollama — Lokal & kostenlos (kein Internet)", "ollama"),
        ]
        for label, val in providers:
            self._provider_combo.addItem(label, val)

        saved_provider = self._cfg.get("provider", "claude")
        for i in range(self._provider_combo.count()):
            if self._provider_combo.itemData(i) == saved_provider:
                self._provider_combo.setCurrentIndex(i)
                break
        self._provider_combo.currentIndexChanged.connect(self._on_provider_change)
        lay.addWidget(self._provider_combo)

        lay.addWidget(self._section("API-KEY"))
        self._api_key_input = self._input("sk-ant-... / sk-... / AIza...", echo_password=True,
                                          value=self._cfg.get("api_key", ""))
        lay.addWidget(self._api_key_input)

        api_hint = _lbl("Der Key wird verschlüsselt gespeichert und nie übertragen.", size=9, color=TEXT_D)
        lay.addWidget(api_hint)

        lay.addWidget(self._section("MODELL"))
        self._model_combo = QComboBox()
        self._fill_models(self._cfg.get("provider", "claude"))
        lay.addWidget(self._model_combo)

        self._model_hint = _lbl("claude-sonnet-5 = beste Balance aus Geschwindigkeit und Qualität.", size=9, color=TEXT_D)
        self._model_hint.setWordWrap(True)
        lay.addWidget(self._model_hint)

        lay.addWidget(_sep())

        lay.addWidget(self._section("PEXELS API-KEY (für Präsentations-Bilder)"))
        self._pexels_key_input = self._input("Pexels API-Key eintragen", echo_password=True,
                                              value=self._cfg.get("pexels_api_key", ""))
        lay.addWidget(self._pexels_key_input)
        pexels_hint = _lbl("Kostenlos unter pexels.com/api registrieren — für Bilder in Präsentationen.", size=9, color=TEXT_D)
        pexels_hint.setWordWrap(True)
        lay.addWidget(pexels_hint)

        lay.addWidget(_sep())

        lay.addWidget(self._section("PICOVOICE KEY (für 'Hey Vadox' Wake-Word)"))
        self._picovoice_key_input = self._input("Picovoice Access Key eintragen", echo_password=True,
                                                 value=self._cfg.get("picovoice_key", ""))
        lay.addWidget(self._picovoice_key_input)
        pico_hint = _lbl("Kostenlos auf console.picovoice.ai — aktiviert 'Hey Vadox' ohne Knopfdruck.", size=9, color=TEXT_D)
        pico_hint.setWordWrap(True)
        lay.addWidget(pico_hint)

        lay.addWidget(_sep())

        # Provider Status
        status_row = QHBoxLayout()
        status_row.addWidget(_lbl("Status:", size=10, color=TEXT_D))
        self._status_lbl = _lbl("Nicht getestet", size=10, color=AMBER)
        status_row.addWidget(self._status_lbl)
        status_row.addStretch()
        test_btn = QPushButton("Verbindung testen")
        test_btn.setFixedHeight(32)
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background:{BG}; border:1px solid {BORDER}; color:{CYAN_D};
                font-family:'Courier New'; font-size:10px; border-radius:6px; padding:0 14px;
            }}
            QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
        """)
        test_btn.clicked.connect(self._test_connection)
        status_row.addWidget(test_btn)
        lay.addLayout(status_row)

        lay.addStretch()
        return w

    def _fill_models(self, provider: str):
        self._model_combo.clear()
        models = {
            "claude": [
                ("Claude Sonnet 5 — Empfohlen", "claude-sonnet-5"),
                ("Claude Haiku 4.5 — Schnell & günstig", "claude-haiku-4-5"),
                ("Claude Opus 4.8 — Stärkstes Modell", "claude-opus-4-8"),
            ],
            "openai": [
                ("GPT-4o — Empfohlen", "gpt-4o"),
                ("GPT-4o Mini — Günstig", "gpt-4o-mini"),
                ("GPT-4 Turbo", "gpt-4-turbo"),
            ],
            "gemini": [
                ("Gemini 2.0 Flash — Empfohlen", "gemini-2.0-flash"),
                ("Gemini 1.5 Pro", "gemini-1.5-pro"),
                ("Gemini 1.5 Flash — Günstig", "gemini-1.5-flash"),
            ],
            "openrouter": [
                ("Claude Sonnet 4.5 (via OpenRouter)", "anthropic/claude-sonnet-4-5"),
                ("GPT-4o (via OpenRouter)", "openai/gpt-4o"),
                ("Gemini 2.0 Flash (via OpenRouter)", "google/gemini-2.0-flash-001"),
                ("Llama 3.3 70B — Kostenlos", "meta-llama/llama-3.3-70b-instruct:free"),
                ("DeepSeek R1 — Günstig & stark", "deepseek/deepseek-r1"),
                ("Mistral Large", "mistralai/mistral-large"),
                ("Qwen 2.5 72B", "qwen/qwen-2.5-72b-instruct"),
            ],
            "ollama": [
                ("Llama 3.3 — Empfohlen (lokal)", "llama3.3"),
                ("Llama 3.1", "llama3.1"),
                ("Mistral", "mistral"),
                ("Gemma 3", "gemma3"),
                ("Phi-4 (Microsoft)", "phi4"),
                ("Qwen 2.5", "qwen2.5"),
                ("DeepSeek R1 (lokal)", "deepseek-r1"),
            ],
        }
        saved_model = self._cfg.get("model", "")
        for label, val in models.get(provider, []):
            self._model_combo.addItem(label, val)
        for i in range(self._model_combo.count()):
            if self._model_combo.itemData(i) == saved_model:
                self._model_combo.setCurrentIndex(i)
                break

        # Hinweis-Text für OpenRouter/Ollama aktualisieren
        if hasattr(self, "_model_hint"):
            hints = {
                "openrouter": "openrouter.ai — Ein API-Key, 200+ Modelle. Kostenlose Modelle verfügbar.",
                "ollama":     "ollama.ai installieren → 'ollama pull llama3.3' → läuft ohne Internet.",
                "claude":     "claude-sonnet-5 = beste Balance aus Geschwindigkeit und Qualität.",
                "openai":     "gpt-4o = Empfohlen. gpt-4o-mini = günstiger.",
                "gemini":     "gemini-2.0-flash = schnell und günstig.",
            }
            self._model_hint.setText(hints.get(provider, ""))

    def _on_provider_change(self, _):
        provider = self._provider_combo.currentData()
        self._fill_models(provider)
        self._status_lbl.setText("Nicht getestet")
        self._status_lbl.setStyleSheet(f"color:{AMBER}; font-size:10px; background:transparent;")

        # Placeholder-Text für API-Key je Provider
        placeholders = {
            "claude":      "sk-ant-...",
            "openai":      "sk-...",
            "gemini":      "AIza...",
            "openrouter":  "sk-or-... (openrouter.ai → Keys)",
            "ollama":      "Kein Key nötig — läuft lokal",
        }
        self._api_key_input.setPlaceholderText(placeholders.get(provider, "API-Key"))
        if provider == "ollama":
            self._api_key_input.setEnabled(False)
            self._api_key_input.setText("")
        else:
            self._api_key_input.setEnabled(True)

    def _test_connection(self):
        provider = self._provider_combo.currentData()
        key = self._api_key_input.text().strip()
        model = self._model_combo.currentData() or ""
        if not key:
            self._status_lbl.setText("Kein API-Key eingegeben")
            self._status_lbl.setStyleSheet(f"color:{PINK}; font-size:10px; background:transparent;")
            return
        self._status_lbl.setText("Teste...")
        self._status_lbl.setStyleSheet(f"color:{AMBER}; font-size:10px; background:transparent;")

        import threading
        def _test():
            ok, msg = self._do_test(provider, key, model)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._on_test_done(ok, msg))
        threading.Thread(target=_test, daemon=True).start()

    def _do_test(self, provider, key, model) -> tuple[bool, str]:
        try:
            if provider == "claude":
                from anthropic import Anthropic
                c = Anthropic(api_key=key)
                c.messages.create(model=model, max_tokens=10,
                                  messages=[{"role": "user", "content": "Hi"}])
                return True, "Verbunden"
            elif provider in ("openai", "openrouter", "ollama"):
                from vadox.core.ai_engine import _make_openai_client
                c = _make_openai_client(provider, key)
                # Ollama: einfachen Ping versuchen
                if provider == "ollama":
                    import requests
                    r = requests.get("http://localhost:11434/api/tags", timeout=4)
                    models_list = [m["name"] for m in r.json().get("models", [])]
                    if models_list:
                        return True, f"Verbunden — {len(models_list)} Modelle: {', '.join(models_list[:3])}"
                    return True, "Ollama läuft — noch kein Modell installiert (ollama pull llama3.3)"
                r = c.chat.completions.create(
                    model=model, max_tokens=10,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                return True, "Verbunden"
            elif provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=key)
                m = genai.GenerativeModel(model)
                m.generate_content("Hi")
                return True, "Verbunden"
        except Exception as e:
            err = str(e)
            if provider == "ollama" and "connection" in err.lower():
                return False, "Ollama nicht gestartet — bitte 'ollama serve' ausführen"
            return False, err[:80]

    def _on_test_done(self, ok: bool, msg: str):
        color = GREEN if ok else PINK
        self._status_lbl.setText(f"{'✓' if ok else '✗'} {msg}")
        self._status_lbl.setStyleSheet(f"color:{color}; font-size:10px; background:transparent;")

    # ── Tab: Stimme ───────────────────────────────────────────────────────────
    def _tab_voice(self) -> QWidget:
        from PyQt6.QtWidgets import QScrollArea
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border:none; background:transparent; }"
            "QScrollBar:vertical { width:4px; background:#040b18; }"
            "QScrollBar::handle:vertical { background:#0a3a5a; border-radius:2px; }"
        )
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(6)

        lay.addWidget(self._section("SPRACH-AUSGABE (TTS)"))
        self._tts_check = QCheckBox("Vadox spricht Antworten laut aus")
        self._tts_check.setChecked(self._cfg.get("tts_enabled", True))
        lay.addWidget(self._tts_check)

        lay.addWidget(self._section("STIMME AUSWÄHLEN"))
        self._voice_combo = QComboBox()
        voices = [
            ("Katja — Deutsch (weiblich, klar)", "de-DE-KatjaNeural"),
            ("Conrad — Deutsch (männlich)", "de-DE-ConradNeural"),
            ("Amala — Deutsch (weiblich, warm)", "de-DE-AmalaNeural"),
            ("Bernd — Deutsch (männlich, tief)", "de-DE-BerndNeural"),
            ("Elke — Deutsch (weiblich)", "de-DE-ElkeNeural"),
        ]
        saved_voice = self._cfg.get("voice", "de-DE-KatjaNeural")
        for label, val in voices:
            self._voice_combo.addItem(label, val)
            if val == saved_voice:
                self._voice_combo.setCurrentIndex(self._voice_combo.count() - 1)
        lay.addWidget(self._voice_combo)

        test_voice_btn = QPushButton("Stimme testen")
        test_voice_btn.setFixedHeight(32)
        test_voice_btn.setStyleSheet(f"""
            QPushButton {{
                background:{BG}; border:1px solid {BORDER}; color:{CYAN_D};
                font-family:'Courier New'; font-size:10px; border-radius:6px;
                padding:0 14px; margin-top:8px;
            }}
            QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
        """)
        test_voice_btn.clicked.connect(self._test_voice)
        lay.addWidget(test_voice_btn)

        # ── ElevenLabs (JARVIS-Stimme) ────────────────────────────────────────
        lay.addWidget(_sep())
        lay.addWidget(self._section("ELEVENLABS — JARVIS-STIMME (optional)"))

        self._eleven_check = QCheckBox("ElevenLabs Stimme aktivieren (überschreibt kostenlose Stimme)")
        self._eleven_check.setChecked(self._cfg.get("elevenlabs_enabled", False))
        self._eleven_check.setStyleSheet(f"color:{TEXT}; font-size:10px;")
        lay.addWidget(self._eleven_check)

        self._eleven_key_input = self._input(
            "ElevenLabs API-Key (elevenlabs.io → Account → API Keys)",
            echo_password=True,
            value=self._cfg.get("elevenlabs_api_key", "")
        )
        lay.addWidget(self._eleven_key_input)

        lay.addWidget(self._section("STIMME AUSWÄHLEN"))

        # Bekannte Stimmen + Eigene
        self._eleven_voice_combo = QComboBox()
        ELEVEN_VOICES = [
            ("--- Eigene Voice ID eintragen ---", "__custom__"),
            # Männlich (ideal für JARVIS)
            ("Daniel — Tief, ruhig, professionell (EN)", "onwK4e9ZLuTAKqWW03F9"),
            ("Antoni — Klar, selbstbewusst (EN)",         "ErXwobaYiN019PkySvjV"),
            ("Josh — Warm, freundlich (EN)",               "TxGEqnHWrfWFTfGW9XjX"),
            ("Arnold — Kraftvoll, dramatisch (EN)",        "VR6AewLTigWG4xSOukaG"),
            ("Florian — Deutsch, tief (DE)",               "AZnzlk1XvdvUeBnXmlld"),
            # Weiblich
            ("Rachel — Klar, neutral (EN)",                "21m00Tcm4TlvDq8ikWAM"),
            ("Bella — Sanft, warm (EN)",                   "EXAVITQu4vr4xnSDxMaL"),
            ("Vadox Standard (JARVIS-Stil)",               "W2KR2ct3bRh7HcawFJB4"),
        ]
        saved_vid = self._cfg.get("elevenlabs_voice_id", "W2KR2ct3bRh7HcawFJB4")
        found = False
        for label, vid in ELEVEN_VOICES:
            self._eleven_voice_combo.addItem(label, vid)
            if vid == saved_vid:
                self._eleven_voice_combo.setCurrentIndex(self._eleven_voice_combo.count() - 1)
                found = True
        if not found:
            # War eine eigene ID — auf "__custom__" zeigen
            self._eleven_voice_combo.setCurrentIndex(0)

        self._eleven_voice_combo.setStyleSheet(f"""
            QComboBox {{ background:{BG}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:10px; padding:6px 10px; border-radius:6px; }}
            QComboBox::drop-down {{ border:none; }}
            QComboBox QAbstractItemView {{ background:{BG_CARD}; color:{CYAN};
                border:1px solid {BORDER}; selection-background-color:{CYAN_D}; }}
        """)
        self._eleven_voice_combo.currentIndexChanged.connect(self._on_eleven_voice_change)
        lay.addWidget(self._eleven_voice_combo)

        # Eigene Voice-ID Feld (nur bei "__custom__" sichtbar)
        self._eleven_custom_id = self._input(
            "Eigene Voice ID einkopieren (aus elevenlabs.io)",
            value=saved_vid if not found else ""
        )
        self._eleven_custom_id.setVisible(not found)
        lay.addWidget(self._eleven_custom_id)

        voice_id_hint = _lbl(
            "Eigene Stimme: elevenlabs.io → Voice Library → Stimme → ID kopieren",
            size=9, color=TEXT_D
        )
        voice_id_hint.setWordWrap(True)
        lay.addWidget(voice_id_hint)

        test_eleven_btn = QPushButton("ElevenLabs Stimme testen")
        test_eleven_btn.setFixedHeight(32)
        test_eleven_btn.setStyleSheet(f"""
            QPushButton {{
                background:#0a1e0a; border:1px solid #00ff8844; color:#00cc66;
                font-family:'Courier New'; font-size:10px; border-radius:6px; padding:0 14px; margin-top:4px;
            }}
            QPushButton:hover {{ border-color:#00ff88; color:#00ff88; }}
        """)
        test_eleven_btn.clicked.connect(self._test_elevenlabs)
        lay.addWidget(test_eleven_btn)

        lay.addWidget(_sep())
        lay.addWidget(_sep())
        lay.addWidget(self._section("SPRACH-EINGABE (STT)"))
        self._stt_check = QCheckBox("Mikrofon-Eingabe aktiviert")
        self._stt_check.setChecked(self._cfg.get("stt_enabled", True))
        lay.addWidget(self._stt_check)

        lay.addWidget(self._section("SPRACHE ERKENNEN ALS"))
        self._lang_combo = QComboBox()
        langs = [("Deutsch", "de-DE"), ("Englisch", "en-US"), ("Türkisch", "tr-TR"),
                 ("Russisch", "ru-RU"), ("Arabisch", "ar-SA")]
        saved_lang = self._cfg.get("language", "de-DE")
        for label, val in langs:
            self._lang_combo.addItem(label, val)
            if val == saved_lang:
                self._lang_combo.setCurrentIndex(self._lang_combo.count() - 1)
        lay.addWidget(self._lang_combo)

        lay.addWidget(_sep())
        lay.addWidget(self._section("VADOX-SPRACHE (KI-Antworten & Oberfläche)"))
        self._ui_lang_combo = QComboBox()
        ui_langs = [
            ("Deutsch — Vadox antwortet auf Deutsch", "de"),
            ("English — Vadox responds in English",   "en"),
        ]
        saved_ui_lang = self._cfg.get("ui_language", "de")
        for label, val in ui_langs:
            self._ui_lang_combo.addItem(label, val)
            if val == saved_ui_lang:
                self._ui_lang_combo.setCurrentIndex(self._ui_lang_combo.count() - 1)
        lay.addWidget(self._ui_lang_combo)
        lang_hint = _lbl(
            "Wechsel wirkt sofort — Vadox antwortet dann in der gewählten Sprache.",
            size=9, color=TEXT_D
        )
        lang_hint.setWordWrap(True)
        lay.addWidget(lang_hint)

        lay.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return w

    def _tab_email(self) -> QWidget:
        from PyQt6.QtWidgets import QScrollArea, QTextBrowser
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Innerer Scroll-Bereich
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; } QScrollBar:vertical { width:4px; background:#040b18; } QScrollBar::handle:vertical { background:#0a3a5a; border-radius:2px; }")
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(6)

        # ── Anbieter ─────────────────────────────────────────────────────────
        lay.addWidget(self._section("E-MAIL ANBIETER"))
        self._email_provider = QComboBox()
        providers = [
            ("Gmail (Google) — App-Passwort", "gmail"),
            ("Outlook / Hotmail privat — App-Passwort", "outlook"),
            ("Outlook Exchange (Firma / Unternehmen)", "exchange"),
            ("Yahoo Mail — App-Passwort", "yahoo"),
            ("Web.de — normales Passwort möglich", "web.de"),
            ("GMX — normales Passwort möglich", "gmx"),
            ("T-Online — normales Passwort möglich", "t-online"),
        ]
        saved_prov = self._cfg.get("email_provider", "gmail")
        for label, val in providers:
            self._email_provider.addItem(label, val)
            if val == saved_prov:
                self._email_provider.setCurrentIndex(self._email_provider.count() - 1)
        lay.addWidget(self._email_provider)

        # ── E-Mail Adresse ────────────────────────────────────────────────────
        lay.addWidget(self._section("E-MAIL ADRESSE"))
        self._email_addr = self._input("name@firma.de", value=self._cfg.get("email_address", ""))
        lay.addWidget(self._email_addr)

        # ── Exchange: OAuth-Login (Office 365) ────────────────────────────────
        self._ms_oauth_frame = QFrame()
        self._ms_oauth_frame.setStyleSheet(
            "QFrame{background:#071a2e; border:1px solid #0a3060; border-radius:8px;}"
        )
        ms_lay = QVBoxLayout(self._ms_oauth_frame)
        ms_lay.setContentsMargins(12, 10, 12, 10)
        ms_lay.setSpacing(6)

        ms_title = _lbl("MICROSOFT / OFFICE 365 LOGIN", size=10, color=CYAN, bold=True)
        ms_lay.addWidget(ms_title)

        ms_info = QLabel(
            "Office 365 erlaubt kein Passwort-Login mehr (seit 2022).\n"
            "Klicke 'Microsoft Login' — der Browser öffnet sich, du loggst dich einmal ein.\n"
            "Danach funktioniert alles automatisch."
        )
        ms_info.setWordWrap(True)
        ms_info.setStyleSheet(f"color:#7acce0; font-size:10px; background:transparent;")
        ms_lay.addWidget(ms_info)

        # Client-ID Feld (optional — für eigene Azure App)
        client_id_row = QHBoxLayout()
        client_id_lbl = _lbl("Azure Client-ID:", size=9, color=TEXT)
        client_id_lbl.setFixedWidth(110)
        self._ms_client_id = self._input(
            "Leer lassen für Standard-App",
            value=self._cfg.get("ms_client_id", "")
        )
        self._ms_client_id.setFixedHeight(26)
        client_id_row.addWidget(client_id_lbl)
        client_id_row.addWidget(self._ms_client_id)
        ms_lay.addLayout(client_id_row)

        # Login-Button + Status
        login_row = QHBoxLayout()
        self._ms_login_btn = QPushButton("⚡ Microsoft Login")
        self._ms_login_btn.setFixedHeight(34)
        self._ms_login_btn.setStyleSheet(f"""
            QPushButton {{
                background:#0052cc; border:none; color:#ffffff;
                font-family:'Courier New'; font-size:11px; font-weight:bold;
                border-radius:6px; padding:0 18px;
            }}
            QPushButton:hover {{ background:#0066ff; }}
            QPushButton:pressed {{ background:#003d99; }}
        """)
        self._ms_login_btn.clicked.connect(self._ms_oauth_login)

        self._ms_logout_btn = QPushButton("Logout")
        self._ms_logout_btn.setFixedHeight(34)
        self._ms_logout_btn.setFixedWidth(70)
        self._ms_logout_btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:1px solid #3a3a5a; color:#7acce0;
                font-family:'Courier New'; font-size:9px; border-radius:6px;
            }}
            QPushButton:hover {{ border-color:{PINK}; color:{PINK}; }}
        """)
        self._ms_logout_btn.clicked.connect(self._ms_oauth_logout)

        login_row.addWidget(self._ms_login_btn)
        login_row.addWidget(self._ms_logout_btn)
        login_row.addStretch()
        ms_lay.addLayout(login_row)

        self._ms_login_status = QLabel("")
        self._ms_login_status.setWordWrap(True)
        self._ms_login_status.setStyleSheet(f"color:{AMBER}; font-size:10px; background:transparent;")
        ms_lay.addWidget(self._ms_login_status)

        lay.addWidget(self._ms_oauth_frame)

        # Login-Status initial setzen
        from vadox.tools.email_oauth import is_logged_in
        if is_logged_in():
            self._ms_login_status.setText("✓ Eingeloggt (Token vorhanden)")
            self._ms_login_status.setStyleSheet(f"color:{GREEN}; font-size:10px; background:transparent;")

        # ── Exchange: Domain + Server (Legacy-Fallback) ────────────────────────
        self._exchange_domain_lbl = self._section("WINDOWS-DOMÄNE (nur On-Premise Exchange)")
        lay.addWidget(self._exchange_domain_lbl)
        self._exchange_domain = self._input("z.B. FIRMA oder firma.local", value=self._cfg.get("exchange_domain", ""))
        lay.addWidget(self._exchange_domain)

        self._exchange_server_lbl = self._section("EXCHANGE SERVER (On-Premise, optional)")
        lay.addWidget(self._exchange_server_lbl)
        self._exchange_server = self._input("z.B. mail.firma.de (leer = automatisch)", value=self._cfg.get("exchange_server", ""))
        lay.addWidget(self._exchange_server)

        # ── Passwort ──────────────────────────────────────────────────────────
        self._pass_section_lbl = self._section("APP-PASSWORT")
        lay.addWidget(self._pass_section_lbl)
        self._email_pass = self._input("App-Passwort oder normales Passwort", echo_password=True,
                                       value=self._cfg.get("email_password", ""))
        lay.addWidget(self._email_pass)

        # ── Info-Box ──────────────────────────────────────────────────────────
        self._info_box = QFrame()
        self._info_box.setStyleSheet(f"background:#071525; border:1px solid #0a3060; border-radius:8px;")
        info_lay = QVBoxLayout(self._info_box)
        info_lay.setContentsMargins(12, 10, 12, 10)
        info_lay.setSpacing(4)
        self._info_title = _lbl("", size=10, color=CYAN, bold=True)
        self._info_text  = QLabel("")
        self._info_text.setWordWrap(True)
        self._info_text.setStyleSheet(f"color:{TEXT}; font-size:10px; background:transparent; line-height:1.5;")
        info_lay.addWidget(self._info_title)
        info_lay.addWidget(self._info_text)

        self._guide_btn = QPushButton("")
        self._guide_btn.setFixedHeight(28)
        self._guide_btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:1px solid #0a3060;
                color:{CYAN_D}; font-family:'Courier New'; font-size:9px;
                border-radius:5px; margin-top:4px;
            }}
            QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
        """)
        self._guide_btn.clicked.connect(self._open_guide)
        info_lay.addWidget(self._guide_btn)
        lay.addWidget(self._info_box)

        # ── Test + Status ─────────────────────────────────────────────────────
        lay.addWidget(_sep())
        test_row = QHBoxLayout()
        self._email_status = _lbl("Nicht getestet", size=10, color=AMBER)
        self._email_status.setWordWrap(True)
        test_row.addWidget(self._email_status, stretch=1)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)

        test_email_btn = QPushButton("Verbindung testen")
        test_email_btn.setFixedHeight(30)
        test_email_btn.setStyleSheet(f"""
            QPushButton {{
                background:{BG}; border:1px solid {BORDER}; color:{CYAN_D};
                font-family:'Courier New'; font-size:10px; border-radius:6px; padding:0 14px;
            }}
            QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
        """)
        test_email_btn.clicked.connect(self._test_email)

        diag_btn = QPushButton("🔍 Diagnose (Details)")
        diag_btn.setFixedHeight(30)
        diag_btn.setStyleSheet(f"""
            QPushButton {{
                background:{BG}; border:1px solid #1a4a6a; color:#5ab4d8;
                font-family:'Courier New'; font-size:10px; border-radius:6px; padding:0 14px;
            }}
            QPushButton:hover {{ border-color:#00c8ff; color:#00c8ff; }}
        """)
        diag_btn.clicked.connect(self._diagnose_exchange)

        btn_col.addWidget(test_email_btn)
        btn_col.addWidget(diag_btn)
        test_row.addLayout(btn_col)
        lay.addLayout(test_row)
        lay.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll)

        # Signal NACH Widget-Erstellung verbinden
        self._email_provider.currentIndexChanged.connect(self._on_email_provider_change)
        # Initial-Anzeige setzen
        self._on_email_provider_change(0)
        return w

    def _on_email_provider_change(self, _=0):
        prov = self._email_provider.currentData() if self._email_provider.count() else "gmail"

        is_exchange = prov == "exchange"
        needs_app   = prov in ("gmail", "outlook", "yahoo")
        normal_ok   = prov in ("web.de", "gmx", "t-online")

        # Exchange-Felder: nur bei Exchange anzeigen
        for w in [self._ms_oauth_frame,
                  self._exchange_domain_lbl, self._exchange_domain,
                  self._exchange_server_lbl, self._exchange_server]:
            w.setVisible(prov == "exchange")

        if prov == "exchange":
            self._pass_section_lbl.setText("FIRMEN-PASSWORT (normales Windows-Passwort)")
            title = "Exchange Firmenkonto"
            text  = ("Vadox probiert automatisch mehrere Verbindungsmethoden.\n\n"
                     "Pflichtfelder:\n"
                     "• Firmen-E-Mail-Adresse (z.B. max@firma.de)\n"
                     "• Normales Windows-/Firmen-Passwort\n\n"
                     "Falls die Verbindung fehlschlägt:\n"
                     "• Exchange Server eintragen (z.B. mail.firma.de)\n"
                     "• Windows-Domäne eintragen (z.B. FIRMA oder firma.local)\n"
                     "• Prüfen ob VPN aktiv sein muss\n\n"
                     "Vadox versucht automatisch: Autodiscover → EWS-URL → NTLM → ohne SSL-Prüfung")
            btn = ""
        elif prov == "gmail":
            self._pass_section_lbl.setText("APP-PASSWORT (kein normales Passwort)")
            title = "Gmail: So erstellst du ein App-Passwort"
            text  = ("1. Öffne: myaccount.google.com\n"
                     "2. Sicherheit → 2-Schritt-Verifizierung aktivieren\n"
                     "3. Sicherheit → App-Passwörter (ganz unten)\n"
                     "4. App wählen: Mail | Gerät: Windows\n"
                     "5. Den 16-stelligen Code kopieren und hier einfügen\n"
                     "Warum? Google blockiert normale Passwörter bei IMAP seit 2024.")
            btn = "Gmail App-Passwort erstellen öffnen"
        elif prov == "outlook":
            self._pass_section_lbl.setText("APP-PASSWORT (kein normales Passwort)")
            title = "Outlook / Hotmail: App-Passwort erstellen"
            text  = ("1. Öffne: account.live.com/proofs\n"
                     "2. Sicherheit → Erweiterte Sicherheitsoptionen\n"
                     "3. App-Kennwörter → Neues App-Kennwort erstellen\n"
                     "4. Den generierten Code kopieren und hier einfügen\n"
                     "Warum? Microsoft blockiert normale Passwörter bei IMAP.")
            btn = "Outlook App-Passwort erstellen öffnen"
        elif prov == "yahoo":
            self._pass_section_lbl.setText("APP-PASSWORT (kein normales Passwort)")
            title = "Yahoo: App-Passwort erstellen"
            text  = ("1. Öffne: login.yahoo.com → Kontoinfo\n"
                     "2. Sicherheit → App-Passwörter generieren\n"
                     "3. Den Code kopieren und hier einfügen\n"
                     "Warum? Yahoo blockiert normale Passwörter bei IMAP.")
            btn = "Yahoo Sicherheit öffnen"
        else:
            self._pass_section_lbl.setText("PASSWORT")
            title = f"{prov.upper()}: Normales Passwort möglich"
            text  = ("Bei diesem Anbieter kannst du dein normales E-Mail-Passwort verwenden.\n"
                     "Einfach E-Mail-Adresse und dein bekanntes Passwort eingeben.")
            btn = ""

        self._info_title.setText(title)
        self._info_text.setText(text)
        self._guide_btn.setText(btn)
        self._guide_btn.setVisible(bool(btn) and prov not in ("web.de", "gmx", "t-online", "exchange"))
        self._guide_url = {
            "gmail":   "https://myaccount.google.com/apppasswords",
            "outlook": "https://account.live.com/proofs/manage/additional",
            "yahoo":   "https://login.yahoo.com/account/security",
        }.get(prov, "")

    def _ms_oauth_login(self):
        from PyQt6.QtWidgets import QMessageBox
        from vadox.core import settings as _s

        # Client-ID speichern falls eingetragen
        client_id = self._ms_client_id.text().strip()
        cfg = _s.load()

        if client_id:
            cfg["ms_client_id"] = client_id
        _s.save(cfg)

        # Schritt 1: Device Flow starten (schnell, im Main-Thread)
        import msal, webbrowser, threading
        from PyQt6.QtWidgets import QMessageBox

        self._ms_login_status.setText("⏳ Verbinde mit Microsoft...")
        self._ms_login_status.setStyleSheet(f"color:{AMBER}; font-size:10px; background:transparent;")
        self._ms_login_status.repaint()
        self._ms_login_btn.setEnabled(False)
        self._ms_login_btn.repaint()

        try:
            from vadox.tools.email_oauth import _DEFAULT_CLIENT_ID, _TENANT_ID, _SCOPES, _TOKEN_CACHE_FILE
            import json

            cache_obj = msal.SerializableTokenCache()
            if _TOKEN_CACHE_FILE.exists():
                try:
                    cache_obj.deserialize(_TOKEN_CACHE_FILE.read_text(encoding="utf-8"))
                except Exception:
                    pass

            msal_app = msal.PublicClientApplication(
                client_id=_DEFAULT_CLIENT_ID,
                authority=f"https://login.microsoftonline.com/{_TENANT_ID}",
                token_cache=cache_obj,
            )
            flow = msal_app.initiate_device_flow(scopes=_SCOPES)
        except Exception as e:
            self._ms_login_btn.setEnabled(True)
            self._ms_login_btn.setText("⚡ Microsoft Login")
            QMessageBox.critical(self, "Fehler", f"Verbindung zu Microsoft fehlgeschlagen:\n{e}")
            return

        if "user_code" not in flow:
            self._ms_login_btn.setEnabled(True)
            self._ms_login_btn.setText("⚡ Microsoft Login")
            QMessageBox.critical(self, "Fehler", f"Kein Code erhalten:\n{flow.get('error_description','?')}")
            return

        code = flow["user_code"]
        url  = flow["verification_uri"]

        # Schritt 2: Code anzeigen + Browser öffnen (im Main-Thread — 100% sichtbar)
        self._ms_login_status.setText(f"Code: {code}  |  Webseite: {url}")
        self._ms_login_status.setStyleSheet(
            "color:#ffffff; font-size:12px; font-weight:bold; background:#0a2a4a;"
            "border:1px solid #00c8ff; border-radius:6px; padding:6px;"
        )
        self._ms_login_btn.setText("⏳ Warte auf Login im Browser...")
        self._ms_login_status.repaint()

        QMessageBox.information(
            self,
            "Microsoft Login — Code eingeben",
            f"1. Browser öffnet sich gleich automatisch\n"
            f"2. Gib diesen Code ein:\n\n"
            f"        {code}\n\n"
            f"3. Mit deiner Firmen-E-Mail einloggen\n\n"
            f"Webseite (falls Browser nicht öffnet):\n{url}",
        )
        webbrowser.open(url)

        # Schritt 3: Im Hintergrund auf Login warten
        from PyQt6.QtCore import QTimer

        def _wait_for_login():
            try:
                result = msal_app.acquire_token_by_device_flow(flow)
                if "access_token" in result:
                    # Token speichern
                    _TOKEN_CACHE_FILE.write_text(
                        cache_obj.serialize(), encoding="utf-8"
                    )
                    def _ok():
                        self._ms_login_btn.setEnabled(True)
                        self._ms_login_btn.setText("⚡ Microsoft Login")
                        self._ms_login_status.setText("✓ Erfolgreich eingeloggt!")
                        self._ms_login_status.setStyleSheet(f"color:{GREEN}; font-size:11px; background:transparent;")
                    QTimer.singleShot(0, _ok)
                else:
                    err = result.get("error_description", str(result))[:200]
                    def _fail():
                        self._ms_login_btn.setEnabled(True)
                        self._ms_login_btn.setText("⚡ Microsoft Login")
                        self._ms_login_status.setText(f"✗ {err}")
                        self._ms_login_status.setStyleSheet(f"color:{PINK}; font-size:10px; background:transparent;")
                    QTimer.singleShot(0, _fail)
            except Exception as ex:
                def _err():
                    self._ms_login_btn.setEnabled(True)
                    self._ms_login_btn.setText("⚡ Microsoft Login")
                    self._ms_login_status.setText(f"✗ {ex}")
                    self._ms_login_status.setStyleSheet(f"color:{PINK}; font-size:10px; background:transparent;")
                QTimer.singleShot(0, _err)

        threading.Thread(target=_wait_for_login, daemon=True).start()

    def _ms_oauth_logout(self):
        from vadox.tools.email_oauth import logout
        logout()
        self._ms_login_status.setText("Ausgeloggt.")
        self._ms_login_status.setStyleSheet(f"color:{AMBER}; font-size:10px; background:transparent;")

    def _open_guide(self):
        if self._guide_url:
            import webbrowser
            webbrowser.open(self._guide_url)

    def _test_email(self):
        from PyQt6.QtWidgets import QMessageBox
        try:
            addr = self._email_addr.text().strip()
            pwd  = self._email_pass.text().strip()
            prov = self._email_provider.currentData()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Felder nicht lesbar:\n{e}")
            return

        if not addr or not pwd:
            self._email_status.setText("Bitte E-Mail und Passwort eingeben")
            self._email_status.setStyleSheet(f"color:{PINK}; font-size:10px; background:transparent;")
            return

        self._email_status.setText("⏳ Teste Verbindung...")
        self._email_status.setStyleSheet(f"color:{AMBER}; font-size:11px; background:transparent;")
        self._email_status.repaint()

        domain = self._exchange_domain.text().strip() if prov == "exchange" else ""
        server = self._exchange_server.text().strip() if prov == "exchange" else ""

        import threading
        def _test():
            try:
                ok, msg = self._do_email_test(prov, addr, pwd, domain, server)
            except Exception as ex:
                ok, msg = False, f"Unerwarteter Fehler: {ex}"
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._on_email_test(ok, msg))
        t = threading.Thread(target=_test, daemon=True)
        t.start()

    def _do_email_test(self, prov, addr, pwd, domain="", server="") -> tuple[bool, str]:
        try:
            if prov == "exchange":
                import socket
                socket.setdefaulttimeout(25)
                # Zugangsdaten temporär in Settings schreiben für _exchange_connect()
                from vadox.core import settings as _s
                cfg_tmp = _s.load()
                cfg_tmp["email_address"]   = addr
                cfg_tmp["email_password"]  = pwd
                cfg_tmp["exchange_domain"] = domain
                cfg_tmp["exchange_server"] = server
                _s.save(cfg_tmp)
                from vadox.tools.email_tool import _exchange_connect
                mode, conn = _exchange_connect()
                if mode == "ews":
                    count = conn.inbox.total_count
                    return True, f"✓ Exchange (EWS) verbunden — {count} E-Mails im Posteingang"
                else:
                    _, ids = conn.search(None, "ALL")
                    count = len(ids[0].split()) if ids[0] else 0
                    conn.logout()
                    return True, f"✓ Exchange (IMAP) verbunden — {count} E-Mails gefunden"
            else:
                from vadox.tools.email_tool import PROVIDERS
                import imaplib
                cfg = PROVIDERS.get(prov, PROVIDERS["gmail"])
                mail = imaplib.IMAP4_SSL(cfg["imap"])
                mail.login(addr, pwd)
                mail.select("INBOX")
                _, data = mail.search(None, "ALL")
                count = len(data[0].split()) if data[0] else 0
                mail.logout()
                return True, f"✓ Verbindung erfolgreich — {count} E-Mails gefunden"
        except Exception as e:
            err = str(e)
            if "AUTHENTICATIONFAILED" in err or "Invalid credentials" in err or "Authentication" in err:
                return False, "✗ Falsches Passwort — bitte E-Mail + Passwort prüfen"
            if "timed out" in err.lower() or "timeout" in err.lower():
                return False, "✗ Timeout — Server nicht erreichbar. VPN aktiv? Exchange Server eintragen?"
            if "SSL" in err or "certificate" in err.lower():
                return False, "✗ SSL-Fehler — Vadox hat es trotzdem ohne SSL-Prüfung versucht"
            if "password" in err.lower() and "app" in err.lower():
                return False, "✗ App-Passwort nötig → account.microsoft.com → Sicherheit → App-Kennwörter"
            # Für Exchange: zeige ob IMAP oder EWS scheiterte
            if "IMAP" in err or "EWS" in err or "Verbindung fehlgeschlagen" in err:
                return False, f"✗ EWS + IMAP fehlgeschlagen.\nTipp: Exchange Server-URL eintragen (z.B. mail.firma.de)\nOder: VPN prüfen"
            return False, f"✗ {err[:120]}"

    def _diagnose_exchange(self):
        """Zeigt detaillierten Diagnose-Bericht für Exchange-Verbindung."""
        from PyQt6.QtWidgets import QMessageBox
        try:
            addr   = self._email_addr.text().strip()
            pwd    = self._email_pass.text().strip()
            server = self._exchange_server.text().strip()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Felder nicht lesbar:\n{e}")
            return

        if not addr:
            QMessageBox.warning(self, "Eingabe fehlt", "Bitte zuerst E-Mail-Adresse eingeben.")
            return

        self._email_status.setText("🔍 Diagnose läuft (30 Sek)...")
        self._email_status.setStyleSheet(f"color:{AMBER}; font-size:10px; background:transparent;")
        self._email_status.repaint()

        import threading
        def _run():
            try:
                report = self._run_exchange_diagnosis(addr, pwd, server)
            except Exception as ex:
                report = f"FEHLER beim Ausführen der Diagnose:\n{ex}"

            from PyQt6.QtCore import QTimer
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

            def _show():
                try:
                    dlg = QDialog(self)
                    dlg.setWindowTitle("Exchange Diagnose")
                    dlg.resize(660, 520)
                    dlg.setStyleSheet("background:#040b18; color:#5ab4d8;")
                    lay = QVBoxLayout(dlg)
                    txt = QTextEdit()
                    txt.setReadOnly(True)
                    txt.setPlainText(report)
                    txt.setStyleSheet(
                        "background:#060f1e; color:#c0e8ff; font-family:'Courier New';"
                        "font-size:11px; border:1px solid #0a2540; border-radius:6px;"
                    )
                    close_btn = QPushButton("Schließen")
                    close_btn.setStyleSheet(
                        "QPushButton{background:#071525;border:1px solid #0a2540;"
                        "color:#00c8ff;font-family:'Courier New';font-size:10px;"
                        "border-radius:6px;padding:6px 20px;}"
                    )
                    close_btn.clicked.connect(dlg.accept)
                    lay.addWidget(txt)
                    lay.addWidget(close_btn)
                    self._email_status.setText("Diagnose abgeschlossen.")
                    self._email_status.setStyleSheet(f"color:{AMBER}; font-size:10px; background:transparent;")
                    dlg.exec()
                except Exception as ex2:
                    QMessageBox.critical(self, "Diagnose-Fehler", str(ex2))

            QTimer.singleShot(0, _show)

        threading.Thread(target=_run, daemon=True).start()

    def _run_exchange_diagnosis(self, addr: str, pwd: str, server: str) -> str:
        import socket, ssl, imaplib, http.client, urllib.request
        lines = []
        ok  = "  ✓"
        err = "  ✗"
        warn = "  ⚠"

        email_domain = addr.split("@")[1] if "@" in addr else "?"
        lines.append("=" * 60)
        lines.append("VADOX EXCHANGE DIAGNOSE")
        lines.append("=" * 60)
        lines.append(f"E-Mail:  {addr}")
        lines.append(f"Domain:  {email_domain}")
        lines.append(f"Server:  {server or '(nicht eingetragen)'}")
        lines.append("")

        # ── Port-Tests ──────────────────────────────────────────
        lines.append("── PORT-ERREICHBARKEIT ──────────────────────")
        servers_to_check = []
        if server:
            servers_to_check.append(server)
        servers_to_check += [
            "outlook.office365.com",
            f"mail.{email_domain}",
            f"webmail.{email_domain}",
            f"owa.{email_domain}",
        ]

        reachable_443  = []
        reachable_993  = []
        reachable_587  = []

        for host in servers_to_check:
            for port, lst in [(443, reachable_443), (993, reachable_993), (587, reachable_587)]:
                try:
                    socket.setdefaulttimeout(5)
                    s = socket.create_connection((host, port))
                    s.close()
                    lst.append(host)
                    lines.append(f"{ok} {host}:{port} erreichbar")
                except Exception as e:
                    lines.append(f"{err} {host}:{port} — {type(e).__name__}: {e}")

        lines.append("")

        # ── IMAP-Test ───────────────────────────────────────────
        lines.append("── IMAP LOGIN-TEST (Port 993) ───────────────")
        if not reachable_993:
            lines.append(f"{warn} Kein IMAP-Server erreichbar (Port 993 überall gesperrt)")
            lines.append(f"     → Firma hat IMAP deaktiviert, nur EWS/ActiveSync erlaubt")
        else:
            for host in reachable_993:
                try:
                    socket.setdefaulttimeout(10)
                    mail = imaplib.IMAP4_SSL(host, 993)
                    mail.login(addr, pwd)
                    mail.select("INBOX")
                    _, ids = mail.search(None, "ALL")
                    count = len(ids[0].split()) if ids[0] else 0
                    mail.logout()
                    lines.append(f"{ok} IMAP LOGIN OK via {host} — {count} E-Mails")
                except imaplib.IMAP4.error as e:
                    if "AUTHENTICATIONFAILED" in str(e) or "Invalid" in str(e):
                        lines.append(f"{err} {host}: Login-Fehler — Falsches Passwort ODER Basic-Auth deaktiviert")
                        lines.append(f"     → Lösung: App-Passwort erstellen unter account.microsoft.com")
                    else:
                        lines.append(f"{err} {host}: {e}")
                except Exception as e:
                    lines.append(f"{err} {host}: {type(e).__name__}: {e}")

        lines.append("")

        # ── EWS HTTPS-Test ──────────────────────────────────────
        lines.append("── EWS HTTPS-TEST (Port 443) ────────────────")
        if not reachable_443:
            lines.append(f"{warn} Kein HTTPS-Server erreichbar")
        else:
            ews_paths = ["/EWS/Exchange.asmx", "/autodiscover/autodiscover.xml"]
            for host in reachable_443[:3]:
                for path in ews_paths:
                    try:
                        import ssl as ssl_mod
                        ctx = ssl_mod.create_default_context()
                        ctx.check_hostname = False
                        ctx.verify_mode = ssl_mod.CERT_NONE
                        conn = http.client.HTTPSConnection(host, 443, context=ctx, timeout=8)
                        conn.request("GET", path, headers={"User-Agent": "Vadox/1.0"})
                        resp = conn.getresponse()
                        conn.close()
                        status_map = {
                            200: "OK",
                            401: "401 Unauthorized (Server da, aber Auth nötig — gut!)",
                            403: "403 Forbidden (Zugriff gesperrt)",
                            404: "404 Nicht gefunden (EWS deaktiviert?)",
                            503: "503 Service Unavailable",
                        }
                        status_txt = status_map.get(resp.status, str(resp.status))
                        symbol = ok if resp.status in (200, 401) else warn if resp.status == 404 else err
                        lines.append(f"{symbol} {host}{path} → {status_txt}")
                    except Exception as e:
                        lines.append(f"{err} {host}{path} → {type(e).__name__}: {e}")

        lines.append("")

        # ── Empfehlung ──────────────────────────────────────────
        lines.append("── EMPFEHLUNG ───────────────────────────────")
        if not reachable_443 and not reachable_993:
            lines.append(f"{warn} ALLE Ports gesperrt!")
            lines.append("   → VPN aktivieren und nochmal probieren")
            lines.append("   → Oder: Firma erlaubt nur internes Netzwerk")
        elif not reachable_993:
            lines.append(f"{warn} IMAP (Port 993) gesperrt, aber HTTPS erreichbar")
            lines.append("   → EWS sollte funktionieren (wird automatisch versucht)")
            lines.append("   → Falls EWS auch fehlschlägt: Basic-Auth evtl. deaktiviert")
            lines.append("   → Lösung A: App-Passwort erstellen (account.microsoft.com)")
            lines.append("   → Lösung B: IT-Admin fragen IMAP oder EWS zu aktivieren")
        else:
            lines.append(f"{ok} Server erreichbar — IMAP oder EWS sollte klappen")
            lines.append("   → Falls Login trotzdem fehlschlägt: App-Passwort nötig!")
            lines.append("   → account.microsoft.com → Sicherheit → App-Kennwörter")

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    def _on_email_test(self, ok: bool, msg: str):
        color = GREEN if ok else PINK
        self._email_status.setText(msg)
        self._email_status.setStyleSheet(f"color:{color}; font-size:11px; background:transparent;")

    def _tab_calendar(self) -> QWidget:
        from PyQt6.QtWidgets import QScrollArea
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}QScrollBar:vertical{width:4px;background:#040b18;}QScrollBar::handle:vertical{background:#0a3a5a;border-radius:2px;}")
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(6)

        lay.addWidget(self._section("KALENDER-ANBIETER"))
        self._cal_provider = QComboBox()
        cal_providers = [
            ("Automatisch (Exchange oder CalDAV)", "auto"),
            ("Outlook Exchange (Firmenkonto)", "exchange"),
            ("Google Calendar (CalDAV)", "caldav"),
            ("iCloud Kalender (CalDAV)", "caldav"),
            ("Nextcloud / andere CalDAV", "caldav"),
        ]
        saved_prov = self._cfg.get("cal_provider", "auto")
        for label, val in cal_providers:
            self._cal_provider.addItem(label, val)
        self._cal_provider.currentIndexChanged.connect(self._on_cal_provider_change)
        lay.addWidget(self._cal_provider)

        # CalDAV URL (nur für CalDAV-Anbieter)
        self._cal_url_lbl = self._section("CALDAV SERVER-URL")
        lay.addWidget(self._cal_url_lbl)
        self._cal_url = self._input(
            "z.B. https://caldav.icloud.com oder https://calendar.google.com/dav/...",
            value=self._cfg.get("cal_caldav_url", "")
        )
        lay.addWidget(self._cal_url)

        # Hinweis-Box
        self._cal_info = QLabel("")
        self._cal_info.setWordWrap(True)
        self._cal_info.setStyleSheet(f"""
            background:#071525; border:1px solid #0a3060; border-radius:8px;
            color:{TEXT}; font-size:10px; padding:10px; margin-top:4px;
        """)
        lay.addWidget(self._cal_info)

        lay.addWidget(_sep())

        # Test-Zeile
        test_row = QHBoxLayout()
        self._cal_status = _lbl("Nicht getestet", size=10, color=AMBER)
        test_row.addWidget(self._cal_status)
        test_row.addStretch()
        test_btn = QPushButton("Verbindung testen")
        test_btn.setFixedHeight(32)
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.setStyleSheet(f"""
            QPushButton{{background:{BG};border:1px solid {BORDER};color:{CYAN_D};
            font-family:'Courier New';font-size:10px;border-radius:6px;padding:0 14px;}}
            QPushButton:hover{{border-color:{CYAN};color:{CYAN};}}
        """)
        test_btn.clicked.connect(self._test_calendar)
        test_row.addWidget(test_btn)
        lay.addLayout(test_row)
        lay.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll)

        # Hinweis initial setzen
        self._on_cal_provider_change(0)
        return w

    def _on_cal_provider_change(self, _=0):
        if not hasattr(self, "_cal_provider"):
            return
        val = self._cal_provider.currentData()
        is_caldav = (val == "caldav")
        self._cal_url_lbl.setVisible(is_caldav)
        self._cal_url.setVisible(is_caldav)

        hints = {
            "auto":     "Vadox nutzt automatisch die E-Mail-Zugangsdaten aus dem E-MAIL Tab.\nFür Exchange-Konten funktioniert das ohne weitere Einrichtung.",
            "exchange": "Nutzt die E-Mail-Zugangsdaten aus dem E-MAIL Tab.\nKein weiterer Schritt nötig — einfach verbinden und testen.",
            "caldav":   (
                "Google Calendar URL:\n"
                "1. Öffne calendar.google.com → Einstellungen → Kalender\n"
                "2. Adresse im CalDAV-Format kopieren\n"
                "   Format: https://www.google.com/calendar/dav/DEINE_EMAIL/events\n\n"
                "iCloud URL:\n"
                "   https://caldav.icloud.com\n"
                "   Passwort = App-Passwort (appleid.apple.com → Sicherheit)\n\n"
                "Nextcloud URL:\n"
                "   https://DEINE-DOMAIN/remote.php/dav/calendars/NUTZER/"
            ),
        }
        self._cal_info.setText(hints.get(val, ""))

    def _test_calendar(self):
        self._cal_status.setText("Teste Verbindung...")
        self._cal_status.setStyleSheet(f"color:{AMBER};font-size:10px;background:transparent;")
        import threading
        def _test():
            try:
                from vadox.tools.calendar_tool import get_todays_events
                result = get_todays_events()
                ok = "konnte nicht" not in result and "Kein Kalender" not in result
                msg = "Verbindung erfolgreich" if ok else result[:60]
            except Exception as e:
                ok, msg = False, str(e)[:60]
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self._on_cal_test(ok, msg))
        threading.Thread(target=_test, daemon=True).start()

    def _on_cal_test(self, ok, msg):
        color = GREEN if ok else PINK
        self._cal_status.setText(f"{'✓' if ok else '✗'} {msg}")
        self._cal_status.setStyleSheet(f"color:{color};font-size:10px;background:transparent;")

    def _test_voice(self):
        voice = self._voice_combo.currentData()
        import threading
        from vadox.core.tts_engine import TTSEngine
        def _run():
            tts = TTSEngine(voice=voice)
            tts.speak("Hallo, ich bin Vadox, dein persönlicher KI-Assistent.")
        threading.Thread(target=_run, daemon=True).start()

    def _on_eleven_voice_change(self, _):
        """Zeigt/versteckt das Custom-ID-Feld je nach Auswahl."""
        is_custom = self._eleven_voice_combo.currentData() == "__custom__"
        self._eleven_custom_id.setVisible(is_custom)

    def _get_eleven_voice_id(self) -> str:
        """Gibt die gewählte oder eigene Voice-ID zurück."""
        val = self._eleven_voice_combo.currentData()
        if val == "__custom__":
            return self._eleven_custom_id.text().strip()
        return val or "W2KR2ct3bRh7HcawFJB4"

    def _test_elevenlabs(self):
        api_key  = self._eleven_key_input.text().strip()
        voice_id = self._get_eleven_voice_id()
        if not api_key:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Kein API-Key", "Bitte zuerst ElevenLabs API-Key eingeben.")
            return
        import threading
        from vadox.core.tts_engine import TTSEngine
        lang = self._ui_lang_combo.currentData() if hasattr(self, "_ui_lang_combo") else "de"
        test_text = (
            "Online. All systems ready. I am Vadox, your personal AI assistant."
            if lang == "en" else
            "Online. Alle Systeme bereit. Ich bin Vadox, dein persönlicher KI-Assistent."
        )
        def _run():
            tts = TTSEngine()
            tts._eleven_key   = api_key
            tts._eleven_voice = voice_id
            tts._use_eleven   = True
            tts.speak(test_text)
        threading.Thread(target=_run, daemon=True).start()

    # ── Tab: Smart Home ───────────────────────────────────────────────────────
    def _tab_smarthome(self) -> QWidget:
        from PyQt6.QtWidgets import QScrollArea
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border:none; background:{BG}; }}")
        inner = QWidget()
        inner.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 8, 8, 16)
        lay.setSpacing(14)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        sh = self._cfg.get("smarthome", {})

        # ── Philips Hue ──────────────────────────────────────────────────────
        lay.addWidget(self._section("PHILIPS HUE"))
        hue_BG_CARD = QFrame()
        hue_BG_CARD.setStyleSheet(f"background:{BG_CARD}; border:1px solid {BORDER}; border-radius:8px;")
        hue_lay = QVBoxLayout(hue_BG_CARD)
        hue_lay.setContentsMargins(14, 12, 14, 12)
        hue_lay.setSpacing(8)

        hue_lay.addWidget(_lbl("Bridge IP-Adresse:", size=9, color=TEXTD))
        self._hue_ip = self._input("z.B. 192.168.1.100", value=sh.get("hue_ip", ""))
        hue_lay.addWidget(self._hue_ip)

        hue_lay.addWidget(_lbl("API-Key (wird automatisch erstellt):", size=9, color=TEXTD))
        self._hue_key = self._input("API-Key", value=sh.get("hue_key", ""))
        hue_lay.addWidget(self._hue_key)

        hue_btn_row = QHBoxLayout()
        pair_btn = QPushButton("Bridge-Taste druecken & verbinden")
        pair_btn.setFixedHeight(32)
        pair_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pair_btn.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        pair_btn.setStyleSheet(f"QPushButton {{ background:#0a2a0a; border:1px solid {GREEN}; color:{GREEN}; border-radius:6px; }} QPushButton:hover {{ background:#0f3a0f; }}")
        pair_btn.clicked.connect(self._hue_pair)
        self._hue_status = _lbl("", size=9, color=GREEN)
        hue_btn_row.addWidget(pair_btn)
        hue_btn_row.addWidget(self._hue_status)
        hue_btn_row.addStretch()
        hue_lay.addLayout(hue_btn_row)

        hue_lay.addWidget(_lbl(
            "Anleitung: Hue Bridge per LAN anschliessen → IP im Router nachschauen\n"
            "→ IP eintragen → Bridge-Knopf druecken → Verbinden klicken",
            size=8, color=TEXTD))
        lay.addWidget(hue_BG_CARD)

        # ── Shelly ───────────────────────────────────────────────────────────
        lay.addWidget(self._section("SHELLY GERAETE"))
        shelly_BG_CARD = QFrame()
        shelly_BG_CARD.setStyleSheet(f"background:{BG_CARD}; border:1px solid {BORDER}; border-radius:8px;")
        shelly_lay = QVBoxLayout(shelly_BG_CARD)
        shelly_lay.setContentsMargins(14, 12, 14, 12)
        shelly_lay.setSpacing(8)

        shelly_lay.addWidget(_lbl("Geraet hinzufuegen:", size=9, color=TEXTD))
        shelly_row = QHBoxLayout()
        self._shelly_name = self._input("Name (z.B. Kueche)", value="")
        self._shelly_ip   = self._input("IP (z.B. 192.168.1.50)", value="")
        add_shelly_btn = QPushButton("+ Hinzufuegen")
        add_shelly_btn.setFixedHeight(32)
        add_shelly_btn.setFixedWidth(130)
        add_shelly_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_shelly_btn.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        add_shelly_btn.setStyleSheet(f"QPushButton {{ background:#0a2a4a; border:1px solid {CYAN}; color:{CYAN}; border-radius:6px; }} QPushButton:hover {{ background:#0f3a60; }}")
        add_shelly_btn.clicked.connect(self._add_shelly_device)
        shelly_row.addWidget(self._shelly_name)
        shelly_row.addWidget(self._shelly_ip)
        shelly_row.addWidget(add_shelly_btn)
        shelly_lay.addLayout(shelly_row)

        self._shelly_list_lay = QVBoxLayout()
        self._shelly_list_lay.setSpacing(4)
        shelly_lay.addLayout(self._shelly_list_lay)
        self._refresh_shelly_list()
        lay.addWidget(shelly_BG_CARD)

        # ── Home Assistant ────────────────────────────────────────────────────
        lay.addWidget(self._section("HOME ASSISTANT"))
        ha_BG_CARD = QFrame()
        ha_BG_CARD.setStyleSheet(f"background:{BG_CARD}; border:1px solid {BORDER}; border-radius:8px;")
        ha_lay = QVBoxLayout(ha_BG_CARD)
        ha_lay.setContentsMargins(14, 12, 14, 12)
        ha_lay.setSpacing(8)

        ha_row = QHBoxLayout()
        ha_ip_col = QVBoxLayout()
        ha_ip_col.addWidget(_lbl("IP / Hostname:", size=9, color=TEXTD))
        self._ha_ip = self._input("z.B. 192.168.1.200", value=sh.get("ha_ip", ""))
        ha_ip_col.addWidget(self._ha_ip)
        ha_port_col = QVBoxLayout()
        ha_port_col.addWidget(_lbl("Port:", size=9, color=TEXTD))
        self._ha_port = self._input("8123", value=sh.get("ha_port", "8123"))
        self._ha_port.setFixedWidth(80)
        ha_port_col.addWidget(self._ha_port)
        ha_row.addLayout(ha_ip_col)
        ha_row.addLayout(ha_port_col)
        ha_lay.addLayout(ha_row)

        ha_lay.addWidget(_lbl("Langzeit-Zugriffstoken:", size=9, color=TEXTD))
        self._ha_token = self._input("Token aus HA Profil → Sicherheit", value=sh.get("ha_token", ""),
                                     echo_password=True)
        ha_lay.addWidget(self._ha_token)

        ha_test_row = QHBoxLayout()
        ha_test_btn = QPushButton("Verbindung testen")
        ha_test_btn.setFixedHeight(32)
        ha_test_btn.setFixedWidth(160)
        ha_test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ha_test_btn.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        ha_test_btn.setStyleSheet(f"QPushButton {{ background:#0a2a4a; border:1px solid {CYAN}; color:{CYAN}; border-radius:6px; }} QPushButton:hover {{ background:#0f3a60; }}")
        ha_test_btn.clicked.connect(self._test_ha)
        self._ha_status = _lbl("", size=9, color=GREEN)
        ha_test_row.addWidget(ha_test_btn)
        ha_test_row.addWidget(self._ha_status)
        ha_test_row.addStretch()
        ha_lay.addLayout(ha_test_row)

        ha_lay.addWidget(_lbl(
            "Anleitung: HA oeffnen → Profil → Sicherheit → Langzeit-Zugriffstoken erstellen → hier einfuegen",
            size=8, color=TEXTD))
        lay.addWidget(ha_BG_CARD)
        lay.addStretch()
        return w

    def _hue_pair(self):
        ip = self._hue_ip.text().strip()
        if not ip:
            self._hue_status.setText("Bitte IP eingeben")
            self._hue_status.setStyleSheet(f"color:{RED}; background:transparent;")
            return
        self._hue_status.setText("Verbinde...")
        self._hue_status.setStyleSheet(f"color:{AMBER}; background:transparent;")
        import threading
        def _pair():
            try:
                import requests
                r = requests.post(f"http://{ip}/api", json={"devicetype": "vadox#windows"}, timeout=8)
                data = r.json()
                if isinstance(data, list) and "success" in data[0]:
                    key = data[0]["success"]["username"]
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, lambda: self._on_hue_paired(ip, key))
                elif isinstance(data, list) and "error" in data[0]:
                    err = data[0]["error"].get("description", "Fehler")
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, lambda: self._on_hue_error(err))
            except Exception as e:
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, lambda: self._on_hue_error(str(e)))
        threading.Thread(target=_pair, daemon=True).start()

    def _on_hue_paired(self, ip, key):
        self._hue_key.setText(key)
        self._hue_status.setText("Verbunden!")
        self._hue_status.setStyleSheet(f"color:{GREEN}; background:transparent;")

    def _on_hue_error(self, msg):
        self._hue_status.setText(f"Fehler: {msg[:50]}")
        self._hue_status.setStyleSheet(f"color:{RED}; background:transparent;")

    def _add_shelly_device(self):
        name = self._shelly_name.text().strip()
        ip   = self._shelly_ip.text().strip()
        if not name or not ip:
            return
        sh = self._cfg.get("smarthome", {})
        devices = sh.get("shelly_devices", [])
        devices.append({"name": name, "ip": ip})
        sh["shelly_devices"] = devices
        self._cfg["smarthome"] = sh
        self._shelly_name.clear()
        self._shelly_ip.clear()
        self._refresh_shelly_list()

    def _refresh_shelly_list(self):
        while self._shelly_list_lay.count():
            item = self._shelly_list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        sh = self._cfg.get("smarthome", {})
        for d in sh.get("shelly_devices", []):
            row = QFrame()
            row.setStyleSheet(f"background:#040c18; border:1px solid {BORDER}; border-radius:5px;")
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(10, 6, 10, 6)
            r_lay.addWidget(_lbl(f"🔌 {d['name']}", size=9, color=CYAN))
            r_lay.addWidget(_lbl(d['ip'], size=8, color=TEXTD))
            r_lay.addStretch()
            del_btn = QPushButton("x")
            del_btn.setFixedSize(22, 22)
            del_btn.setStyleSheet(f"background:transparent; color:{RED}; border:none; font-size:12px;")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda _, n=d['name']: self._remove_shelly(n))
            r_lay.addWidget(del_btn)
            self._shelly_list_lay.addWidget(row)

    def _remove_shelly(self, name):
        sh = self._cfg.get("smarthome", {})
        sh["shelly_devices"] = [d for d in sh.get("shelly_devices", []) if d["name"] != name]
        self._cfg["smarthome"] = sh
        self._refresh_shelly_list()

    def _test_ha(self):
        ip    = self._ha_ip.text().strip()
        port  = self._ha_port.text().strip() or "8123"
        token = self._ha_token.text().strip()
        if not ip or not token:
            self._ha_status.setText("IP und Token benoetigt")
            self._ha_status.setStyleSheet(f"color:{RED}; background:transparent;")
            return
        self._ha_status.setText("Teste...")
        self._ha_status.setStyleSheet(f"color:{AMBER}; background:transparent;")
        import threading
        def _test():
            try:
                import requests
                r = requests.get(
                    f"http://{ip}:{port}/api/",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=8
                )
                ok = r.status_code == 200
                msg = "Verbunden!" if ok else f"Fehler {r.status_code}"
                color = GREEN if ok else RED
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, lambda: (
                    self._ha_status.setText(msg),
                    self._ha_status.setStyleSheet(f"color:{color}; background:transparent;")
                ))
            except Exception as e:
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, lambda: (
                    self._ha_status.setText(str(e)[:50]),
                    self._ha_status.setStyleSheet(f"color:{RED}; background:transparent;")
                ))
        threading.Thread(target=_test, daemon=True).start()

    # ── Tab: Profil ───────────────────────────────────────────────────────────
    def _tab_profile(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(6)

        lay.addWidget(self._section("DEIN NAME"))
        mem = memory.load()
        saved_name = mem.get("user_name") or self._cfg.get("user_name", "")
        self._name_input = self._input("z.B. Max", value=saved_name)
        lay.addWidget(self._name_input)
        lay.addWidget(_lbl("Vadox begrüßt dich beim Start mit deinem Namen.", size=9, color=TEXT_D))

        lay.addWidget(_sep())
        lay.addWidget(self._section("GEDÄCHTNIS"))

        mem_count = len(mem.get("facts", []))
        conv_count = mem.get("conversation_count", 0)
        lay.addWidget(_lbl(f"Gespeicherte Fakten: {mem_count}", size=11, color=TEXT))
        lay.addWidget(_lbl(f"Gespräche bisher: {conv_count}", size=11, color=TEXT))
        lay.addWidget(_lbl(f"Zuletzt gesehen: {mem.get('last_seen', 'Heute')}", size=11, color=TEXT))

        clear_mem_btn = QPushButton("Gedächtnis löschen")
        clear_mem_btn.setFixedHeight(32)
        clear_mem_btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:1px solid {BORDER};
                color:{PINK}; font-family:'Courier New'; font-size:10px;
                border-radius:6px; padding:0 14px; margin-top:8px;
            }}
            QPushButton:hover {{ border-color:{PINK}; background:#1a0010; }}
        """)
        clear_mem_btn.clicked.connect(self._clear_memory)
        lay.addWidget(clear_mem_btn)

        lay.addWidget(_sep())
        lay.addWidget(self._section("WINDOWS AUTOSTART"))
        lay.addWidget(_lbl("Vadox startet automatisch wenn der PC eingeschaltet wird.", size=9, color=TEXT_D))
        lay.addSpacing(4)

        from vadox.tools.autostart import is_autostart_enabled
        self._autostart_check = QCheckBox("Vadox mit Windows starten")
        self._autostart_check.setChecked(is_autostart_enabled())
        self._autostart_check.stateChanged.connect(self._toggle_autostart)
        lay.addWidget(self._autostart_check)

        self._autostart_status = _lbl(
            "✓ Autostart aktiv" if is_autostart_enabled() else "Autostart inaktiv",
            size=9, color=GREEN if is_autostart_enabled() else TEXT_D
        )
        lay.addWidget(self._autostart_status)

        lay.addStretch()
        return w

    def _toggle_autostart(self, state):
        from vadox.tools.autostart import enable_autostart, disable_autostart
        if state:
            result = enable_autostart()
            self._autostart_status.setText("✓ Autostart aktiv")
            self._autostart_status.setStyleSheet(f"color:{GREEN}; font-family:'Courier New'; font-size:9px;")
        else:
            result = disable_autostart()
            self._autostart_status.setText("Autostart inaktiv")
            self._autostart_status.setStyleSheet(f"color:{TEXT_D}; font-family:'Courier New'; font-size:9px;")

    def _clear_memory(self):
        reply = QMessageBox.question(
            self, "Gedächtnis löschen",
            "Alle gespeicherten Fakten und Vorlieben löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from vadox.core.memory import MEMORY_PATH
            if MEMORY_PATH.exists():
                MEMORY_PATH.unlink()

    # ── Tab: Über ─────────────────────────────────────────────────────────────
    # ── Tab: Telegram ─────────────────────────────────────────────────────────
    def _tab_telegram(self) -> QWidget:
        from PyQt6.QtWidgets import QScrollArea
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 24, 20, 16)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        lay.addWidget(_lbl("📱 TELEGRAM BOT", size=13, bold=True, color=CYAN))
        lay.addWidget(_lbl("Vadox sendet Benachrichtigungen direkt auf dein Handy.", size=10, color=TEXT_D))
        lay.addSpacing(12)

        lay.addWidget(self._section("SCHRITT 1 — Bot erstellen"))
        lay.addWidget(_lbl("1. Öffne Telegram und suche nach @BotFather", size=10, color=TEXT))
        lay.addWidget(_lbl("2. Schreibe /newbot und folge den Anweisungen", size=10, color=TEXT))
        lay.addWidget(_lbl("3. Kopiere den Bot-Token (sieht aus wie: 123456:ABC-DEF...)", size=10, color=TEXT))
        lay.addSpacing(8)

        lay.addWidget(self._section("BOT TOKEN"))
        self._telegram_token = self._input(
            "Bot-Token von @BotFather (z.B. 7123456789:AAF...)",
            echo_password=True,
            value=self._cfg.get("telegram_token", "")
        )
        lay.addWidget(self._telegram_token)

        lay.addWidget(self._section("SCHRITT 2 — Chat-ID herausfinden"))
        lay.addWidget(_lbl("1. Schreibe deinem Bot eine Nachricht (z.B. /start)", size=10, color=TEXT))
        lay.addWidget(_lbl("2. Klicke auf 'Chat-ID abrufen' um deine ID zu ermitteln", size=10, color=TEXT))
        lay.addSpacing(4)

        get_id_btn = QPushButton("Chat-ID abrufen")
        get_id_btn.setFixedHeight(34)
        get_id_btn.setStyleSheet(f"""
            QPushButton {{
                background:#001a35; border:1px solid {CYAN_D};
                color:{CYAN}; font-family:'Courier New'; font-size:10px;
                border-radius:6px; padding:0 16px;
            }}
            QPushButton:hover {{ background:#002a45; }}
        """)
        get_id_btn.clicked.connect(self._get_telegram_chat_id)
        lay.addWidget(get_id_btn)
        lay.addSpacing(4)

        lay.addWidget(self._section("CHAT-ID"))
        self._telegram_chat_id = self._input(
            "Deine Telegram Chat-ID (Zahl, z.B. 123456789)",
            value=self._cfg.get("telegram_chat_id", "")
        )
        lay.addWidget(self._telegram_chat_id)

        lay.addSpacing(12)
        test_btn = QPushButton("🔔 Test-Nachricht senden")
        test_btn.setFixedHeight(38)
        test_btn.setStyleSheet(f"""
            QPushButton {{
                background:#001a35; border:1px solid {CYAN};
                color:{CYAN}; font-family:'Courier New'; font-size:11px;
                border-radius:8px; padding:0 20px;
            }}
            QPushButton:hover {{ background:#002a50; }}
        """)
        test_btn.clicked.connect(self._test_telegram)
        lay.addWidget(test_btn)

        self._telegram_status = _lbl("", size=10, color=GREEN)
        lay.addWidget(self._telegram_status)
        lay.addStretch()
        return w

    def _get_telegram_chat_id(self):
        token = self._telegram_token.text().strip()
        if not token:
            self._telegram_status.setText("Bitte zuerst den Bot-Token eintragen.")
            return
        try:
            import requests
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            r   = requests.get(url, timeout=8)
            updates = r.json().get("result", [])
            if not updates:
                self._telegram_status.setText("Keine Nachrichten gefunden. Schreibe deinem Bot /start und versuche es nochmal.")
                return
            last    = updates[-1].get("message", {})
            chat_id = str(last.get("chat", {}).get("id", ""))
            name    = last.get("from", {}).get("first_name", "?")
            self._telegram_chat_id.setText(chat_id)
            self._telegram_status.setText(f"✓ Chat-ID gefunden: {chat_id} ({name})")
        except Exception as e:
            self._telegram_status.setText(f"Fehler: {e}")

    def _test_telegram(self):
        token   = self._telegram_token.text().strip()
        chat_id = self._telegram_chat_id.text().strip()
        if not token or not chat_id:
            self._telegram_status.setText("Bitte Token und Chat-ID eintragen.")
            return
        try:
            from vadox.tools.telegram_bot import send_telegram
            result = send_telegram("✅ Vadox ist verbunden! Du erhältst ab jetzt Benachrichtigungen.", token, chat_id)
            self._telegram_status.setText(result)
        except Exception as e:
            self._telegram_status.setText(f"Fehler: {e}")

    def _tab_about(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 24, 20, 16)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        logo = QLabel("V")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(64, 64)
        logo.setStyleSheet(
            f"background:#0a1e35; border:1px solid #1a4a8a; border-radius:12px;"
            f"color:{CYAN}; font-size:28px; font-weight:700; font-family:'Courier New';"
        )
        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(logo)
        logo_row.addStretch()
        lay.addLayout(logo_row)

        for text, size, color in [
            ("VADOX", 20, CYAN),
            ("Intelligenter Desktop-Assistent", 11, TEXT),
            ("Version 2.0 — Phase 2", 10, TEXT_D),
            ("", 0, ""),
            ("Unterstützte KI-Anbieter:", 10, TEXT_D),
            ("Claude (Anthropic)  ·  GPT-4o (OpenAI)  ·  Gemini (Google)", 10, TEXT),
            ("", 0, ""),
            ("Entwickelt mit Python, PyQt6, Playwright, edge-tts", 9, TEXT_D),
        ]:
            if not text:
                lay.addSpacing(4)
                continue
            l = _lbl(text, size=size, color=color, bold=(size >= 16))
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(l)

        lay.addStretch()
        return w

    # ── Speichern / Reset ────────────────────────────────────────────────────
    def _save(self):
        cfg = settings.load()
        cfg["provider"]        = self._provider_combo.currentData()
        cfg["api_key"]         = self._api_key_input.text().strip()
        cfg["model"]           = self._model_combo.currentData() or ""
        cfg["pexels_api_key"]  = self._pexels_key_input.text().strip()
        cfg["picovoice_key"]   = self._picovoice_key_input.text().strip()
        cfg["voice"]                = self._voice_combo.currentData()
        cfg["tts_enabled"]          = self._tts_check.isChecked()
        cfg["stt_enabled"]          = self._stt_check.isChecked()
        cfg["language"]             = self._lang_combo.currentData()
        cfg["elevenlabs_enabled"]   = self._eleven_check.isChecked()
        cfg["elevenlabs_api_key"]   = self._eleven_key_input.text().strip()
        cfg["elevenlabs_voice_id"]  = self._get_eleven_voice_id()
        cfg["ui_language"]          = self._ui_lang_combo.currentData() if hasattr(self, "_ui_lang_combo") else "de"
        cfg["user_name"]        = self._name_input.text().strip()
        cfg["email_provider"]   = self._email_provider.currentData()
        cfg["email_address"]    = self._email_addr.text().strip()
        cfg["email_password"]   = self._email_pass.text().strip()
        cfg["exchange_domain"]  = self._exchange_domain.text().strip()
        cfg["exchange_server"]  = self._exchange_server.text().strip()
        cfg["cal_provider"]     = self._cal_provider.currentData()
        cfg["cal_caldav_url"]   = self._cal_url.text().strip()
        # Smart Home
        sh = cfg.get("smarthome", {})
        sh["hue_ip"]   = self._hue_ip.text().strip()
        sh["hue_key"]  = self._hue_key.text().strip()
        sh["ha_ip"]    = self._ha_ip.text().strip()
        sh["ha_port"]  = self._ha_port.text().strip() or "8123"
        sh["ha_token"] = self._ha_token.text().strip()
        cfg["smarthome"] = sh
        # Telegram
        cfg["telegram_token"]   = self._telegram_token.text().strip()
        cfg["telegram_chat_id"] = self._telegram_chat_id.text().strip()
        settings.save(cfg)

        name = cfg["user_name"]
        if name:
            memory.set_user_name(name)

        self.settings_saved.emit(cfg)
        self.accept()

    def _reset(self):
        reply = QMessageBox.question(
            self, "Zurücksetzen",
            "Alle Einstellungen auf Standard zurücksetzen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from vadox.core.settings import DEFAULT, SETTINGS_PATH
            if SETTINGS_PATH.exists():
                SETTINGS_PATH.unlink()
            self.reject()

