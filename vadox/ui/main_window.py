import os
import math
import random
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea,
    QFrame, QSizePolicy, QGridLayout, QTextEdit,
    QStackedWidget, QFileDialog, QMessageBox, QComboBox, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QMetaObject, Q_ARG, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

from vadox.ui.ring_widget import RingWidget
from vadox.ui.settings_panel import SettingsPanel
from vadox.core.system_monitor import SystemMonitor
from vadox.core.ai_engine import AIEngine
from vadox.core.tts_engine import TTSEngine, SentenceSpeechQueue
from vadox.core.stt_engine import STTEngine
from vadox.core import settings, memory, license


# ── Farben ────────────────────────────────────────────────────────────────────
BG_DARK   = "#010810"
BG_PANEL  = "#030c1a"
BG_CARD   = "#061525"
BORDER    = "#0a1e35"
BORDER2   = "#0a2540"
CYAN      = "#00c8ff"
CYAN_DIM  = "#4aaace"
GREEN     = "#00ff88"
PINK      = "#ff00aa"
AMBER     = "#ffaa00"
PURPLE    = "#a066ff"
TEXT_DIM  = "#5ab4d8"
TEXT_MID  = "#7acce0"
LABEL_DIM = "#3a7aaa"


def styled(widget: QWidget, css: str):
    widget.setStyleSheet(css)
    return widget


def label(text: str, size: int = 11, color: str = CYAN, bold: bool = False,
          spacing: int = 0) -> QLabel:
    lbl = QLabel(text)
    weight = "600" if bold else "400"
    lbl.setStyleSheet(
        f"color:{color}; font-size:{size}px; font-weight:{weight};"
        f"letter-spacing:{spacing}px; background:transparent;"
    )
    lbl.setFont(QFont("Courier New", size))
    return lbl


def make_stat_card(title: str, value: str, color: str) -> tuple[QFrame, QLabel]:
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background:{BG_DARK}; border:1px solid {BORDER};
            border-radius:6px;
        }}
    """)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(8, 6, 8, 6)
    lay.setSpacing(2)

    title_lbl = label(title, size=10, color=TEXT_MID, spacing=1)
    title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    val_lbl = QLabel(value)
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    val_lbl.setStyleSheet(
        f"color:{color}; font-size:18px; font-weight:700;"
        f"font-family:'Courier New'; background:transparent;"
    )

    bar_bg = QFrame()
    bar_bg.setFixedHeight(3)
    bar_bg.setStyleSheet(f"background:#0a2040; border-radius:1px;")
    bar_fg = QFrame(bar_bg)
    bar_fg.setFixedHeight(3)
    bar_fg.setStyleSheet(f"background:{color}; border-radius:1px;")
    bar_fg.setObjectName("bar_fg")

    lay.addWidget(title_lbl)
    lay.addWidget(val_lbl)
    lay.addWidget(bar_bg)

    card._val_lbl = val_lbl
    card._bar_fg = bar_fg
    card._bar_bg = bar_bg
    card._color = color
    return card, val_lbl


class VoiceWaveform(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.active = False
        self.bars = [4] * 24
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_bars)
        self._timer.start(80)

    def set_active(self, active: bool):
        self.active = active

    def _update_bars(self):
        if self.active:
            self.bars = [random.randint(4, 22) for _ in range(24)]
        else:
            self.bars = [4] * 24
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor
        painter = QPainter(self)
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        bar_w = 2
        count = 24
        gap = max(1, (w - bar_w * count) // (count + 1))

        color = QColor(0, 200, 255) if self.active else QColor(0, 200, 255, 60)

        for i, bar_h in enumerate(self.bars):
            x = gap + i * (bar_w + gap)
            y = (h - bar_h) // 2
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(x, y, bar_w, bar_h, 1, 1)
        painter.end()


class ActivityLog(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet(f"""
            QTextEdit {{
                background:{BG_CARD}; border:none;
                color:{TEXT_MID}; font-family:'Courier New';
                font-size:10px;
            }}
            QScrollBar:vertical {{ width:4px; background:{BG_DARK}; }}
            QScrollBar::handle:vertical {{ background:{CYAN_DIM}; border-radius:2px; }}
        """)

    def log(self, source: str, message: str, color: str = None):
        now = datetime.now().strftime("%H:%M:%S")
        src_colors = {
            "SYS": TEXT_DIM,
            "AI":  "#1a8a5a",
            "ERR": "#8a2a2a",
            "NET": "#1a5a8a",
        }
        clr = color or src_colors.get(source, TEXT_MID)
        self.append(
            f'<span style="color:{TEXT_DIM};">{now}</span> '
            f'<span style="color:{clr};">{source}:</span> '
            f'<span style="color:{clr};">{message}</span>'
        )
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())


class ChatBubble(QFrame):
    feedback_given = pyqtSignal(bool)  # True = positiv, False = negativ

    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        bubble = QFrame()
        bubble.setMaximumWidth(560)
        b_lay = QVBoxLayout(bubble)
        b_lay.setContentsMargins(12, 8, 12, 8)
        b_lay.setSpacing(4)

        if is_user:
            bubble.setStyleSheet(f"""
                QFrame {{ background:#0d2a45; border:1px solid #1a5a8a;
                          border-radius:12px; border-top-right-radius:3px; }}
            """)
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            bubble.setStyleSheet(f"""
                QFrame {{ background:{BG_CARD}; border:1px solid {BORDER2};
                          border-radius:12px; border-top-left-radius:3px; }}
            """)
            src_lbl = label("VADOX", size=9, color=CYAN_DIM, spacing=1)
            b_lay.addWidget(src_lbl)
            layout.addWidget(bubble)
            layout.addStretch()

        msg_lbl = QLabel(text)
        msg_lbl.setWordWrap(True)
        msg_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        msg_lbl.setCursor(Qt.CursorShape.IBeamCursor)
        msg_lbl.setStyleSheet(
            f"color:{CYAN if not is_user else '#5ab0d8'}; font-size:13px; background:transparent;"
        )
        msg_lbl.setFont(QFont("Segoe UI", 11))
        b_lay.addWidget(msg_lbl)

        self._msg_lbl  = msg_lbl
        self._is_user  = is_user
        self._feedback_row = None

        # Feedback-Buttons nur für Vadox-Antworten
        if not is_user:
            self._add_feedback_buttons(b_lay)

    def _add_feedback_buttons(self, parent_layout):
        from PyQt6.QtWidgets import QPushButton, QHBoxLayout
        row = QHBoxLayout()
        row.setContentsMargins(0, 4, 0, 0)
        row.setSpacing(4)

        btn_style = """
            QPushButton {
                background: transparent; border: none;
                color: #1a4060; font-size: 14px; padding: 2px 4px;
            }
            QPushButton:hover { color: %s; }
        """
        self._thumb_up   = QPushButton("👍")
        self._thumb_down = QPushButton("👎")
        self._thumb_up.setFixedSize(28, 22)
        self._thumb_down.setFixedSize(28, 22)
        self._thumb_up.setStyleSheet(btn_style % "#00cc44")
        self._thumb_down.setStyleSheet(btn_style % "#cc4400")
        self._thumb_up.setToolTip("Gute Antwort")
        self._thumb_down.setToolTip("Schlechte Antwort")
        self._thumb_up.clicked.connect(lambda: self._on_feedback(True))
        self._thumb_down.clicked.connect(lambda: self._on_feedback(False))

        row.addWidget(self._thumb_up)
        row.addWidget(self._thumb_down)
        row.addStretch()
        parent_layout.addLayout(row)
        self._feedback_row = row

    def _on_feedback(self, positive: bool):
        # Buttons ausblenden nach Klick
        if hasattr(self, '_thumb_up'):
            self._thumb_up.hide()
            self._thumb_down.hide()
        from PyQt6.QtWidgets import QLabel
        icon = "👍" if positive else "👎"
        done_lbl = QLabel(icon)
        done_lbl.setStyleSheet("background:transparent; font-size:13px;")
        if self._feedback_row:
            self._feedback_row.insertWidget(0, done_lbl)
        self.feedback_given.emit(positive)

    def append_text(self, text: str):
        self._msg_lbl.setText(self._msg_lbl.text() + text)

    def get_text(self) -> str:
        return self._msg_lbl.text()


class MainWindow(QMainWindow):
    _log_signal         = pyqtSignal(str, str)
    _chat_chunk_signal  = pyqtSignal(str)
    _chat_done_signal   = pyqtSignal(str)
    _mic_result_signal  = pyqtSignal(str)
    _mic_error_signal   = pyqtSignal(str)
    _tts_done_signal    = pyqtSignal()
    _tool_use_signal    = pyqtSignal(str)
    _agent_result_signal = pyqtSignal(str, str)
    _api_test_signal    = pyqtSignal(bool, str, str, str, str)
    _wake_word_signal   = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VADOX — COMMAND CENTER")
        self.setMinimumSize(900, 600)
        self.resize(1280, 760)
        self.setStyleSheet(f"QMainWindow {{ background:{BG_DARK}; }}")

        self._ai: AIEngine | None = None
        self._tts = TTSEngine(voice="de-DE-KatjaNeural")
        self._sentence_queue = SentenceSpeechQueue(self._tts)
        self._stt = STTEngine()
        self._monitor = SystemMonitor()
        self._speaking  = False
        self._listening = False
        self._voice_followup = False  # True solange ein Sprachgespräch aktiv ist (10s Folgefenster ohne "Hey Jarvis")
        self._current_ai_bubble: ChatBubble | None = None
        self._full_ai_response = ""

        self._build_ui()
        self._connect_signals()
        self._start_clock()
        self._monitor.stats_updated.connect(self._on_stats)
        self._monitor.start()

        self._log_signal.emit("SYS", "Vadox wird gestartet...")
        self._log_signal.emit("NET", "Verbindung wird hergestellt...")
        self._log_signal.emit("SYS", "Alle Module geladen.")
        self._log_signal.emit("AI",  "Vadox ist bereit.")

        saved_key = settings.get("api_key", "")
        if saved_key:
            self._api_input.setText(saved_key)
            QTimer.singleShot(300, self._init_ai)

        memory.record_session()

        from vadox.core import agent_scheduler
        agent_scheduler.start(on_result=self._on_agent_result)
        self._log_signal.emit("AGT", "Agent-Scheduler aktiv.")

        self._start_wake_word()

        # Morgen-Briefing (nur einmal täglich, nach UI-Start)
        QTimer.singleShot(2000, self._maybe_briefing)

    # ═══════════════════════════════════════════════════════════════
    #  UI AUFBAUEN — ENTWURF 2  (Horizontal Nav + 2-Spalten-Layout)
    # ═══════════════════════════════════════════════════════════════
    def _build_ui(self):
        root = QWidget()
        root.setStyleSheet(f"background:{BG_DARK};")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_topbar())
        outer.addWidget(self._build_license_banner())

        # Body: Left col + Main col per QSplitter (resizable)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setStyleSheet("QSplitter::handle { background:#0a1e35; width:1px; }")
        self._splitter.setHandleWidth(1)

        self._left_col_widget = self._build_left_col()
        self._splitter.addWidget(self._left_col_widget)

        self._splitter.addWidget(self._build_main_col())
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([240, 900])

        outer.addWidget(self._splitter, stretch=1)
        outer.addWidget(self._build_bottombar())

    # ── Top Bar ───────────────────────────────────────────────────
    def _build_topbar(self) -> QWidget:
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"background:{BG_PANEL}; border-bottom:1px solid {BORDER};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(10)

        # Logo
        logo_hex = QFrame()
        logo_hex.setFixedSize(34, 34)
        logo_hex.setStyleSheet(
            f"background:#050f1e; border:1px solid #1a4a7a; border-radius:7px;"
        )
        lh_lay = QHBoxLayout(logo_hex)
        lh_lay.setContentsMargins(0, 0, 0, 0)
        v_lbl = label("V", size=16, color=CYAN, bold=True)
        v_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lh_lay.addWidget(v_lbl)

        name_col = QVBoxLayout()
        name_col.setSpacing(0)
        name_col.addWidget(label("VADOX", size=11, color=CYAN, bold=True, spacing=2))
        name_col.addWidget(label("COMMAND CENTER", size=7, color="#1a4a6a", spacing=1))

        sep1 = QFrame()
        sep1.setFixedSize(1, 28)
        sep1.setStyleSheet(f"background:{BORDER};")

        # Nav Pills
        self._nav_pill_widgets = []
        nav_items = [
            ("DASHBOARD",     self._go_dashboard),
            ("CHAT",          self._go_chat),
            ("ÜBERSETZER",    self._open_translator_panel),
            ("CODING",        self._open_coding_panel),
            ("LERNEN",        self._open_learn_panel),
            ("SMART HOME",    self._open_smarthome_panel),
            ("E-MAIL",        self._go_email),
            ("DATEIEN",       self._go_files),
            ("BROWSER",       self._go_browser),
            ("PC CTRL",       self._go_pc),
            ("IT SECURITY",   self._open_security_panel),
            ("PHONE LINK",    self._open_phone_panel),
            ("AGENTEN",       self._open_agent_panel),
            ("EINSTELLUNGEN", self._open_settings),
        ]
        nav_scroll = QScrollArea()
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_scroll.setFixedHeight(36)
        nav_scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        nav_inner = QWidget()
        nav_inner.setStyleSheet("background:transparent;")
        nav_inner_lay = QHBoxLayout(nav_inner)
        nav_inner_lay.setContentsMargins(0, 0, 0, 0)
        nav_inner_lay.setSpacing(4)

        for i, (name, handler) in enumerate(nav_items):
            pill = QPushButton(name)
            pill.setFixedHeight(30)
            pill.setCursor(Qt.CursorShape.PointingHandCursor)
            pill.setFont(QFont("Courier New", 9))
            self._style_pill(pill, active=(i == 0))
            pill.clicked.connect(handler)
            pill.clicked.connect(lambda _, idx=i, p=pill: self._set_nav_active(idx))
            nav_inner_lay.addWidget(pill)
            self._nav_pill_widgets.append(pill)

        nav_inner_lay.addStretch()
        nav_scroll.setWidget(nav_inner)
        nav_scroll.setWidgetResizable(True)

        sep2 = QFrame()
        sep2.setFixedSize(1, 28)
        sep2.setStyleSheet(f"background:{BORDER};")

        # Wake indicator
        wake_box = QFrame()
        wake_box.setStyleSheet(
            f"background:{BG_CARD}; border:1px solid {BORDER2}; border-radius:6px;"
        )
        wk_lay = QHBoxLayout(wake_box)
        wk_lay.setContentsMargins(8, 4, 8, 4)
        wk_lay.setSpacing(5)
        self._wake_dot = QFrame()
        self._wake_dot.setFixedSize(8, 8)
        self._wake_dot.setStyleSheet("background:#0a3a5a; border-radius:4px;")
        self._wake_lbl = QLabel("HEY JARVIS")
        self._wake_lbl.setStyleSheet("color:#0a3a5a; font-size:10px; background:transparent;")
        self._wake_lbl.setFont(QFont("Courier New", 10))
        wk_lay.addWidget(self._wake_dot)
        wk_lay.addWidget(self._wake_lbl)

        # Status badge
        status_box = QFrame()
        status_box.setStyleSheet(
            f"background:{BG_CARD}; border:1px solid {BORDER2}; border-radius:14px;"
        )
        sb_lay = QHBoxLayout(status_box)
        sb_lay.setContentsMargins(8, 4, 8, 4)
        sb_lay.setSpacing(5)
        sys_dot = QFrame()
        sys_dot.setFixedSize(7, 7)
        sys_dot.setStyleSheet(f"background:{GREEN}; border-radius:3px;")
        sb_lay.addWidget(sys_dot)
        sb_lay.addWidget(label("OPTIMAL", size=10, color=TEXT_MID, spacing=1))

        # Einstellungen-Shortcut-Button (Zahnrad)
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(32, 32)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setToolTip("Einstellungen")
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background:{BG_CARD}; border:1px solid {BORDER2};
                color:{CYAN_DIM}; font-size:16px; border-radius:6px;
            }}
            QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; background:#0a1e35; }}
        """)
        settings_btn.clicked.connect(self._open_settings)

        # Clock
        clock_col = QVBoxLayout()
        clock_col.setSpacing(0)
        clock_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._clock_lbl = label("00:00:00", size=14, color=CYAN, bold=True, spacing=1)
        self._clock_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._date_lbl  = label("", size=9, color=LABEL_DIM, spacing=1)
        self._date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        clock_col.addWidget(self._clock_lbl)
        clock_col.addWidget(self._date_lbl)

        lay.addWidget(logo_hex)
        lay.addLayout(name_col)
        lay.addWidget(sep1)
        lay.addWidget(nav_scroll, stretch=1)
        lay.addWidget(sep2)
        lay.addWidget(wake_box)
        lay.addWidget(status_box)
        lay.addWidget(settings_btn)
        lay.addLayout(clock_col)
        return bar

    def _buy_plan(self, plan: str):
        """Fordert eine dynamische Stripe-Checkout-URL vom Lizenz-Server an
        und oeffnet sie im Browser, statt eines statischen Payment-Links."""
        url = license.start_checkout(plan)
        if url:
            import webbrowser
            webbrowser.open(url)
        else:
            self._log.log("ERR", "Konnte keine Zahlungsseite laden — prüfe deine Internetverbindung.")

    def _build_license_banner(self) -> QWidget:
        """Lizenz-Banner unter der Topbar — Trial-Countdown oder PRO-Status."""
        from vadox.core.license import get_info
        info = get_info()

        self._license_banner = QFrame()
        self._license_banner.setFixedHeight(28)
        lay = QHBoxLayout(self._license_banner)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(8)

        ltype = info.get("type", "NONE")

        if ltype in ("PRO", "BUSINESS"):
            # Grüner Status-Banner
            self._license_banner.setStyleSheet(
                "background:#020d08; border-bottom:1px solid #0a3020;"
            )
            dot = QFrame()
            dot.setFixedSize(7, 7)
            dot.setStyleSheet("background:#00ff88; border-radius:3px;")
            lbl_type = "PRO" if ltype == "PRO" else "BUSINESS"
            txt = label(f"✓  VADOX {lbl_type}  —  LIFETIME · UNLIMITED", size=9,
                        color="#00ff88", spacing=1)
            lay.addWidget(dot)
            lay.addWidget(txt)
            lay.addStretch()

        elif ltype == "MONTH":
            # Cyan Banner für 1-Monats-Kunden — weiterer Monat oder Lifetime-Upgrade
            self._license_banner.setStyleSheet(
                "background:#00121a; border-bottom:1px solid #0a3a4a;"
            )
            dot = QFrame()
            dot.setFixedSize(7, 7)
            dot.setStyleSheet(f"background:{CYAN}; border-radius:3px;")
            days_left = info.get("days_left", 0)
            txt = label(f"✓  VADOX 1 MONAT — noch {days_left} Tage", size=9,
                        color=CYAN, spacing=1)

            month_btn = QPushButton("🔁 Weiteren Monat — 67 €")
            month_btn.setFixedHeight(20)
            month_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            month_btn.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
            month_btn.setStyleSheet(f"""
                QPushButton {{
                    background:#001a1a; border:1px solid {CYAN};
                    color:{CYAN}; border-radius:4px; padding:0 8px;
                }}
                QPushButton:hover {{ background:#002a2a; color:#7ae0ff; }}
            """)
            month_btn.clicked.connect(lambda: self._buy_plan("month"))

            lifetime_btn = QPushButton("⚡ Lifetime upgraden — 197 €")
            lifetime_btn.setFixedHeight(20)
            lifetime_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            lifetime_btn.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
            lifetime_btn.setStyleSheet("""
                QPushButton {
                    background:#1a0a00; border:1px solid #ffaa00;
                    color:#ffaa00; border-radius:4px; padding:0 8px;
                }
                QPushButton:hover { background:#2a1a00; color:#ffd060; }
            """)
            lifetime_btn.clicked.connect(lambda: self._buy_plan("pro"))

            lay.addWidget(dot)
            lay.addWidget(txt)
            lay.addStretch()
            lay.addWidget(month_btn)
            lay.addWidget(lifetime_btn)

        elif ltype == "TRIAL":
            # Amber Trial-Banner mit Countdown
            self._license_banner.setStyleSheet(
                "background:#0d0900; border-bottom:1px solid #3a2000;"
            )
            dot = QFrame()
            dot.setFixedSize(7, 7)
            dot.setStyleSheet("background:#ffaa00; border-radius:3px;")
            self._trial_lbl = label("⏱  TRIAL", size=9, color="#ffaa00", spacing=1)

            month_btn = QPushButton("🔁 1 Monat — 67 €")
            month_btn.setFixedHeight(20)
            month_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            month_btn.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
            month_btn.setStyleSheet(f"""
                QPushButton {{
                    background:#001a1a; border:1px solid {CYAN};
                    color:{CYAN}; border-radius:4px; padding:0 8px;
                }}
                QPushButton:hover {{ background:#002a2a; color:#7ae0ff; }}
            """)
            month_btn.clicked.connect(lambda: self._buy_plan("month"))

            buy_btn = QPushButton("⚡ PRO kaufen — 197 €  Lifetime")
            buy_btn.setFixedHeight(20)
            buy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            buy_btn.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
            buy_btn.setStyleSheet("""
                QPushButton {
                    background:#1a0a00; border:1px solid #ffaa00;
                    color:#ffaa00; border-radius:4px; padding:0 8px;
                }
                QPushButton:hover { background:#2a1a00; color:#ffd060; }
            """)
            buy_btn.clicked.connect(lambda: self._buy_plan("pro"))

            lay.addWidget(dot)
            lay.addWidget(self._trial_lbl)
            lay.addStretch()
            lay.addWidget(month_btn)
            lay.addWidget(buy_btn)

            # Countdown jede Minute aktualisieren
            self._trial_timer = QTimer(self)
            self._trial_timer.timeout.connect(self._update_trial_banner)
            self._trial_timer.start(60_000)
            self._update_trial_banner()

        else:
            self._license_banner.setFixedHeight(0)

        return self._license_banner

    def _update_trial_banner(self):
        from vadox.core.license import get_trial_info, check
        trial = get_trial_info()
        if not trial.get("active"):
            # Trial abgelaufen → Dialog zeigen
            self._trial_timer.stop()
            from vadox.ui.license_dialog import LicenseDialog
            dlg = LicenseDialog(parent=self, mode="trial_expired")
            if not (dlg.exec() and dlg.was_accepted()):
                self.close()
            return
        secs = trial.get("seconds_left", 0)
        h = secs // 3600
        m = (secs % 3600) // 60
        self._trial_lbl.setText(f"⏱  TRIAL — noch {h}h {m:02d}m")

    def _style_pill(self, pill: QPushButton, active: bool = False):
        if active:
            pill.setStyleSheet(f"""
                QPushButton {{
                    background:{BG_CARD}; border:1px solid {CYAN}44;
                    color:{CYAN}; font-family:'Courier New'; font-size:11px;
                    border-radius:6px; padding:0 13px; letter-spacing:1px;
                }}
            """)
        else:
            pill.setStyleSheet(f"""
                QPushButton {{
                    background:transparent; border:1px solid transparent;
                    color:{LABEL_DIM}; font-family:'Courier New'; font-size:11px;
                    border-radius:6px; padding:0 13px; letter-spacing:1px;
                }}
                QPushButton:hover {{
                    background:{BG_CARD}; border-color:{BORDER};
                    color:{TEXT_MID};
                }}
            """)

    def _set_nav_active(self, active_idx: int):
        for i, pill in enumerate(self._nav_pill_widgets):
            self._style_pill(pill, active=(i == active_idx))

    # ── Left Column ───────────────────────────────────────────────
    def _build_left_col(self) -> QWidget:
        col = QFrame()
        col.setMinimumWidth(200)
        col.setMaximumWidth(280)
        col.setStyleSheet(f"background:{BG_PANEL}; border-right:1px solid {BORDER};")
        lay = QVBoxLayout(col)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        # ── AI Freund Card ────────────────────────────────────────
        ai_card = QFrame()
        ai_card.setStyleSheet(
            f"background:{BG_CARD}; border:1px solid {BORDER2}; border-radius:10px;"
        )
        ai_lay = QVBoxLayout(ai_card)
        ai_lay.setContentsMargins(10, 10, 10, 10)
        ai_lay.setSpacing(6)

        ai_hdr = QHBoxLayout()
        ai_hdr.addWidget(label("AI FREUND", size=10, color=TEXT_MID, spacing=2))
        ai_hdr.addStretch()
        self._secure_lbl = label("● AKTIV", size=10, color=GREEN)
        ai_hdr.addWidget(self._secure_lbl)
        ai_lay.addLayout(ai_hdr)

        # Ring widget
        ring_wrap = QWidget()
        ring_wrap.setStyleSheet("background:transparent;")
        rw_lay = QVBoxLayout(ring_wrap)
        rw_lay.setContentsMargins(0, 0, 0, 0)
        rw_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._ring = RingWidget()
        self._ring.setFixedSize(160, 160)

        core_overlay = QWidget(self._ring)
        core_overlay.setGeometry(50, 50, 60, 60)
        core_overlay.setStyleSheet("background:transparent;")
        c_lay = QVBoxLayout(core_overlay)
        c_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_lay.setSpacing(2)

        v_box = QFrame()
        v_box.setFixedSize(36, 36)
        v_box.setStyleSheet(
            f"background:#0a1e35; border:1px solid #1a4a8a; border-radius:8px;"
        )
        vb_lay = QHBoxLayout(v_box)
        vb_lay.setContentsMargins(0, 0, 0, 0)
        vb_logo = label("V", size=16, color=CYAN, bold=True)
        vb_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vb_lay.addWidget(vb_logo)

        self._status_lbl = QLabel("ACTIVE")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setStyleSheet(
            f"background:#003a1a; border:1px solid #005a2a; color:{GREEN};"
            f"font-size:8px; letter-spacing:1px; border-radius:3px;"
            f"padding:1px 6px; font-family:'Courier New';"
        )
        c_lay.addWidget(v_box, alignment=Qt.AlignmentFlag.AlignCenter)
        c_lay.addWidget(self._status_lbl)
        rw_lay.addWidget(self._ring, alignment=Qt.AlignmentFlag.AlignCenter)
        ai_lay.addWidget(ring_wrap)

        # Emotion tags
        emo_row = QHBoxLayout()
        emo_row.setSpacing(4)
        for emo, active in [("BEREIT", True), ("AKTIV", False), ("HILFSBEREIT", False)]:
            tag = QFrame()
            tag.setStyleSheet(
                f"background:{'#00c8ff11' if active else BG_DARK}; "
                f"border:1px solid {'#00c8ff44' if active else BORDER}; border-radius:10px;"
            )
            tl = QHBoxLayout(tag)
            tl.setContentsMargins(6, 3, 6, 3)
            tl.addWidget(label(emo, size=9, color=CYAN if active else LABEL_DIM))
            emo_row.addWidget(tag)
        ai_lay.addLayout(emo_row)
        lay.addWidget(ai_card)

        # ── System Stats ──────────────────────────────────────────
        stats_card = QFrame()
        stats_card.setStyleSheet(
            f"background:{BG_CARD}; border:1px solid {BORDER2}; border-radius:10px;"
        )
        sc_lay = QVBoxLayout(stats_card)
        sc_lay.setContentsMargins(10, 8, 10, 8)
        sc_lay.setSpacing(6)

        sh = QHBoxLayout()
        sh.addWidget(label("SYSTEM MONITOR", size=10, color=TEXT_MID, spacing=2))
        sh.addStretch()
        sh.addWidget(label("● LIVE", size=10, color=GREEN))
        sc_lay.addLayout(sh)

        grid = QGridLayout()
        grid.setSpacing(5)
        self._stat_cards = {}
        stats = [("CPU", "0%", CYAN), ("RAM", "0%", PURPLE),
                 ("GPU", "0%", GREEN), ("DISK", "0%", AMBER)]
        for i, (title, val, color) in enumerate(stats):
            card, val_lbl = make_stat_card(title, val, color)
            self._stat_cards[title] = (card, val_lbl)
            # Keep MEM alias for backward compat
            if title == "RAM":
                self._stat_cards["MEM"] = (card, val_lbl)
            grid.addWidget(card, i // 2, i % 2)
        sc_lay.addLayout(grid)

        # Uptime row
        self._sys_rows = {}
        for key, val in [("UP TIME", "00:00:00"), ("PROZESSE", "---"),
                         ("NUTZER", "---"), ("OS", "WIN 11")]:
            row = QHBoxLayout()
            row.setContentsMargins(0, 1, 0, 1)
            k_lbl = label(key, size=10, color=TEXT_DIM)
            v_lbl = label(val, size=10, color=GREEN)
            row.addWidget(k_lbl)
            row.addStretch()
            row.addWidget(v_lbl)
            sc_lay.addLayout(row)
            self._sys_rows[key] = v_lbl

        lay.addWidget(stats_card)

        # ── Quick Actions ─────────────────────────────────────────
        qa_card = QFrame()
        qa_card.setStyleSheet(
            f"background:{BG_CARD}; border:1px solid {BORDER2}; border-radius:10px;"
        )
        qa_lay = QVBoxLayout(qa_card)
        qa_lay.setContentsMargins(10, 8, 10, 8)
        qa_lay.setSpacing(6)
        qa_lay.addWidget(label("SCHNELL-ZUGRIFF", size=10, color=TEXT_MID, spacing=2))

        qa_grid = QGridLayout()
        qa_grid.setSpacing(5)
        qa_items = [
            ("ÜBERSETZER", self._open_translator_panel,  CYAN),
            ("CODING",     self._open_coding_panel,       GREEN),
            ("LERNEN",     self._open_learn_panel,        PURPLE),
            ("SMART HOME", self._open_smarthome_panel,   AMBER),
            ("E-MAIL",     self._go_email,                PINK),
            ("AI FREUND",  self._open_face_panel,         "#00d4aa"),
        ]
        for i, (name, handler, color) in enumerate(qa_items):
            btn = QPushButton(name)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Courier New", 10))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background:{BG_DARK}; border:1px solid {BORDER};
                    color:{color}; border-radius:6px; letter-spacing:1px;
                    font-size:10px;
                }}
                QPushButton:hover {{
                    background:{BG_CARD}; border-color:{color}66;
                }}
            """)
            btn.clicked.connect(handler)
            qa_grid.addWidget(btn, i // 2, i % 2)
        qa_lay.addLayout(qa_grid)
        lay.addWidget(qa_card)

        # ── API Key (compact, hidden, but accessible) ─────────────
        api_box = QFrame()
        api_box.setStyleSheet(
            f"background:{BG_CARD}; border:1px solid {BORDER2}; border-radius:8px;"
        )
        ab_lay = QVBoxLayout(api_box)
        ab_lay.setContentsMargins(8, 6, 8, 6)
        ab_lay.setSpacing(4)
        ab_lay.addWidget(label("API KEY", size=10, color=TEXT_DIM, spacing=1))

        self._api_input = QLineEdit()
        self._api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_input.setPlaceholderText("sk-ant-...")
        self._api_input.setFixedHeight(26)
        self._api_input.setStyleSheet(f"""
            QLineEdit {{
                background:{BG_DARK}; border:1px solid {BORDER2};
                color:{CYAN}; font-family:'Courier New'; font-size:10px;
                border-radius:4px; padding:0 6px;
            }}
            QLineEdit:focus {{ border-color:{CYAN}; }}
        """)
        self._api_input.returnPressed.connect(self._init_ai)

        api_btn = QPushButton("VERBINDEN")
        api_btn.setFixedHeight(24)
        api_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        api_btn.setStyleSheet(f"""
            QPushButton {{
                background:#003a1a; border:1px solid #005a2a;
                color:{GREEN}; font-family:'Courier New'; font-size:8px;
                border-radius:4px; letter-spacing:1px;
            }}
            QPushButton:hover {{ background:#004a22; }}
        """)
        api_btn.clicked.connect(self._init_ai)
        ab_lay.addWidget(self._api_input)
        ab_lay.addWidget(api_btn)

        self._api_status_lbl = QLabel("")
        self._api_status_lbl.setWordWrap(True)
        self._api_status_lbl.setStyleSheet(f"color:{AMBER}; font-size:9px; background:transparent;")
        ab_lay.addWidget(self._api_status_lbl)

        help_lbl = QLabel(
            '<a href="https://console.anthropic.com/settings/keys" '
            'style="color:#00c8ff;">Kein Key? Hier in 1 Minute kostenlos holen →</a>'
        )
        help_lbl.setOpenExternalLinks(True)
        help_lbl.setStyleSheet("font-size:9px; background:transparent;")
        ab_lay.addWidget(help_lbl)
        lay.addWidget(api_box)

        return col

    # ── Main Column (Stack + Chat + Activity) ─────────────────────
    def _build_main_col(self) -> QWidget:
        col = QFrame()
        col.setStyleSheet(f"background:{BG_DARK};")
        lay = QVBoxLayout(col)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Info strip
        lay.addWidget(self._build_info_strip())

        # Stack: 0=chat/dashboard, 1=files, 2=email, 3=pc, 4=browser
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background:{BG_DARK};")
        self._stack.addWidget(self._build_dashboard_page())   # 0
        self._stack.addWidget(self._build_files_page())       # 1
        self._stack.addWidget(self._build_email_page())       # 2
        self._stack.addWidget(self._build_pc_page())          # 3
        self._stack.addWidget(self._build_browser_page())     # 4
        lay.addWidget(self._stack, stretch=1)

        # Activity log (compact, always visible)
        lay.addWidget(self._build_activity_strip())

        # Input bar
        lay.addWidget(self._build_input_bar())
        return col

    def _build_info_strip(self) -> QWidget:
        strip = QFrame()
        strip.setFixedHeight(32)
        strip.setStyleSheet(
            f"background:{BG_PANEL}; border-bottom:1px solid {BORDER};"
        )
        lay = QHBoxLayout(strip)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(8)

        self._strip_labels = {}
        tags = [
            ("CPU",   "0%",    CYAN),
            ("RAM",   "0%",    PURPLE),
            ("GPU",   "0%",    GREEN),
            ("DISK",  "0%",    AMBER),
        ]
        for key, val, color in tags:
            tag = QFrame()
            tag.setStyleSheet(
                f"background:{BG_CARD}; border:1px solid {BORDER}; border-radius:4px;"
            )
            tl = QHBoxLayout(tag)
            tl.setContentsMargins(8, 2, 8, 2)
            tl.setSpacing(5)
            tl.addWidget(label(key, size=10, color=LABEL_DIM, spacing=1))
            vl = label(val, size=10, color=color, bold=True)
            tl.addWidget(vl)
            lay.addWidget(tag)
            self._strip_labels[key] = vl

        lay.addStretch()

        # Model selector display
        cfg = settings.load()
        self._model_lbl = label(
            cfg.get("model", "claude-sonnet-5"), size=8, color=TEXT_MID
        )
        mdl_tag = QFrame()
        mdl_tag.setStyleSheet(
            f"background:{BG_CARD}; border:1px solid {BORDER}; border-radius:4px;"
        )
        ml = QHBoxLayout(mdl_tag)
        ml.setContentsMargins(8, 2, 8, 2)
        ml.setSpacing(5)
        ml.addWidget(label("MODEL", size=10, color=LABEL_DIM, spacing=1))
        ml.addWidget(self._model_lbl)
        lay.addWidget(mdl_tag)

        return strip

    def _build_activity_strip(self) -> QWidget:
        frame = QFrame()
        frame.setFixedHeight(110)
        frame.setStyleSheet(
            f"background:{BG_PANEL}; border-top:1px solid {BORDER};"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(4)

        hdr = QHBoxLayout()
        hdr.addWidget(label("AKTIVITÄTEN", size=10, color=TEXT_MID, spacing=2))
        hdr.addStretch()
        self._live_dot = label("● LIVE", size=10, color=GREEN)
        hdr.addWidget(self._live_dot)
        lay.addLayout(hdr)

        self._log = ActivityLog()
        lay.addWidget(self._log, stretch=1)
        return frame

    # ── Bottom Bar ────────────────────────────────────────────────
    def _build_bottombar(self) -> QWidget:
        bar = QFrame()
        bar.setFixedHeight(46)
        bar.setStyleSheet(f"background:{BG_PANEL}; border-top:1px solid {BORDER};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(10)

        # Left info
        self._mic_status = QFrame()
        self._mic_status.setStyleSheet(
            f"background:{BG_CARD}; border:1px solid {BORDER2}; border-radius:6px;"
        )
        ms_lay = QHBoxLayout(self._mic_status)
        ms_lay.setContentsMargins(8, 4, 8, 4)
        self._mic_status_lbl = label("● MIC BEREIT", size=10, color=GREEN, spacing=1)
        ms_lay.addWidget(self._mic_status_lbl)

        info_sep = QFrame()
        info_sep.setFixedSize(1, 20)
        info_sep.setStyleSheet(f"background:{BORDER};")

        # Voice pill (center)
        voice_pill = QFrame()
        voice_pill.setStyleSheet(
            f"background:{BG_CARD}; border:1px solid #00c8ff22; border-radius:18px;"
        )
        vp_lay = QHBoxLayout(voice_pill)
        vp_lay.setContentsMargins(14, 4, 14, 4)
        vp_lay.setSpacing(10)

        self._waveform = VoiceWaveform()
        vp_lay.addWidget(self._waveform)

        talk_lbl = label("MIT VADOX SPRECHEN — HEY JARVIS", size=10, color=CYAN, spacing=1)
        talk_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vp_lay.addWidget(talk_lbl, stretch=1)

        self._waveform2 = VoiceWaveform()
        vp_lay.addWidget(self._waveform2)

        # Right info
        self._wave_state = label("BEREIT", size=10, color=CYAN_DIM)

        day_btn = QPushButton("TAGESBRIEFING")
        day_btn.setFixedHeight(28)
        day_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        day_btn.setFont(QFont("Courier New", 10))
        day_btn.setStyleSheet(f"""
            QPushButton {{
                background:{BG_CARD}; border:1px solid {BORDER2};
                color:{TEXT_MID}; border-radius:6px; padding:0 10px; letter-spacing:1px;
            }}
            QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
        """)
        day_btn.clicked.connect(lambda: self._quick_send("Gib mir ein Tagesbriefing"))

        kb_lbl = label("F11: VOLLBILD", size=10, color=LABEL_DIM)

        lay.addWidget(self._mic_status)
        lay.addWidget(info_sep)
        lay.addWidget(voice_pill, stretch=1)
        lay.addWidget(self._wave_state)
        lay.addWidget(day_btn)
        lay.addWidget(kb_lbl)
        return bar

    # ── Nav Actions ───────────────────────────────────────────────
    def _go_dashboard(self):
        self._stack.setCurrentIndex(0)

    def _go_chat(self):
        self._stack.setCurrentIndex(0)

    def _go_files(self):
        self._stack.setCurrentIndex(1)

    def _go_email(self):
        self._stack.setCurrentIndex(2)

    def _go_pc(self):
        self._stack.setCurrentIndex(3)

    def _go_browser(self):
        self._stack.setCurrentIndex(4)

    def _nav_switch(self, idx: int):
        self._stack.setCurrentIndex(idx)

    def _nav_switch_with_nav(self, stack_idx: int, nav_btn_idx: int):
        self._stack.setCurrentIndex(stack_idx)
        self._set_nav_active(nav_btn_idx)

    # ═══════════════════════════════════════════════════════════════
    #  PAGE BUILDERS (Dashboard, Files, Email, PC, Browser)
    # ═══════════════════════════════════════════════════════════════
    def _build_dashboard_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background:{BG_DARK};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._build_chat_area(), stretch=1)
        return page

    def _build_files_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background:{BG_DARK};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        lay.addWidget(label("DATEIEN & ORDNER", size=13, color=CYAN, bold=True, spacing=2))

        path_row = QHBoxLayout()
        self._files_path = QLineEdit(str(os.path.expanduser("~")))
        self._files_path.setFixedHeight(34)
        self._files_path.setStyleSheet(self._field_style())
        browse_btn = QPushButton("Öffnen")
        browse_btn.setFixedHeight(34)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet(self._action_btn_style())
        browse_btn.clicked.connect(self._files_browse)
        go_btn = QPushButton("Anzeigen")
        go_btn.setFixedHeight(34)
        go_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        go_btn.setStyleSheet(self._action_btn_style())
        go_btn.clicked.connect(self._files_list)
        path_row.addWidget(self._files_path, stretch=1)
        path_row.addWidget(browse_btn)
        path_row.addWidget(go_btn)
        lay.addLayout(path_row)

        self._files_output = QTextEdit()
        self._files_output.setReadOnly(True)
        self._files_output.setStyleSheet(self._output_style())
        lay.addWidget(self._files_output, stretch=1)

        act_row = QHBoxLayout()
        for txt, fn in [("Vadox fragen", self._files_ask_ai),
                        ("Datei öffnen", self._files_open_selected),
                        ("Im Explorer",  self._files_open_explorer)]:
            b = QPushButton(txt)
            b.setFixedHeight(32)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(self._action_btn_style())
            b.clicked.connect(fn)
            act_row.addWidget(b)
        act_row.addStretch()
        lay.addLayout(act_row)
        return page

    def _build_email_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background:{BG_DARK};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        lay.addWidget(label("E-MAIL ZENTRALE", size=13, color=CYAN, bold=True, spacing=2))

        btn_row = QHBoxLayout()
        for lbl_txt, cmd in [
            ("Posteingang lesen", "Lies meine letzten 5 E-Mails"),
            ("Ungelesene",        "Wie viele ungelesene E-Mails habe ich?"),
            ("E-Mail suchen",     "Suche E-Mails von"),
            ("E-Mail schreiben",  "Schreibe eine E-Mail an"),
        ]:
            b = QPushButton(lbl_txt)
            b.setFixedHeight(36)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(self._action_btn_style())
            b.clicked.connect(lambda _, c=cmd: self._email_quick(c))
            btn_row.addWidget(b)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        self._email_output = QTextEdit()
        self._email_output.setReadOnly(True)
        self._email_output.setPlaceholderText(
            "E-Mails erscheinen hier...\nKlicke auf einen Button oder schreibe unten."
        )
        self._email_output.setStyleSheet(self._output_style())
        lay.addWidget(self._email_output, stretch=1)

        compose_row = QHBoxLayout()
        self._email_to   = QLineEdit()
        self._email_to.setPlaceholderText("An: empfaenger@email.de")
        self._email_subj = QLineEdit()
        self._email_subj.setPlaceholderText("Betreff")
        for f in [self._email_to, self._email_subj]:
            f.setFixedHeight(32)
            f.setStyleSheet(self._field_style())
        send_btn = QPushButton("Senden via Vadox")
        send_btn.setFixedHeight(32)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet(self._action_btn_style())
        send_btn.clicked.connect(self._email_compose_send)
        compose_row.addWidget(self._email_to, 2)
        compose_row.addWidget(self._email_subj, 2)
        compose_row.addWidget(send_btn, 1)
        lay.addLayout(compose_row)
        return page

    def _build_pc_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background:{BG_DARK};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        lay.addWidget(label("PC STEUERUNG", size=13, color=CYAN, bold=True, spacing=2))

        grid = QGridLayout()
        grid.setSpacing(10)
        actions = [
            ("Screenshot",           "Mache einen Screenshot"),
            ("System-Info",          "Zeige mir die System-Informationen"),
            ("Lautstärke erhöhen",   "Erhöhe die Lautstärke"),
            ("Lautstärke senken",    "Senke die Lautstärke"),
            ("Chrome öffnen",        "Öffne Chrome"),
            ("Notepad öffnen",       "Öffne Notepad"),
            ("Explorer öffnen",      "Öffne den Explorer"),
            ("Rechner öffnen",       "Öffne den Rechner"),
            ("Task Manager",         "Öffne den Task Manager"),
            ("Desktop anzeigen",     "Zeige den Desktop"),
            ("CPU-Auslastung",       "Wie hoch ist die CPU-Auslastung?"),
            ("RAM-Auslastung",       "Wie viel RAM wird genutzt?"),
        ]
        for i, (lbl_txt, cmd) in enumerate(actions):
            b = QPushButton(lbl_txt)
            b.setFixedHeight(42)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{
                    background:{BG_CARD}; border:1px solid #0a3060;
                    color:{CYAN}; font-family:'Courier New'; font-size:10px;
                    border-radius:8px;
                }}
                QPushButton:hover {{ background:#0a1e35; border-color:{CYAN}; }}
            """)
            b.clicked.connect(lambda _, c=cmd: self._pc_action(c))
            grid.addWidget(b, i // 3, i % 3)
        lay.addLayout(grid)

        self._pc_output = QTextEdit()
        self._pc_output.setReadOnly(True)
        self._pc_output.setPlaceholderText("Ergebnis erscheint hier...")
        self._pc_output.setStyleSheet(self._output_style())
        lay.addWidget(self._pc_output, stretch=1)
        return page

    def _build_browser_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background:{BG_DARK};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        lay.addWidget(label("BROWSER STEUERUNG", size=13, color=CYAN, bold=True, spacing=2))

        url_row = QHBoxLayout()
        self._browser_url = QLineEdit()
        self._browser_url.setPlaceholderText("https://... oder Suchbegriff eingeben")
        self._browser_url.setFixedHeight(38)
        self._browser_url.setStyleSheet(self._field_style())
        self._browser_url.returnPressed.connect(self._browser_go)
        go_btn = QPushButton("Öffnen")
        go_btn.setFixedHeight(38)
        go_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        go_btn.setStyleSheet(self._action_btn_style())
        go_btn.clicked.connect(self._browser_go)
        url_row.addWidget(self._browser_url, stretch=1)
        url_row.addWidget(go_btn)
        lay.addLayout(url_row)

        quick_row = QHBoxLayout()
        for name, url in [("Google", "https://google.de"), ("YouTube", "https://youtube.com"),
                          ("Gmail",  "https://gmail.com"),  ("LinkedIn", "https://linkedin.com"),
                          ("Amazon", "https://amazon.de")]:
            b = QPushButton(name)
            b.setFixedHeight(30)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(self._action_btn_style())
            b.clicked.connect(lambda _, u=url: self._browser_open_url(u))
            quick_row.addWidget(b)
        quick_row.addStretch()
        lay.addLayout(quick_row)

        self._browser_output = QTextEdit()
        self._browser_output.setReadOnly(True)
        self._browser_output.setPlaceholderText("Browser-Aktionen und Ergebnisse erscheinen hier...")
        self._browser_output.setStyleSheet(self._output_style())
        lay.addWidget(self._browser_output, stretch=1)

        act_row = QHBoxLayout()
        for lbl_txt, cmd in [("Seite lesen", "Lies den Inhalt der aktuellen Seite"),
                              ("Screenshot",  "Mache einen Browser-Screenshot"),
                              ("Schließen",   "Schließe den Browser")]:
            b = QPushButton(lbl_txt)
            b.setFixedHeight(32)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(self._action_btn_style())
            b.clicked.connect(lambda _, c=cmd: self._browser_action(c))
            act_row.addWidget(b)
        act_row.addStretch()
        lay.addLayout(act_row)
        return page

    # ── Chat Area ─────────────────────────────────────────────────
    def _build_chat_area(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{BG_DARK}; }}
            QScrollBar:vertical {{ width:4px; background:{BG_DARK}; }}
            QScrollBar::handle:vertical {{ background:{CYAN_DIM}; border-radius:2px; }}
        """)
        self._chat_container = QWidget()
        self._chat_container.setStyleSheet(f"background:{BG_DARK};")
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(16, 10, 16, 10)
        self._chat_layout.setSpacing(4)
        self._chat_layout.addStretch()
        scroll.setWidget(self._chat_container)
        self._chat_scroll = scroll
        return scroll

    def _build_input_bar(self) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet(f"background:{BG_DARK}; border-top:1px solid {BORDER};")
        lay = QVBoxLayout(bar)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(6)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Schreibe einen Befehl oder eine Frage...")
        self._input.setFixedHeight(40)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background:{BG_CARD}; border:1px solid {BORDER2};
                color:{CYAN}; font-family:'Courier New'; font-size:12px;
                border-radius:10px; padding:0 14px;
            }}
            QLineEdit:focus {{ border:1px solid {CYAN}; }}
        """)
        self._input.returnPressed.connect(self._send_message)

        # Datei-Anhang Button
        self._attach_btn = QPushButton("📎")
        self._attach_btn.setFixedSize(40, 40)
        self._attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._attach_btn.setToolTip("Datei anhängen (PDF, Bild, Text, Excel...)")
        self._attach_btn.setStyleSheet(f"""
            QPushButton {{
                background:{BG_CARD}; border:1px solid {BORDER2};
                color:{CYAN}; font-size:18px; border-radius:10px;
            }}
            QPushButton:hover {{ background:#1a2a3a; border-color:{CYAN}; }}
        """)
        self._attach_btn.clicked.connect(self._attach_file)
        self._attached_file: str | None = None

        self._mic_btn = QPushButton("🎤")
        self._mic_btn.setFixedSize(40, 40)
        self._mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mic_btn.setStyleSheet(self._mic_style(False))
        self._mic_btn.clicked.connect(self._toggle_mic)

        self._stop_btn = QPushButton("⏹")
        self._stop_btn.setFixedSize(40, 40)
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.setToolTip("Vadox stoppen (Sprache unterbrechen)")
        self._stop_btn.setStyleSheet(f"""
            QPushButton {{
                background:#3a0a0a; border:1px solid #8a1a1a;
                color:#ff4444; font-size:16px; border-radius:10px;
            }}
            QPushButton:hover {{ background:#5a0a0a; border-color:#ff4444; }}
        """)
        self._stop_btn.clicked.connect(self._stop_speaking)

        self._send_btn = QPushButton("➤")
        self._send_btn.setFixedSize(40, 40)
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background:#1a3a6a; border:1px solid #2a5a9a;
                color:{CYAN}; font-size:16px; border-radius:10px;
            }}
            QPushButton:hover {{ background:#1f4a80; }}
        """)
        self._send_btn.clicked.connect(self._send_message)

        input_row.addWidget(self._attach_btn)
        input_row.addWidget(self._input, stretch=1)
        input_row.addWidget(self._mic_btn)
        input_row.addWidget(self._stop_btn)
        input_row.addWidget(self._send_btn)
        lay.addLayout(input_row)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(5)
        for cmd in ["E-Mails lesen", "Screenshot", "Wetter", "Code schreiben", "Übersetzen"]:
            btn = QPushButton(cmd)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(24)
            btn.setFont(QFont("Courier New", 9))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background:{BG_CARD}; border:1px solid {BORDER};
                    color:{CYAN_DIM}; font-size:9px; border-radius:5px;
                    padding:0 10px;
                }}
                QPushButton:hover {{ border:1px solid {CYAN}; color:{CYAN}; }}
            """)
            btn.clicked.connect(lambda _, c=cmd: self._quick_send(c))
            quick_row.addWidget(btn)
        quick_row.addStretch()
        lay.addLayout(quick_row)
        return bar

    # ── Shared Styles ─────────────────────────────────────────────
    def _field_style(self):
        return f"""
            QLineEdit {{
                background:{BG_CARD}; border:1px solid {BORDER2};
                color:{CYAN}; font-family:'Courier New'; font-size:11px;
                border-radius:6px; padding:0 10px;
            }}
            QLineEdit:focus {{ border-color:{CYAN}; }}
        """

    def _output_style(self):
        return f"""
            QTextEdit {{
                background:{BG_CARD}; border:1px solid {BORDER2};
                color:{CYAN}; font-family:'Courier New'; font-size:11px;
                border-radius:8px; padding:10px;
            }}
        """

    def _action_btn_style(self):
        return f"""
            QPushButton {{
                background:{BG_CARD}; border:1px solid {BORDER2};
                color:{CYAN}; font-family:'Courier New'; font-size:10px;
                border-radius:6px; padding:0 14px;
            }}
            QPushButton:hover {{ border-color:{CYAN}; }}
        """

    # ── Responsive ────────────────────────────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = event.size().width()
        # Hide left column when too narrow
        if hasattr(self, '_left_col_widget'):
            if w < 920:
                self._left_col_widget.hide()
            else:
                self._left_col_widget.show()
                # Adjust left col width proportionally
                left_w = min(280, max(200, int(w * 0.20)))
                self._splitter.setSizes([left_w, w - left_w])

    # ═══════════════════════════════════════════════════════════════
    #  FILE ACTIONS
    # ═══════════════════════════════════════════════════════════════
    def _files_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Ordner wählen", self._files_path.text())
        if path:
            self._files_path.setText(path)
            self._files_list()

    def _files_list(self):
        path = self._files_path.text().strip()
        if not os.path.isdir(path):
            self._files_output.setPlainText("Ordner nicht gefunden.")
            return
        try:
            entries = sorted(os.listdir(path))
            lines = []
            for e in entries:
                full = os.path.join(path, e)
                tag = "[ORDNER]" if os.path.isdir(full) else "[DATEI] "
                lines.append(f"{tag}  {e}")
            self._files_output.setPlainText("\n".join(lines) if lines else "(leer)")
        except Exception as ex:
            self._files_output.setPlainText(f"Fehler: {ex}")

    def _files_ask_ai(self):
        path = self._files_path.text().strip()
        self._input.setText(f"Zeige mir den Inhalt von {path}")
        self._nav_switch(0)
        self._send_message()

    def _files_open_selected(self):
        import subprocess
        path = self._files_path.text().strip()
        if os.path.exists(path):
            subprocess.Popen(f'explorer "{path}"')

    def _files_open_explorer(self):
        import subprocess
        path = self._files_path.text().strip()
        subprocess.Popen(f'explorer "{path}"')

    # ═══════════════════════════════════════════════════════════════
    #  EMAIL ACTIONS
    # ═══════════════════════════════════════════════════════════════
    def _email_quick(self, cmd: str):
        self._input.setText(cmd)
        self._nav_switch(0)
        self._send_message()

    def _email_compose_send(self):
        to   = self._email_to.text().strip()
        subj = self._email_subj.text().strip()
        if to and subj:
            self._input.setText(f"Schreibe eine E-Mail an {to} mit Betreff '{subj}'")
            self._nav_switch(0)
            self._send_message()

    # ═══════════════════════════════════════════════════════════════
    #  PC ACTIONS
    # ═══════════════════════════════════════════════════════════════
    def _pc_action(self, cmd: str):
        self._input.setText(cmd)
        self._nav_switch(0)
        self._send_message()

    # ═══════════════════════════════════════════════════════════════
    #  BROWSER ACTIONS
    # ═══════════════════════════════════════════════════════════════
    def _browser_go(self):
        url = self._browser_url.text().strip()
        if not url:
            return
        if not url.startswith("http"):
            url = f"https://www.google.de/search?q={url.replace(' ', '+')}"
        self._input.setText(f"Öffne im Browser: {url}")
        self._nav_switch(0)
        self._send_message()

    def _browser_open_url(self, url: str):
        self._input.setText(f"Öffne im Browser: {url}")
        self._nav_switch(0)
        self._send_message()

    def _browser_action(self, cmd: str):
        self._input.setText(cmd)
        self._nav_switch(0)
        self._send_message()

    # ═══════════════════════════════════════════════════════════════
    #  SIGNALE
    # ═══════════════════════════════════════════════════════════════
    def _connect_signals(self):
        self._log_signal.connect(self._log.log)
        self._chat_chunk_signal.connect(self._on_chat_chunk)
        self._chat_done_signal.connect(self._on_chat_done)
        self._mic_result_signal.connect(self._on_mic_result)
        self._mic_error_signal.connect(self._on_mic_error)
        self._tts_done_signal.connect(self._on_tts_finished)
        self._tool_use_signal.connect(self._on_tool_use)
        self._agent_result_signal.connect(self._on_agent_result_ui)
        self._api_test_signal.connect(self._on_api_key_tested)
        self._wake_word_signal.connect(self._wake_word_activate)

    def _on_agent_result_ui(self, agent_name: str, result: str):
        self._nav_switch(0)
        self._add_chat_bubble(f"Agent {agent_name}: {result}", is_user=False)

    # ═══════════════════════════════════════════════════════════════
    #  PANEL OPENER
    # ═══════════════════════════════════════════════════════════════
    def _on_agent_result(self, agent_id: str, agent_name: str, result: str):
        self._log_signal.emit("AGT", f"{agent_name}: {result[:60]}")
        self._agent_result_signal.emit(agent_name, result)

    def _open_agent_panel(self):
        from vadox.ui.agent_panel import AgentPanel
        dlg = AgentPanel(self)
        dlg.exec()

    def _open_security_panel(self):
        from vadox.ui.security_panel import SecurityPanel
        dlg = SecurityPanel(self)
        dlg.exec()

    def _open_phone_panel(self):
        from vadox.ui.phone_panel import PhonePanel
        dlg = PhonePanel(self)
        dlg.exec()

    def _open_settings(self):
        try:
            panel = SettingsPanel(self)
            panel.settings_saved.connect(self._apply_settings)
            panel.exec()
        except Exception as e:
            import traceback; traceback.print_exc()
            QMessageBox.warning(self, "Einstellungen", f"Fehler: {e}")

    def _open_learn_panel(self):
        try:
            from vadox.ui.learn_panel import LearnPanel
            dlg = LearnPanel(self)
            dlg.exec()
        except Exception as e:
            import traceback; traceback.print_exc()
            QMessageBox.warning(self, "Lern-Modus", f"Fehler: {e}")

    def _open_coding_panel(self):
        try:
            from vadox.ui.coding_panel import CodingPanel
            dlg = CodingPanel(self)
            dlg.exec()
        except Exception as e:
            import traceback; traceback.print_exc()
            QMessageBox.warning(self, "Coding", f"Fehler: {e}")

    def _open_translator_panel(self):
        try:
            from vadox.ui.translator_panel import TranslatorPanel
            dlg = TranslatorPanel(self)
            dlg.exec()
        except Exception as e:
            import traceback; traceback.print_exc()
            QMessageBox.warning(self, "Übersetzer", f"Fehler: {e}")

    def _open_smarthome_panel(self):
        try:
            from vadox.ui.smarthome_panel import SmartHomePanel
            dlg = SmartHomePanel(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "Smart Home", f"Fehler: {e}")

    def _open_face_panel(self):
        try:
            from vadox.ui.face_panel import FacePanel
            dlg = FacePanel(self)
            dlg.friend_reaction.connect(self._on_friend_reaction)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "Gesichtserkennung",
                f"Fehler beim Laden:\n{e}\n\npip install opencv-python deepface")

    # ═══════════════════════════════════════════════════════════════
    #  WAKE-WORD
    # ═══════════════════════════════════════════════════════════════
    def _start_wake_word(self):
        wake_enabled = settings.get("wake_word_enabled", True)
        if not wake_enabled:
            self._log_signal.emit("WW", "Wake-Word deaktiviert.")
            return
        from vadox.core import wake_word
        wake_word.start(on_detected=self._on_wake_word)
        self._log_signal.emit("WW", "Wake-Word aktiv — sage 'Hey Jarvis'")
        self._update_wake_indicator(True)

    def _stop_speaking(self):
        """Vadox sofort stoppen — TTS unterbrechen, Mikrofon freigeben."""
        self._tts.stop()
        self._speaking  = False
        self._listening = False
        self._voice_followup = False
        self._mic_btn.setStyleSheet(self._mic_style(False))
        self._log_signal.emit("SYS", "Gestoppt.")

    def _maybe_briefing(self):
        """Startet das Morgen-Briefing wenn es heute noch nicht gelaufen ist."""
        try:
            from vadox.core.briefing import run_briefing, should_run_briefing
            if should_run_briefing():
                self._log_signal.emit("AI", "Starte Morgen-Briefing...")
                run_briefing(self._tts, delay_seconds=0.5)
        except Exception as e:
            print(f"[Briefing] {e}")

    def _on_wake_word(self):
        self._wake_word_signal.emit()

    def _wake_word_activate(self):
        self._update_wake_indicator(True, active=True)
        self._log_signal.emit("WW", "Wake-Word erkannt — höre zu...")
        self._toggle_mic()
        QTimer.singleShot(500, lambda: self._update_wake_indicator(True, active=False))

    def _update_wake_indicator(self, enabled: bool, active: bool = False):
        if hasattr(self, '_wake_dot'):
            if not enabled:
                self._wake_dot.setStyleSheet("background:#0a3a5a; border-radius:4px;")
                self._wake_lbl.setText("WAKE-WORD AUS")
                self._wake_lbl.setStyleSheet("color:#0a3a5a; font-size:9px; background:transparent;")
            elif active:
                self._wake_dot.setStyleSheet(f"background:{AMBER}; border-radius:4px;")
                self._wake_lbl.setText("HÖRT ZU...")
                self._wake_lbl.setStyleSheet(f"color:{AMBER}; font-size:9px; background:transparent;")
            else:
                self._wake_dot.setStyleSheet(f"background:{GREEN}; border-radius:4px;")
                self._wake_lbl.setText("HEY JARVIS")
                self._wake_lbl.setStyleSheet(f"color:{GREEN}; font-size:9px; background:transparent;")

    # ═══════════════════════════════════════════════════════════════
    #  FACE ENGINE
    # ═══════════════════════════════════════════════════════════════
    def _start_face_engine(self):
        try:
            from vadox.core import face_engine
            face_engine.start(on_result=self._on_face_result)
            self._log_signal.emit("CAM", "Gesichtserkennung aktiv.")
        except Exception as e:
            self._log_signal.emit("CAM", f"Gesichtserkennung nicht verfügbar: {e}")

    def _on_face_result(self, event: str, data: dict):
        QTimer.singleShot(0, lambda: self._handle_face_event(event, data))

    def _handle_face_event(self, event: str, data: dict):
        if event == "emotion":
            emotion    = data.get("label_de", "Neutral")
            icon       = data.get("icon", "😐")
            person     = data.get("person", "Unbekannt")
            confidence = data.get("confidence", 0)
            if confidence > 60 and data.get("emotion") not in ("neutral",):
                self._add_chat_bubble(
                    f"{icon} Ich sehe du bist gerade {emotion} ({person}). Kann ich dir helfen?",
                    is_user=False
                )
        elif event == "person":
            person = data.get("person", "Unbekannt")
            if person != "Unbekannt":
                self._add_chat_bubble(
                    f"Hallo {person}! Schön dich zu sehen. Wie kann ich dir helfen?",
                    is_user=False
                )

    def _on_friend_reaction(self, emotion: str, message: str):
        try:
            self._log_signal.emit("CAM", f"Freund-Reaktion: {emotion}")
            self._add_chat_bubble(f"💙 {message}", is_user=False)
        except Exception:
            pass
        try:
            import threading
            threading.Thread(
                target=lambda: self._tts.speak(message, on_done=self._friend_reaction_listen),
                daemon=True
            ).start()
        except Exception as e:
            print(f"[FriendReaction] {e}")

    def _friend_reaction_listen(self):
        QTimer.singleShot(300, self._do_friend_listen)

    def _do_friend_listen(self):
        if self._listening:
            return
        self._log_signal.emit("CAM", "Warte auf Antwort...")
        self._update_wake_indicator(True, active=True)
        self._listening = True
        self._mic_btn.setStyleSheet(self._mic_style(True))
        self._mic_status_lbl.setText("● ANTWORTE EINFACH...")
        self._mic_status_lbl.setStyleSheet(
            f"color:#ff6ec7; font-size:8px; letter-spacing:1px; background:transparent;"
        )
        self._waveform.set_active(True)
        self._stt.listen_once(
            on_result=lambda t: self._mic_result_signal.emit(t),
            on_error=lambda e: self._mic_error_signal.emit(e),
        )

    # ═══════════════════════════════════════════════════════════════
    #  EINSTELLUNGEN
    # ═══════════════════════════════════════════════════════════════
    def _apply_settings(self, cfg: dict):
        provider = cfg.get("provider", "claude")
        key      = cfg.get("api_key", "")
        model    = cfg.get("model", "claude-sonnet-5")
        voice    = cfg.get("voice", "de-DE-KatjaNeural")
        self._tts = TTSEngine(voice=voice)
        self._sentence_queue = SentenceSpeechQueue(self._tts)
        if key:
            self._api_input.setText(key)
            self._ai = AIEngine(provider=provider, api_key=key, model=model)
            self._log.log("NET", f"KI gewechselt: {provider.upper()} / {model}")
            self._add_ai_bubble(
                f"Einstellungen gespeichert. Ich nutze jetzt {provider.upper()} — {model}."
            )
            if hasattr(self, '_model_lbl'):
                self._model_lbl.setText(model)

    # ═══════════════════════════════════════════════════════════════
    #  UHR
    # ═══════════════════════════════════════════════════════════════
    def _start_clock(self):
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        now  = datetime.now()
        h    = now.hour % 12 or 12
        ampm = "AM" if now.hour < 12 else "PM"
        self._clock_lbl.setText(f"{h:02d}:{now.minute:02d}:{now.second:02d} {ampm}")
        days   = ["SO", "MO", "DI", "MI", "DO", "FR", "SA"]
        months = ["JAN","FEB","MRZ","APR","MAI","JUN","JUL","AUG","SEP","OKT","NOV","DEZ"]
        self._date_lbl.setText(
            f"{days[now.weekday()]} · {now.day:02d}. {months[now.month-1]} {now.year}"
        )

    # ═══════════════════════════════════════════════════════════════
    #  SYSTEM STATS
    # ═══════════════════════════════════════════════════════════════
    def _on_stats(self, stats: dict):
        self._update_card("CPU",  f"{int(stats['cpu'])}%",   stats['cpu'])
        self._update_card("RAM",  f"{int(stats['mem'])}%",   stats['mem'])
        self._update_card("MEM",  f"{int(stats['mem'])}%",   stats['mem'])
        self._update_card("GPU",  f"{int(stats['gpu'])}%",   stats['gpu'])
        self._update_card("DISK", f"{int(stats['disk'])}%",  stats['disk'])

        # Update info strip
        if hasattr(self, '_strip_labels'):
            self._strip_labels.get("CPU",  QLabel()).setText(f"{int(stats['cpu'])}%")
            self._strip_labels.get("RAM",  QLabel()).setText(f"{int(stats['mem'])}%")
            self._strip_labels.get("GPU",  QLabel()).setText(f"{int(stats['gpu'])}%")
            self._strip_labels.get("DISK", QLabel()).setText(f"{int(stats['disk'])}%")

        if "UP TIME"  in self._sys_rows: self._sys_rows["UP TIME"].setText(stats['uptime'])
        if "PROZESSE" in self._sys_rows: self._sys_rows["PROZESSE"].setText(str(stats['procs']))
        if "NUTZER"   in self._sys_rows: self._sys_rows["NUTZER"].setText(stats['user'])

    def _update_card(self, key: str, text: str, pct: float):
        if key not in self._stat_cards:
            return
        card, val_lbl = self._stat_cards[key]
        val_lbl.setText(text)
        bar_fg = card._bar_fg
        bar_bg = card._bar_bg
        bar_bg.update()
        w = max(1, int(bar_bg.width() * pct / 100))
        bar_fg.setFixedWidth(w)
        bar_fg.setFixedHeight(3)

    # ═══════════════════════════════════════════════════════════════
    #  KI
    # ═══════════════════════════════════════════════════════════════
    def _init_ai(self):
        key = self._api_input.text().strip()
        if not key:
            self._api_status_lbl.setText("Bitte zuerst einen API-Key eingeben.")
            self._api_status_lbl.setStyleSheet(f"color:{PINK}; font-size:9px; background:transparent;")
            return
        cfg      = settings.load()
        provider = cfg.get("provider", "claude")
        model    = cfg.get("model", "claude-sonnet-5")

        self._api_status_lbl.setText("Verbindung wird geprüft...")
        self._api_status_lbl.setStyleSheet(f"color:{AMBER}; font-size:9px; background:transparent;")

        import threading
        def _check():
            from vadox.core.ai_engine import test_api_connection
            ok, msg = test_api_connection(provider, key, model)
            self._api_test_signal.emit(ok, msg, key, provider, model)
        threading.Thread(target=_check, daemon=True).start()

    def _on_api_key_tested(self, ok: bool, msg: str, key: str, provider: str, model: str):
        if not ok:
            self._api_status_lbl.setText(f"✗ {msg}")
            self._api_status_lbl.setStyleSheet(f"color:{PINK}; font-size:9px; background:transparent;")
            self._log.log("ERR", f"API-Verbindung fehlgeschlagen: {msg}")
            return

        self._api_status_lbl.setText(f"✓ {msg}")
        self._api_status_lbl.setStyleSheet(f"color:{GREEN}; font-size:9px; background:transparent;")
        self._ai = AIEngine(provider=provider, api_key=key, model=model)
        settings.set_value("api_key", key)
        self._log.log("NET", "API verbunden. Key gespeichert.")
        self._log.log("AI",  "Vadox ist bereit.")

        mem   = memory.load()
        name  = mem.get("user_name") or settings.get("user_name", "")
        count = mem.get("conversation_count", 0)
        if name and count > 1:
            greeting = f"Willkommen zurück, {name}. Ich bin bereit. Wie kann ich dir helfen?"
        elif name:
            greeting = f"Hallo {name}, ich bin Vadox. Wie kann ich dir helfen?"
        else:
            greeting = "Verbindung hergestellt. Ich bin Vadox, dein KI-Assistent. Wie kann ich dir helfen?"
        self._add_ai_bubble(greeting)

    # ═══════════════════════════════════════════════════════════════
    #  CHAT
    # ═══════════════════════════════════════════════════════════════
    def _attach_file(self):
        """Datei auswählen und an nächste Nachricht anhängen."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Datei anhängen", "",
            "Alle Dateien (*.*);;PDF (*.pdf);;Bilder (*.png *.jpg *.jpeg *.bmp *.webp);;"
            "Text (*.txt *.md *.csv *.json);;Excel (*.xlsx *.xls);;Word (*.docx)"
        )
        if not path:
            return
        self._attached_file = path
        fname = Path(path).name
        # Button-Farbe ändern um anzuzeigen dass Datei angehängt ist
        self._attach_btn.setStyleSheet(f"""
            QPushButton {{
                background:#0d3a1a; border:1px solid #2aaa55;
                color:#2aff77; font-size:18px; border-radius:10px;
            }}
            QPushButton:hover {{ background:#0d4a1a; }}
        """)
        self._attach_btn.setToolTip(f"Angehängt: {fname} (nochmal klicken zum Entfernen)")
        self._input.setPlaceholderText(f"📎 {fname} — Was soll ich damit machen?")

        # Zweiter Klick entfernt die Datei
        self._attach_btn.clicked.disconnect()
        self._attach_btn.clicked.connect(self._remove_attachment)

    def _remove_attachment(self):
        self._attached_file = None
        self._attach_btn.setStyleSheet(f"""
            QPushButton {{
                background:{BG_CARD}; border:1px solid {BORDER2};
                color:{CYAN}; font-size:18px; border-radius:10px;
            }}
            QPushButton:hover {{ background:#1a2a3a; border-color:{CYAN}; }}
        """)
        self._attach_btn.setToolTip("Datei anhängen (PDF, Bild, Text, Excel...)")
        self._input.setPlaceholderText("Schreibe einen Befehl oder eine Frage...")
        self._attach_btn.clicked.disconnect()
        self._attach_btn.clicked.connect(self._attach_file)

    def _send_message(self):
        text = self._input.text().strip()
        attached = getattr(self, '_attached_file', None)
        if not text and not attached:
            return

        # Datei-Inhalt in Nachricht einbetten
        final_text = text
        if attached:
            path = Path(attached)
            fname = path.name
            suffix = path.suffix.lower()
            file_content = ""
            try:
                if suffix == ".pdf":
                    import fitz
                    doc = fitz.open(str(path))
                    pages = [doc[i].get_text() for i in range(min(len(doc), 20))]
                    file_content = "\n".join(pages)
                    doc.close()
                elif suffix in (".png", ".jpg", ".jpeg", ".bmp", ".webp"):
                    import base64
                    with open(str(path), "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    file_content = f"[BILD base64:{b64[:100]}...]"
                elif suffix in (".xlsx", ".xls"):
                    try:
                        import openpyxl
                        wb = openpyxl.load_workbook(str(path), data_only=True)
                        rows = []
                        for ws in wb.worksheets:
                            rows.append(f"--- Tabelle: {ws.title} ---")
                            for row in ws.iter_rows(max_row=200, values_only=True):
                                if any(c is not None for c in row):
                                    rows.append("\t".join(str(c) if c is not None else "" for c in row))
                        file_content = "\n".join(rows)
                    except Exception:
                        file_content = "[Excel-Datei — openpyxl nicht verfügbar]"
                elif suffix in (".docx",):
                    try:
                        import docx
                        doc = docx.Document(str(path))
                        file_content = "\n".join(p.text for p in doc.paragraphs)
                    except Exception:
                        file_content = "[Word-Datei — python-docx nicht verfügbar]"
                else:
                    with open(str(path), "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read(50000)
            except Exception as e:
                file_content = f"[Fehler beim Lesen: {e}]"

            if not text:
                final_text = f"Ich habe dir die Datei '{fname}' angehängt. Bitte analysiere sie."
            final_text = f"{final_text}\n\n--- DATEIINHALT: {fname} ---\n{file_content}\n--- ENDE DATEI ---"

            # Anhang zurücksetzen
            self._remove_attachment()

        self._input.clear()
        display_text = text if text else f"📎 {Path(attached).name if attached else ''}"
        self._add_user_bubble(display_text + (f"\n📎 {Path(attached).name}" if attached and text else ""))
        if self._ai is None:
            self._add_ai_bubble("Bitte zuerst den API-Key eingeben und auf Verbinden klicken.")
            return
        self._log.log("AI", f"Verarbeite: {final_text[:40]}...")
        self._current_ai_bubble = None
        self._full_ai_response  = ""
        self._sentence_queue.reset()
        self._ai.chat(
            final_text,
            on_chunk=lambda chunk: self._chat_chunk_signal.emit(chunk),
            on_done=lambda resp: self._chat_done_signal.emit(resp),
            on_tool_use=lambda name: self._tool_use_signal.emit(name),
        )

    def _quick_send(self, text: str):
        self._input.setText(text)
        self._send_message()

    def _add_user_bubble(self, text: str):
        bubble = ChatBubble(text, is_user=True)
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def _add_ai_bubble(self, text: str = "") -> ChatBubble:
        bubble = ChatBubble(text, is_user=False)
        bubble.feedback_given.connect(
            lambda positive, b=bubble: self._on_feedback(positive, b)
        )
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()
        return bubble

    def _on_feedback(self, positive: bool, bubble: "ChatBubble"):
        from vadox.core.feedback import save_positive, save_negative
        last_user = ""
        # Letzte Nutzer-Nachricht aus History holen
        if self._ai and self._ai.history:
            for entry in reversed(self._ai.history):
                if entry.get("role") == "user":
                    last_user = str(entry.get("content", ""))[:200]
                    break
        ai_text = bubble.get_text()
        if positive:
            save_positive(last_user, ai_text)
            self._log.log("AI", "Feedback: Antwort als gut bewertet.")
        else:
            save_negative(last_user, ai_text)
            self._log.log("AI", "Feedback: Antwort als schlecht bewertet.")

    def _add_chat_bubble(self, text: str, is_user: bool = False):
        if is_user:
            self._add_user_bubble(text)
        else:
            self._add_ai_bubble(text)

    def _on_chat_chunk(self, chunk: str):
        if self._current_ai_bubble is None:
            self._current_ai_bubble = self._add_ai_bubble("")
            self._set_speaking(True)
        self._current_ai_bubble.append_text(chunk)
        self._full_ai_response += chunk
        self._sentence_queue.feed(chunk)
        self._scroll_to_bottom()

    def _on_tool_use(self, tool_name: str):
        tool_labels = {
            "get_weather": "Wetterdaten abrufen",
            "web_search":  "Websuche durchführen",
            "news_search": "Nachrichten suchen",
            "search_files": "Dateien suchen",
            "list_directory": "Verzeichnis lesen",
            "read_file":  "Datei lesen",
            "create_file": "Datei erstellen",
            "delete_file": "Datei löschen",
            "take_screenshot": "Screenshot machen",
            "open_application": "Anwendung öffnen",
            "open_url": "Webseite öffnen",
            "get_system_info": "Systeminfo abrufen",
        }
        lbl_txt = tool_labels.get(tool_name, tool_name)
        self._log.log("SYS", f"Tool aktiv: {lbl_txt}...")
        if self._current_ai_bubble is None:
            self._current_ai_bubble = self._add_ai_bubble(f"[ {lbl_txt}... ]")
        else:
            self._current_ai_bubble.append_text(f"\n[ {lbl_txt}... ]")
        self._scroll_to_bottom()

    def _on_chat_done(self, full_response: str):
        self._log.log("AI", "Antwort erhalten.")
        self._set_speaking(True)
        self._sentence_queue.finish(on_done=lambda: self._tts_done_signal.emit())

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self._chat_scroll.verticalScrollBar().setValue(
            self._chat_scroll.verticalScrollBar().maximum()
        ))

    # ═══════════════════════════════════════════════════════════════
    #  MIKROFON
    # ═══════════════════════════════════════════════════════════════
    def _mic_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background:#3a0020; border:1px solid {PINK};
                    color:{PINK}; font-size:16px; border-radius:10px;
                }}
            """
        return f"""
            QPushButton {{
                background:{BG_CARD}; border:1px solid {BORDER2};
                color:{CYAN_DIM}; font-size:16px; border-radius:10px;
            }}
            QPushButton:hover {{ border:1px solid {CYAN}; }}
        """

    def _toggle_mic(self):
        if self._listening:
            return
        self._listening = True
        self._voice_followup = True  # Sprachgespräch aktiv — nach der Antwort 10s Folgefenster öffnen
        self._mic_btn.setStyleSheet(self._mic_style(True))
        self._mic_status_lbl.setText("● HÖRT ZU...")
        self._mic_status_lbl.setStyleSheet(
            f"color:{PINK}; font-size:8px; letter-spacing:1px; background:transparent;"
        )
        self._waveform.set_active(True)
        self._waveform2.set_active(True)
        self._log.log("SYS", "Mikrofon aktiv, höre zu...")
        self._stt.listen_once(
            on_result=lambda t: self._mic_result_signal.emit(t),
            on_error=lambda e: self._mic_error_signal.emit(e),
        )

    def _on_mic_result(self, text: str):
        self._reset_mic()
        self._log.log("SYS", f"Erkannt: {text}")
        self._input.setText(text)
        self._send_message()

    def _on_mic_error(self, error: str):
        self._reset_mic()
        self._log.log("ERR", error)
        if self._voice_followup:
            self._voice_followup = False
            self._log.log("WW", "Kein Input erkannt — zurück im Schlafmodus, warte auf 'Hey Jarvis'.")

    def _reset_mic(self):
        self._listening = False
        self._mic_btn.setStyleSheet(self._mic_style(False))
        self._mic_status_lbl.setText("● MIC BEREIT")
        self._mic_status_lbl.setStyleSheet(
            f"color:{GREEN}; font-size:8px; letter-spacing:1px; background:transparent;"
        )
        self._waveform.set_active(False)
        if hasattr(self, '_waveform2'):
            self._waveform2.set_active(False)

    # ═══════════════════════════════════════════════════════════════
    #  STIMME
    # ═══════════════════════════════════════════════════════════════
    def _on_tts_finished(self):
        self._set_speaking(False)
        # War das ein per Sprache gestartetes Gespräch? Dann 10s Folgefenster
        # öffnen (STTEngine.listen_once hat timeout=10) statt erneut "Hey Jarvis" zu verlangen.
        if self._voice_followup and not self._listening:
            self._toggle_mic()

    def _set_speaking(self, speaking: bool):
        self._speaking = speaking
        self._ring.set_state(speaking=speaking)
        if speaking:
            self._wave_state.setText("SPRICHT")
            self._wave_state.setStyleSheet(
                f"color:{CYAN}; font-size:8px; background:transparent;"
            )
            self._waveform.set_active(True)
            if hasattr(self, '_waveform2'):
                self._waveform2.set_active(True)
        else:
            self._wave_state.setText("BEREIT")
            self._wave_state.setStyleSheet(
                f"color:{CYAN_DIM}; font-size:8px; background:transparent;"
            )
            if not self._listening:
                self._waveform.set_active(False)
                if hasattr(self, '_waveform2'):
                    self._waveform2.set_active(False)

    # ═══════════════════════════════════════════════════════════════
    #  KEYBOARD
    # ═══════════════════════════════════════════════════════════════
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self._monitor.stop()
        super().closeEvent(event)
