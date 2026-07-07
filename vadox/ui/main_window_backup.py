import os
import math
import random
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea,
    QFrame, QSizePolicy, QGridLayout, QTextEdit,
    QStackedWidget, QFileDialog, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QMetaObject, Q_ARG
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

from vadox.ui.ring_widget import RingWidget
from vadox.ui.settings_panel import SettingsPanel
from vadox.core.system_monitor import SystemMonitor
from vadox.core.ai_engine import AIEngine
from vadox.core.tts_engine import TTSEngine
from vadox.core.stt_engine import STTEngine
from vadox.core import settings, memory


# ── Farben ────────────────────────────────────────────────────────────────────
BG_DARK   = "#050d1a"
BG_PANEL  = "#060f1e"
BG_CARD   = "#071525"
BORDER    = "#0a2540"
CYAN      = "#00c8ff"
CYAN_DIM  = "#2a7aaa"
GREEN     = "#00ff88"
PINK      = "#ff00aa"
AMBER     = "#ffaa00"
PURPLE    = "#8855ff"
TEXT_DIM  = "#3a8aaa"
TEXT_MID  = "#5ab4d8"


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
            background:{BG_CARD}; border:1px solid #0a2a3a;
            border-radius:6px;
        }}
    """)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(8, 6, 8, 6)
    lay.setSpacing(2)

    title_lbl = label(title, size=8, color=CYAN_DIM, spacing=1)
    title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    val_lbl = QLabel(value)
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    val_lbl.setStyleSheet(
        f"color:{color}; font-size:16px; font-weight:700;"
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
        self.setFixedHeight(32)
        self.active = False
        self.bars = [4] * 20
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_bars)
        self._timer.start(80)

    def set_active(self, active: bool):
        self.active = active

    def _update_bars(self):
        if self.active:
            self.bars = [random.randint(4, 28) for _ in range(20)]
        else:
            self.bars = [4] * 20
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor
        painter = QPainter(self)
        painter.setRenderHint(painter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        bar_w = 3
        gap = (w - bar_w * 20) // 21

        color = QColor(0, 200, 255) if self.active else QColor(10, 60, 90)

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
            "AI": "#1a8a5a",
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
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        bubble = QFrame()
        bubble.setMaximumWidth(500)
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
                QFrame {{ background:{BG_CARD}; border:1px solid {BORDER};
                          border-radius:12px; border-top-left-radius:3px; }}
            """)
            src_lbl = label("VADOX", size=9, color=CYAN_DIM, spacing=1)
            b_lay.addWidget(src_lbl)
            layout.addWidget(bubble)
            layout.addStretch()

        msg_lbl = QLabel(text)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"color:{CYAN if not is_user else '#5ab0d8'}; font-size:13px; background:transparent;")
        msg_lbl.setFont(QFont("Segoe UI", 11))
        b_lay.addWidget(msg_lbl)

        self._msg_lbl = msg_lbl

    def append_text(self, text: str):
        self._msg_lbl.setText(self._msg_lbl.text() + text)


class MainWindow(QMainWindow):
    _log_signal = pyqtSignal(str, str)
    _chat_chunk_signal = pyqtSignal(str)
    _chat_done_signal = pyqtSignal(str)
    _mic_result_signal = pyqtSignal(str)
    _mic_error_signal = pyqtSignal(str)
    _tts_done_signal = pyqtSignal()
    _tool_use_signal = pyqtSignal(str)
    _agent_result_signal = pyqtSignal(str, str)
    _wake_word_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VADOX")
        self.setMinimumSize(1100, 680)
        self.setStyleSheet(f"QMainWindow {{ background:{BG_DARK}; }}")

        self._ai: AIEngine | None = None
        self._tts = TTSEngine(voice="de-DE-KatjaNeural")
        self._stt = STTEngine()
        self._monitor = SystemMonitor()
        self._speaking = False
        self._listening = False
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
        self._log_signal.emit("AI", "Vadox ist bereit.")

        # API-Key automatisch laden
        saved_key = settings.get("api_key", "")
        if saved_key:
            self._api_input.setText(saved_key)
            QTimer.singleShot(300, self._init_ai)

        # Session in Memory aufzeichnen
        memory.record_session()

        # Autonomen Agent-Scheduler starten
        from vadox.core import agent_scheduler
        agent_scheduler.start(on_result=self._on_agent_result)
        self._log_signal.emit("AGT", "Agent-Scheduler aktiv.")

        # Wake-Word starten (falls Key vorhanden)
        self._start_wake_word()

    # ── UI aufbauen ────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        root.setStyleSheet(f"background:{BG_DARK};")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_topbar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())
        body.addWidget(self._build_center(), stretch=1)
        body.addWidget(self._build_right_panel())

        outer.addLayout(body, stretch=1)
        outer.addWidget(self._build_bottombar())

    def _build_topbar(self) -> QWidget:
        bar = QFrame()
        bar.setFixedHeight(54)
        bar.setStyleSheet(f"background:#060e1f; border-bottom:1px solid {BORDER};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)

        logo_box = QFrame()
        logo_box.setFixedSize(36, 36)
        logo_box.setStyleSheet(
            f"background:#0a1e35; border:1px solid #1a4a7a; border-radius:6px;"
        )
        logo_lay = QHBoxLayout(logo_box)
        logo_lay.setContentsMargins(0, 0, 0, 0)
        lbl_v = label("V", size=16, color=CYAN, bold=True)
        lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lay.addWidget(lbl_v)

        name_box = QVBoxLayout()
        name_box.setSpacing(0)
        name_box.addWidget(label("VADOX", size=13, color=CYAN, bold=True, spacing=1))
        name_box.addWidget(label("Intelligenter Desktop-Assistent", size=9, color=TEXT_DIM))

        title_lbl = label("V · A · D · O · X", size=18, color=CYAN, bold=True, spacing=6)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._clock_lbl = label("00:00:00", size=20, color=GREEN, bold=True, spacing=2)
        self._clock_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Wake-Word Indikator
        wake_box = QFrame()
        wake_box.setStyleSheet(f"background:#040c18; border:1px solid {BORDER}; border-radius:6px;")
        wake_lay = QHBoxLayout(wake_box)
        wake_lay.setContentsMargins(8, 4, 8, 4)
        wake_lay.setSpacing(5)
        self._wake_dot = QFrame()
        self._wake_dot.setFixedSize(8, 8)
        self._wake_dot.setStyleSheet("background:#0a3a5a; border-radius:4px;")
        self._wake_lbl = QLabel("WAKE-WORD AUS")
        self._wake_lbl.setStyleSheet("color:#0a3a5a; font-size:9px; background:transparent;")
        self._wake_lbl.setFont(QFont("Courier New", 8))
        wake_lay.addWidget(self._wake_dot)
        wake_lay.addWidget(self._wake_lbl)

        lay.addWidget(logo_box)
        lay.addSpacing(10)
        lay.addLayout(name_box)
        lay.addStretch()
        lay.addWidget(title_lbl)
        lay.addStretch()
        lay.addWidget(wake_box)
        lay.addSpacing(12)
        lay.addWidget(self._clock_lbl)
        return bar

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setFixedWidth(190)
        sidebar.setStyleSheet(f"background:#040b18; border-right:1px solid {BORDER};")

        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 12, 0, 12)
        lay.setSpacing(0)

        nav_label = label("NAVIGATION", size=9, color="#0a3a5a", spacing=2)
        nav_label.setContentsMargins(14, 0, 0, 8)
        lay.addWidget(nav_label)

        # (label, stack_index oder None/string für Dialog)
        nav_items = [
            ("DASHBOARD",     0),
            ("CHAT",          0),
            ("ÜBERSETZER",    "translator"),
            ("CODING",        "coding"),
            ("LERN-MODUS",    "learn"),
            ("BROWSER CTRL",  4),
            ("DATEIEN",       1),
            ("E-MAIL",        2),
            ("PC STEUERUNG",  3),
            ("AGENTEN",       "agents"),
            ("IT SECURITY",   "security"),
            ("PHONE LINK",    "phone"),
            ("AI FREUND",     "face"),
            ("SMART HOME",    "smarthome"),
            ("EINSTELLUNGEN", None),
        ]

        self._nav_buttons = []  # [(frame, dot, label_widget)]

        for i, (name, stack_idx) in enumerate(nav_items):
            active = (i == 0)
            btn = QFrame()
            btn.setFixedHeight(38)
            btn.setStyleSheet(
                f"background:{BG_CARD}; border:1px solid #0a4a7a; border-radius:6px; margin:2px 10px;"
                if active else "background:transparent; margin:2px 10px;"
            )
            b_lay = QHBoxLayout(btn)
            b_lay.setContentsMargins(10, 0, 10, 0)

            dot = QFrame()
            dot.setFixedSize(7, 7)
            dot.setStyleSheet(f"background:{CYAN if active else '#1a2a3a'}; border-radius:3px;")
            b_lay.addWidget(dot)
            b_lay.addSpacing(6)

            lbl_w = label(name, size=10, color=CYAN if active else TEXT_MID, spacing=1)
            b_lay.addWidget(lbl_w)
            b_lay.addStretch()
            lay.addWidget(btn)

            self._nav_buttons.append((btn, dot, lbl_w))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if stack_idx == "agents":
                btn.mousePressEvent = lambda e: self._open_agent_panel()
            elif stack_idx == "security":
                btn.mousePressEvent = lambda e: self._open_security_panel()
            elif stack_idx == "phone":
                btn.mousePressEvent = lambda e: self._open_phone_panel()
            elif stack_idx == "face":
                btn.mousePressEvent = lambda e: self._open_face_panel()
            elif stack_idx == "smarthome":
                btn.mousePressEvent = lambda e: self._open_smarthome_panel()
            elif stack_idx == "translator":
                btn.mousePressEvent = lambda e: self._open_translator_panel()
            elif stack_idx == "coding":
                btn.mousePressEvent = lambda e: self._open_coding_panel()
            elif stack_idx == "learn":
                btn.mousePressEvent = lambda e: self._open_learn_panel()
            elif stack_idx is not None:
                nav_i = i
                btn.mousePressEvent = lambda e, idx=stack_idx, bi=nav_i: self._nav_switch_with_nav(idx, bi)
            else:
                btn.mousePressEvent = lambda e: self._open_settings()

        lay.addSpacing(16)
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{BORDER};")
        lay.addWidget(sep)
        lay.addSpacing(10)

        sys_label = label("SYSTEM", size=9, color="#0a3a5a", spacing=1)
        sys_label.setContentsMargins(14, 0, 0, 6)
        lay.addWidget(sys_label)

        self._sys_rows = {}
        for key, val in [("UP TIME", "00:00:00"), ("PROZESSE", "---"), ("NUTZER", "---"), ("OS", "WIN 11")]:
            row = QHBoxLayout()
            row.setContentsMargins(14, 2, 14, 2)
            k_lbl = label(key, size=10, color=TEXT_DIM)
            v_lbl = label(val, size=10, color="#1a6a4a")
            row.addWidget(k_lbl)
            row.addStretch()
            row.addWidget(v_lbl)
            lay.addLayout(row)
            self._sys_rows[key] = v_lbl

        lay.addStretch()

        api_box = QFrame()
        api_box.setStyleSheet(f"background:{BG_CARD}; border:1px solid {BORDER}; border-radius:6px; margin:8px;")
        api_lay = QVBoxLayout(api_box)
        api_lay.setContentsMargins(8, 8, 8, 8)
        api_lay.setSpacing(4)
        api_lay.addWidget(label("API KEY", size=8, color=TEXT_DIM, spacing=1))
        self._api_input = QLineEdit()
        self._api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_input.setPlaceholderText("sk-ant-...")
        self._api_input.setFixedHeight(28)
        self._api_input.setStyleSheet(f"""
            QLineEdit {{
                background:#040b18; border:1px solid {BORDER};
                color:{CYAN}; font-family:'Courier New'; font-size:10px;
                border-radius:4px; padding:0 6px;
            }}
        """)
        self._api_input.returnPressed.connect(self._init_ai)
        api_btn = QPushButton("VERBINDEN")
        api_btn.setFixedHeight(26)
        api_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        api_btn.setStyleSheet(f"""
            QPushButton {{
                background:#003a1a; border:1px solid #005a2a;
                color:{GREEN}; font-family:'Courier New'; font-size:9px;
                border-radius:4px; letter-spacing:1px;
            }}
            QPushButton:hover {{ background:#004a22; }}
        """)
        api_btn.clicked.connect(self._init_ai)
        api_lay.addWidget(self._api_input)
        api_lay.addWidget(api_btn)
        lay.addWidget(api_box)

        return sidebar

    def _build_center(self) -> QWidget:
        center = QFrame()
        center.setStyleSheet(f"background:{BG_DARK};")
        lay = QVBoxLayout(center)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Stack: Dashboard / Dateien / E-Mail / PC-Steuerung / Browser
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background:{BG_DARK};")

        # 0 — Dashboard (Ring + Chat)
        self._stack.addWidget(self._build_dashboard_page())
        # 1 — Dateien
        self._stack.addWidget(self._build_files_page())
        # 2 — E-Mail
        self._stack.addWidget(self._build_email_page())
        # 3 — PC Steuerung
        self._stack.addWidget(self._build_pc_page())
        # 4 — Browser
        self._stack.addWidget(self._build_browser_page())

        lay.addWidget(self._stack, stretch=1)
        lay.addWidget(self._build_input_bar())
        return center

    def _nav_switch(self, idx: int):
        """Wechselt den Stack ohne Nav-Button-Highlight zu ändern."""
        self._stack.setCurrentIndex(idx)

    def _nav_switch_with_nav(self, stack_idx: int, nav_btn_idx: int):
        """Wechselt Stack UND aktualisiert Nav-Button-Highlight."""
        self._stack.setCurrentIndex(stack_idx)
        for i, (btn, dot, lbl) in enumerate(self._nav_buttons):
            active = (i == nav_btn_idx)
            btn.setStyleSheet(
                f"background:{BG_CARD}; border:1px solid #0a4a7a; border-radius:6px; margin:2px 10px;"
                if active else "background:transparent; margin:2px 10px;"
            )
            dot.setStyleSheet(
                f"background:{CYAN}; border-radius:3px;"
                if active else "background:#1a2a3a; border-radius:3px;"
            )
            lbl.setStyleSheet(
                f"color:{CYAN}; font-size:10px; letter-spacing:1px; background:transparent;"
                if active else f"color:{TEXT_MID}; font-size:10px; letter-spacing:1px; background:transparent;"
            )

    # ── Dashboard ─────────────────────────────────────────────────────────────
    def _build_dashboard_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background:{BG_DARK};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        top = QHBoxLayout()
        top.setContentsMargins(20, 10, 20, 0)
        self._secure_lbl = label("● SECURE", size=9, color="#00ff8840")
        top.addStretch()
        top.addWidget(self._secure_lbl)
        top.addStretch()
        lay.addLayout(top)

        ring_container = QFrame()
        ring_container.setStyleSheet("background:transparent;")
        r_lay = QVBoxLayout(ring_container)
        r_lay.setContentsMargins(0, 0, 0, 0)
        r_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._ring = RingWidget()
        self._ring.setFixedSize(300, 300)

        core_overlay = QWidget(self._ring)
        core_overlay.setGeometry(95, 95, 110, 110)
        core_overlay.setStyleSheet("background:transparent;")
        c_lay = QVBoxLayout(core_overlay)
        c_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_lay.setSpacing(4)

        v_box = QFrame()
        v_box.setFixedSize(56, 56)
        v_box.setStyleSheet("background:#0a1e35; border:1px solid #1a4a8a; border-radius:10px;")
        vb_lay = QHBoxLayout(v_box)
        vb_lay.setContentsMargins(0, 0, 0, 0)
        vb_logo = label("V", size=22, color=CYAN, bold=True)
        vb_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vb_lay.addWidget(vb_logo)

        core_name = label("AI CORE", size=9, color=CYAN, spacing=2)
        core_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._status_lbl = QLabel("ACTIVE")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setStyleSheet(
            f"background:#003a1a; border:1px solid #005a2a; color:{GREEN};"
            f"font-size:9px; letter-spacing:1px; border-radius:4px;"
            f"padding:2px 8px; font-family:'Courier New';"
        )
        c_lay.addWidget(v_box, alignment=Qt.AlignmentFlag.AlignCenter)
        c_lay.addWidget(core_name)
        c_lay.addWidget(self._status_lbl)
        r_lay.addWidget(self._ring, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ring_container)

        secure2 = label("🔒 SECURE: ENABLED", size=9, color="#0a3a5a")
        secure2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        secure2.setContentsMargins(0, 4, 0, 8)
        lay.addWidget(secure2)
        lay.addWidget(self._build_chat_area(), stretch=1)
        return page

    # ── Dateien ───────────────────────────────────────────────────────────────
    def _build_files_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background:{BG_DARK};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        hdr = label("DATEIEN & ORDNER", size=13, color=CYAN, bold=True, spacing=2)
        lay.addWidget(hdr)

        # Pfad-Leiste
        path_row = QHBoxLayout()
        self._files_path = QLineEdit(str(os.path.expanduser("~")))
        self._files_path.setFixedHeight(34)
        self._files_path.setStyleSheet(f"""
            QLineEdit {{ background:{BG_CARD}; border:1px solid #1a3a5a;
                color:{CYAN}; font-family:'Courier New'; font-size:11px;
                border-radius:6px; padding:0 10px; }}
        """)
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

        # Dateiliste
        self._files_output = QTextEdit()
        self._files_output.setReadOnly(True)
        self._files_output.setStyleSheet(f"""
            QTextEdit {{ background:{BG_CARD}; border:1px solid {BORDER};
                color:{CYAN}; font-family:'Courier New'; font-size:11px;
                border-radius:8px; padding:10px; }}
        """)
        lay.addWidget(self._files_output, stretch=1)

        # Aktionen
        act_row = QHBoxLayout()
        for txt, fn in [("Vadox fragen", self._files_ask_ai),
                        ("Datei öffnen", self._files_open_selected),
                        ("Im Explorer", self._files_open_explorer)]:
            b = QPushButton(txt)
            b.setFixedHeight(32)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(self._action_btn_style())
            b.clicked.connect(fn)
            act_row.addWidget(b)
        act_row.addStretch()
        lay.addLayout(act_row)
        return page

    def _action_btn_style(self):
        return f"""
            QPushButton {{ background:{BG_CARD}; border:1px solid #1a3a5a;
                color:{CYAN}; font-family:'Courier New'; font-size:10px;
                border-radius:6px; padding:0 14px; }}
            QPushButton:hover {{ border-color:{CYAN}; }}
        """

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

    # ── E-Mail ────────────────────────────────────────────────────────────────
    def _build_email_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background:{BG_DARK};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        hdr = label("E-MAIL ZENTRALE", size=13, color=CYAN, bold=True, spacing=2)
        lay.addWidget(hdr)

        btn_row = QHBoxLayout()
        quick_email = [
            ("Posteingang lesen", "Lies meine letzten 5 E-Mails"),
            ("Ungelesene", "Wie viele ungelesene E-Mails habe ich?"),
            ("E-Mail suchen", "Suche E-Mails von"),
            ("E-Mail schreiben", "Schreibe eine E-Mail an"),
        ]
        for lbl_txt, cmd in quick_email:
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
        self._email_output.setPlaceholderText("E-Mails erscheinen hier...\nKlicke auf einen Button oder schreibe einen Befehl unten.")
        self._email_output.setStyleSheet(f"""
            QTextEdit {{ background:{BG_CARD}; border:1px solid {BORDER};
                color:{CYAN}; font-family:'Courier New'; font-size:11px;
                border-radius:8px; padding:10px; }}
        """)
        lay.addWidget(self._email_output, stretch=1)

        compose_row = QHBoxLayout()
        self._email_to   = QLineEdit(); self._email_to.setPlaceholderText("An: empfaenger@email.de")
        self._email_subj = QLineEdit(); self._email_subj.setPlaceholderText("Betreff")
        for f in [self._email_to, self._email_subj]:
            f.setFixedHeight(32)
            f.setStyleSheet(f"""QLineEdit {{ background:{BG_CARD}; border:1px solid #1a3a5a;
                color:{CYAN}; font-family:'Courier New'; font-size:10px;
                border-radius:6px; padding:0 8px; }}""")
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

    # ── PC Steuerung ──────────────────────────────────────────────────────────
    def _build_pc_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background:{BG_DARK};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        hdr = label("PC STEUERUNG", size=13, color=CYAN, bold=True, spacing=2)
        lay.addWidget(hdr)

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
                QPushButton {{ background:{BG_CARD}; border:1px solid #0a3060;
                    color:{CYAN}; font-family:'Courier New'; font-size:10px;
                    border-radius:8px; }}
                QPushButton:hover {{ background:#0a1e35; border-color:{CYAN}; }}
            """)
            b.clicked.connect(lambda _, c=cmd: self._pc_action(c))
            grid.addWidget(b, i // 3, i % 3)

        lay.addLayout(grid)

        self._pc_output = QTextEdit()
        self._pc_output.setReadOnly(True)
        self._pc_output.setPlaceholderText("Ergebnis erscheint hier...")
        self._pc_output.setStyleSheet(f"""
            QTextEdit {{ background:{BG_CARD}; border:1px solid {BORDER};
                color:{CYAN}; font-family:'Courier New'; font-size:11px;
                border-radius:8px; padding:10px; }}
        """)
        lay.addWidget(self._pc_output, stretch=1)
        return page

    def _pc_action(self, cmd: str):
        self._input.setText(cmd)
        self._nav_switch(0)
        self._send_message()

    # ── Browser ───────────────────────────────────────────────────────────────
    def _build_browser_page(self) -> QWidget:
        page = QFrame()
        page.setStyleSheet(f"background:{BG_DARK};")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        hdr = label("BROWSER STEUERUNG", size=13, color=CYAN, bold=True, spacing=2)
        lay.addWidget(hdr)

        url_row = QHBoxLayout()
        self._browser_url = QLineEdit()
        self._browser_url.setPlaceholderText("https://... oder Suchbegriff eingeben")
        self._browser_url.setFixedHeight(38)
        self._browser_url.setStyleSheet(f"""
            QLineEdit {{ background:{BG_CARD}; border:1px solid #1a3a5a;
                color:{CYAN}; font-family:'Courier New'; font-size:11px;
                border-radius:8px; padding:0 12px; }}
            QLineEdit:focus {{ border-color:{CYAN}; }}
        """)
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
        quick_sites = [("Google", "https://google.de"), ("YouTube", "https://youtube.com"),
                       ("Gmail", "https://gmail.com"), ("LinkedIn", "https://linkedin.com"),
                       ("Amazon", "https://amazon.de")]
        for name, url in quick_sites:
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
        self._browser_output.setStyleSheet(f"""
            QTextEdit {{ background:{BG_CARD}; border:1px solid {BORDER};
                color:{CYAN}; font-family:'Courier New'; font-size:11px;
                border-radius:8px; padding:10px; }}
        """)
        lay.addWidget(self._browser_output, stretch=1)

        act_row = QHBoxLayout()
        browser_actions = [
            ("Seite lesen", "Lies den Inhalt der aktuellen Seite"),
            ("Screenshot", "Mache einen Browser-Screenshot"),
            ("Browser schließen", "Schließe den Browser"),
        ]
        for lbl_txt, cmd in browser_actions:
            b = QPushButton(lbl_txt)
            b.setFixedHeight(32)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(self._action_btn_style())
            b.clicked.connect(lambda _, c=cmd: self._browser_action(c))
            act_row.addWidget(b)
        act_row.addStretch()
        lay.addLayout(act_row)
        return page

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
        self._chat_layout.setContentsMargins(16, 8, 16, 8)
        self._chat_layout.setSpacing(4)
        self._chat_layout.addStretch()
        scroll.setWidget(self._chat_container)
        self._chat_scroll = scroll
        return scroll

    def _build_input_bar(self) -> QWidget:
        bar = QFrame()
        bar.setStyleSheet(f"background:{BG_DARK}; border-top:1px solid {BORDER};")
        lay = QVBoxLayout(bar)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(8)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Schreibe einen Befehl oder eine Frage...")
        self._input.setFixedHeight(42)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background:{BG_CARD}; border:1px solid #1a3a5a;
                color:{CYAN}; font-family:'Courier New'; font-size:12px;
                border-radius:10px; padding:0 14px;
            }}
            QLineEdit:focus {{ border:1px solid {CYAN}; }}
        """)
        self._input.returnPressed.connect(self._send_message)

        self._mic_btn = QPushButton("🎤")
        self._mic_btn.setFixedSize(42, 42)
        self._mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mic_btn.setStyleSheet(self._mic_style(False))
        self._mic_btn.clicked.connect(self._toggle_mic)

        self._send_btn = QPushButton("➤")
        self._send_btn.setFixedSize(42, 42)
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background:#1a3a6a; border:1px solid #2a5a9a;
                color:{CYAN}; font-size:16px; border-radius:10px;
            }}
            QPushButton:hover {{ background:#1f4a80; }}
        """)
        self._send_btn.clicked.connect(self._send_message)

        input_row.addWidget(self._input, stretch=1)
        input_row.addWidget(self._mic_btn)
        input_row.addWidget(self._send_btn)
        lay.addLayout(input_row)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(6)
        quick_cmds = ["E-Mails lesen", "Screenshot", "Datei suchen", "Wetter", "Code schreiben"]
        for cmd in quick_cmds:
            btn = QPushButton(cmd)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(26)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background:{BG_CARD}; border:1px solid {BORDER};
                    color:{CYAN_DIM}; font-size:10px; border-radius:5px;
                    padding:0 10px; font-family:'Courier New';
                }}
                QPushButton:hover {{ border:1px solid {CYAN}; color:{CYAN}; }}
            """)
            btn.clicked.connect(lambda _, c=cmd: self._quick_send(c))
            quick_row.addWidget(btn)
        quick_row.addStretch()
        lay.addLayout(quick_row)
        return bar

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFixedWidth(248)
        panel.setStyleSheet(f"background:#040b18; border-left:1px solid {BORDER};")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        search = QLineEdit()
        search.setPlaceholderText("Befehl oder Frage eingeben...")
        search.setFixedHeight(34)
        search.setStyleSheet(f"""
            QLineEdit {{
                background:{BG_CARD}; border:1px solid #0a3060;
                color:{CYAN_DIM}; font-family:'Courier New'; font-size:10px;
                border-radius:6px; padding:0 10px;
            }}
        """)
        search.returnPressed.connect(lambda: (self._input.setText(search.text()), self._send_message(), search.clear()))
        lay.addWidget(search)

        grid = QGridLayout()
        grid.setSpacing(6)
        self._stat_cards = {}
        stats = [("CPU", "0%", CYAN), ("MEM", "0%", PINK), ("NET", "0KB", GREEN),
                 ("GPU", "0%", AMBER), ("DISK", "0%", PURPLE)]
        positions = [(0,0),(0,1),(0,2),(1,0),(1,1)]
        for i, (title, val, color) in enumerate(stats):
            r, c = positions[i]
            card, val_lbl = make_stat_card(title, val, color)
            self._stat_cards[title] = (card, val_lbl)
            grid.addWidget(card, r, c)
        lay.addLayout(grid)

        log_header = QHBoxLayout()
        log_header.addWidget(label("ACTIVITY LOG", size=9, color=CYAN_DIM, spacing=1))
        log_header.addStretch()
        self._live_dot = label("● LIVE", size=9, color=GREEN)
        log_header.addWidget(self._live_dot)
        lay.addLayout(log_header)

        self._log = ActivityLog()
        lay.addWidget(self._log, stretch=1)

        wave_header = QHBoxLayout()
        wave_header.addWidget(label("AI STIMME", size=9, color=CYAN_DIM, spacing=1))
        wave_header.addStretch()
        self._wave_state = label("BEREIT", size=9, color=CYAN_DIM)
        wave_header.addWidget(self._wave_state)
        lay.addLayout(wave_header)

        wave_box = QFrame()
        wave_box.setStyleSheet(f"background:{BG_CARD}; border:1px solid {BORDER}; border-radius:6px;")
        w_lay = QVBoxLayout(wave_box)
        w_lay.setContentsMargins(8, 6, 8, 6)
        self._waveform = VoiceWaveform()
        w_lay.addWidget(self._waveform)
        lay.addWidget(wave_box)

        self._mic_status = QFrame()
        self._mic_status.setFixedHeight(32)
        self._mic_status.setStyleSheet(
            f"background:#001a0a; border:1px solid #003a1a; border-radius:6px;"
        )
        ms_lay = QHBoxLayout(self._mic_status)
        ms_lay.setContentsMargins(8, 0, 8, 0)
        self._mic_status_lbl = label("● MIKROFON BEREIT", size=10, color=GREEN, spacing=1)
        self._mic_status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ms_lay.addWidget(self._mic_status_lbl)
        lay.addWidget(self._mic_status)

        fs_btn = QFrame()
        fs_btn.setFixedHeight(28)
        fs_btn.setStyleSheet(f"border:1px solid {BORDER}; border-radius:6px;")
        fs_lay = QHBoxLayout(fs_btn)
        fs_lay.setContentsMargins(8, 0, 8, 0)
        fs_lay.addWidget(label("VOLLBILD  (F11)", size=9, color=TEXT_DIM, spacing=1))
        lay.addWidget(fs_btn)

        return panel

    def _build_bottombar(self) -> QWidget:
        bar = QFrame()
        bar.setFixedHeight(24)
        bar.setStyleSheet(f"background:#040b18; border-top:1px solid {BORDER};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.addWidget(label("F4: MUTE  ·  F11: VOLLBILD", size=9, color="#0a2a3a"))
        lay.addStretch()
        lay.addWidget(label("VADOX — INTELLIGENTER DESKTOP-ASSISTENT", size=9, color="#0a3a5a", spacing=2))
        lay.addStretch()
        lay.addWidget(label("© VADOX 2026", size=9, color="#0a2a3a"))
        return bar

    # ── Signale verbinden ──────────────────────────────────────────────────────
    def _connect_signals(self):
        self._log_signal.connect(self._log.log)
        self._chat_chunk_signal.connect(self._on_chat_chunk)
        self._chat_done_signal.connect(self._on_chat_done)
        self._mic_result_signal.connect(self._on_mic_result)
        self._mic_error_signal.connect(self._on_mic_error)
        self._tts_done_signal.connect(lambda: self._set_speaking(False))
        self._tool_use_signal.connect(self._on_tool_use)
        self._agent_result_signal.connect(self._on_agent_result_ui)
        self._wake_word_signal.connect(self._wake_word_activate)

    def _on_agent_result_ui(self, agent_name: str, result: str):
        """Zeigt Agent-Ergebnis als Chat-Nachricht an."""
        self._nav_switch(0)
        self._add_chat_bubble(f"Agent {agent_name}: {result}", is_user=False)

    # ── Einstellungen ─────────────────────────────────────────────────────────
    def _on_agent_result(self, agent_id: str, agent_name: str, result: str):
        """Wird aufgerufen wenn ein Agent ein Ergebnis liefert (Thread-sicher via Signal)."""
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
        panel = SettingsPanel(self)
        panel.settings_saved.connect(self._apply_settings)
        panel.exec()

    # ── Wake-Word ──────────────────────────────────────────────────────────────
    def _start_wake_word(self):
        wake_enabled = settings.get("wake_word_enabled", True)
        if not wake_enabled:
            self._log_signal.emit("WW", "Wake-Word deaktiviert.")
            return
        from vadox.core import wake_word
        wake_word.start(on_detected=self._on_wake_word)
        self._log_signal.emit("WW", "Wake-Word aktiv — sage 'Hey Jarvis'")
        self._update_wake_indicator(True)

    def _on_wake_word(self):
        """Wird aus Wake-Word Thread aufgerufen — Signal in UI-Thread senden."""
        self._wake_word_signal.emit()

    def _wake_word_activate(self):
        """Läuft im UI-Thread via Signal — Mikrofon aktivieren + visuelles Feedback."""
        self._update_wake_indicator(True, active=True)
        self._log_signal.emit("WW", "Wake-Word erkannt — höre zu...")
        self._toggle_mic()
        QTimer.singleShot(500, lambda: self._update_wake_indicator(True, active=False))

    # ── Face Engine ────────────────────────────────────────────────────────────
    def _start_face_engine(self):
        try:
            from vadox.core import face_engine
            face_engine.start(on_result=self._on_face_result)
            self._log_signal.emit("CAM", "Gesichtserkennung aktiv.")
        except Exception as e:
            self._log_signal.emit("CAM", f"Gesichtserkennung nicht verfügbar: {e}")

    def _on_face_result(self, event: str, data: dict):
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._handle_face_event(event, data))

    def _handle_face_event(self, event: str, data: dict):
        if event == "emotion":
            emotion = data.get("label_de", "Neutral")
            icon = data.get("icon", "😐")
            person = data.get("person", "Unbekannt")
            confidence = data.get("confidence", 0)
            # Nur bei starken Emotionen reagieren (>60% Konfidenz)
            if confidence > 60 and data.get("emotion") not in ("neutral",):
                self._add_chat_bubble(
                    f"{icon} Ich sehe du bist gerade {emotion} ({person}). "
                    f"Kann ich dir helfen?", is_user=False
                )
            # Titelleiste aktualisieren
            if hasattr(self, '_face_emo_lbl'):
                self._face_emo_lbl.setText(f"{icon} {emotion}")
        elif event == "person":
            person = data.get("person", "Unbekannt")
            if person != "Unbekannt":
                self._add_chat_bubble(
                    f"Hallo {person}! Schön dich zu sehen. Wie kann ich dir helfen?",
                    is_user=False
                )
                if hasattr(self, '_face_emo_lbl'):
                    self._face_emo_lbl.setText(f"👤 {person}")
        elif event == "camera_ready":
            self._log_signal.emit("CAM", "Kamera bereit.")

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
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Smart Home", f"Fehler: {e}")

    def _open_face_panel(self):
        try:
            from vadox.ui.face_panel import FacePanel
            dlg = FacePanel(self)
            dlg.friend_reaction.connect(self._on_friend_reaction)
            dlg.exec()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Gesichtserkennung",
                f"Fehler beim Laden:\n{e}\n\nBitte sicherstellen dass OpenCV installiert ist:\npip install opencv-python deepface")

    def _on_friend_reaction(self, emotion: str, message: str):
        """Vadox reagiert als bester Freund — spricht Frage aus, hört dann automatisch zu."""
        try:
            self._log_signal.emit("CAM", f"Freund-Reaktion: {emotion}")
        except Exception:
            pass
        try:
            self._add_chat_bubble(f"💙 {message}", is_user=False)
        except Exception as e:
            print(f"[FriendReaction] chat_bubble Fehler: {e}")
        try:
            import threading
            def _speak():
                try:
                    # Nach dem Sprechen → Mikrofon automatisch aktivieren
                    self._tts.speak(message, on_done=self._friend_reaction_listen)
                except Exception as e:
                    print(f"[FriendReaction] TTS Fehler: {e}")
            threading.Thread(target=_speak, daemon=True).start()
        except Exception as e:
            print(f"[FriendReaction] Thread Fehler: {e}")

    def _friend_reaction_listen(self):
        """Nach der Freund-Frage: Mikrofon automatisch aktivieren (kein Wake-Word nötig)."""
        # Im UI-Thread ausführen
        QTimer.singleShot(300, self._do_friend_listen)

    def _do_friend_listen(self):
        """Mikrofon aktivieren — Antwort des Nutzers aufnehmen."""
        if self._listening:
            return
        self._log_signal.emit("CAM", "Warte auf Antwort...")
        self._update_wake_indicator(True, active=True)
        self._listening = True
        self._mic_btn.setStyleSheet(self._mic_style(True))
        self._mic_status_lbl.setText("● ANTWORTE EINFACH...")
        self._mic_status_lbl.setStyleSheet(f"color:#ff6ec7; font-size:10px; letter-spacing:1px; background:transparent;")
        self._waveform.set_active(True)
        self._stt.listen_once(
            on_result=lambda t: self._mic_result_signal.emit(t),
            on_error=lambda e: self._mic_error_signal.emit(e),
        )

    def _update_wake_indicator(self, enabled: bool, active: bool = False):
        """Aktualisiert den Wake-Word Indikator in der Titelleiste."""
        if hasattr(self, '_wake_dot'):
            if not enabled:
                self._wake_dot.setStyleSheet("background:#0a3a5a; border-radius:5px;")
                self._wake_lbl.setText("WAKE-WORD AUS")
                self._wake_lbl.setStyleSheet("color:#0a3a5a; font-size:9px; background:transparent;")
            elif active:
                self._wake_dot.setStyleSheet(f"background:{AMBER}; border-radius:5px;")
                self._wake_lbl.setText("HÖRT ZU...")
                self._wake_lbl.setStyleSheet(f"color:{AMBER}; font-size:9px; background:transparent;")
            else:
                self._wake_dot.setStyleSheet(f"background:{GREEN}; border-radius:5px;")
                self._wake_lbl.setText("HEY JARVIS")
                self._wake_lbl.setStyleSheet(f"color:{GREEN}; font-size:9px; background:transparent;")

    def _apply_settings(self, cfg: dict):
        provider = cfg.get("provider", "claude")
        key      = cfg.get("api_key", "")
        model    = cfg.get("model", "claude-sonnet-4-6")
        voice    = cfg.get("voice", "de-DE-KatjaNeural")

        self._tts = TTSEngine(voice=voice)

        if key:
            self._api_input.setText(key)
            self._ai = AIEngine(provider=provider, api_key=key, model=model)
            self._log.log("NET", f"KI gewechselt: {provider.upper()} / {model}")
            self._add_ai_bubble(f"Einstellungen gespeichert. Ich nutze jetzt {provider.upper()} mit dem Modell {model}.")

    # ── Uhr ────────────────────────────────────────────────────────────────────
    def _start_clock(self):
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        now = datetime.now()
        h = now.hour % 12 or 12
        ampm = "AM" if now.hour < 12 else "PM"
        t = f"{h:02d}:{now.minute:02d}:{now.second:02d} {ampm}"
        self._clock_lbl.setText(t)

    # ── System Stats ──────────────────────────────────────────────────────────
    def _on_stats(self, stats: dict):
        self._update_card("CPU", f"{int(stats['cpu'])}%", stats['cpu'])
        self._update_card("MEM", f"{int(stats['mem'])}%", stats['mem'])
        self._update_card("NET", f"{stats['net_kb']}KB", min(stats['net_kb'] / 1000 * 100, 100))
        self._update_card("GPU", f"{int(stats['gpu'])}%", stats['gpu'])
        self._update_card("DISK", f"{int(stats['disk'])}%", stats['disk'])

        if "UP TIME" in self._sys_rows:
            self._sys_rows["UP TIME"].setText(stats['uptime'])
        if "PROZESSE" in self._sys_rows:
            self._sys_rows["PROZESSE"].setText(str(stats['procs']))
        if "NUTZER" in self._sys_rows:
            self._sys_rows["NUTZER"].setText(stats['user'])

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

    # ── KI initialisieren ─────────────────────────────────────────────────────
    def _init_ai(self):
        key = self._api_input.text().strip()
        if not key:
            self._log.log("ERR", "Kein API-Key eingegeben.")
            return
        cfg = settings.load()
        provider = cfg.get("provider", "claude")
        model    = cfg.get("model", "claude-sonnet-4-6")
        self._ai = AIEngine(provider=provider, api_key=key, model=model)
        settings.set_value("api_key", key)
        self._log.log("NET", "Claude API verbunden. Key gespeichert.")
        self._log.log("AI", "Vadox ist bereit.")

        # Personalisierte Begrüßung
        mem = memory.load()
        name = mem.get("user_name") or settings.get("user_name", "")
        count = mem.get("conversation_count", 0)
        if name and count > 1:
            greeting = f"Willkommen zurück, {name}. Ich bin bereit. Wie kann ich dir helfen?"
        elif name:
            greeting = f"Hallo {name}, ich bin Vadox, dein KI-Assistent. Wie kann ich dir helfen?"
        else:
            greeting = "Verbindung hergestellt. Ich bin Vadox, dein KI-Assistent. Wie kann ich dir helfen?"
        self._add_ai_bubble(greeting)

    # ── Chat ──────────────────────────────────────────────────────────────────
    def _send_message(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self._add_user_bubble(text)
        if self._ai is None:
            self._add_ai_bubble("Bitte zuerst den API-Key eingeben und auf Verbinden klicken.")
            return
        self._log.log("AI", f"Verarbeite: {text[:40]}...")
        self._current_ai_bubble = None
        self._full_ai_response = ""
        self._ai.chat(
            text,
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
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, bubble)
        self._scroll_to_bottom()
        return bubble

    def _on_chat_chunk(self, chunk: str):
        if self._current_ai_bubble is None:
            self._current_ai_bubble = self._add_ai_bubble("")
        self._current_ai_bubble.append_text(chunk)
        self._full_ai_response += chunk
        self._scroll_to_bottom()

    def _on_tool_use(self, tool_name: str):
        tool_labels = {
            "get_weather": "Wetterdaten abrufen",
            "web_search": "Websuche durchführen",
            "news_search": "Nachrichten suchen",
            "search_files": "Dateien suchen",
            "list_directory": "Verzeichnis lesen",
            "read_file": "Datei lesen",
            "create_file": "Datei erstellen",
            "delete_file": "Datei löschen",
            "take_screenshot": "Screenshot machen",
            "open_application": "Anwendung öffnen",
            "open_url": "Webseite öffnen",
            "get_system_info": "Systeminfo abrufen",
        }
        label = tool_labels.get(tool_name, tool_name)
        self._log.log("SYS", f"Tool aktiv: {label}...")
        if self._current_ai_bubble is None:
            self._current_ai_bubble = self._add_ai_bubble(f"[ {label}... ]")
        else:
            self._current_ai_bubble.append_text(f"\n[ {label}... ]")
        self._scroll_to_bottom()

    def _on_chat_done(self, full_response: str):
        self._log.log("AI", "Antwort erhalten.")
        self._set_speaking(True)
        self._tts.speak(full_response, on_done=lambda: self._tts_done_signal.emit())

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self._chat_scroll.verticalScrollBar().setValue(
            self._chat_scroll.verticalScrollBar().maximum()
        ))

    # ── Mikrofon ──────────────────────────────────────────────────────────────
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
                background:{BG_CARD}; border:1px solid #1a3a5a;
                color:{CYAN_DIM}; font-size:16px; border-radius:10px;
            }}
            QPushButton:hover {{ border:1px solid {CYAN}; }}
        """

    def _toggle_mic(self):
        if self._listening:
            return
        self._listening = True
        self._mic_btn.setStyleSheet(self._mic_style(True))
        self._mic_status_lbl.setText("● HÖRT ZU...")
        self._mic_status_lbl.setStyleSheet(f"color:{PINK}; font-size:10px; letter-spacing:1px; background:transparent;")
        self._waveform.set_active(True)
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

    def _reset_mic(self):
        self._listening = False
        self._mic_btn.setStyleSheet(self._mic_style(False))
        self._mic_status_lbl.setText("● MIKROFON BEREIT")
        self._mic_status_lbl.setStyleSheet(f"color:{GREEN}; font-size:10px; letter-spacing:1px; background:transparent;")
        self._waveform.set_active(False)

    # ── Stimme ────────────────────────────────────────────────────────────────
    def _set_speaking(self, speaking: bool):
        self._speaking = speaking
        self._ring.set_state(speaking=speaking)
        if speaking:
            self._wave_state.setText("SPRICHT")
            self._wave_state.setStyleSheet(f"color:{CYAN}; font-size:9px; background:transparent;")
            self._waveform.set_active(True)
        else:
            self._wave_state.setText("BEREIT")
            self._wave_state.setStyleSheet(f"color:{CYAN_DIM}; font-size:9px; background:transparent;")
            if not self._listening:
                self._waveform.set_active(False)

    # ── Keyboard ──────────────────────────────────────────────────────────────
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif event.key() == Qt.Key.Key_F4:
            pass
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self._monitor.stop()
        super().closeEvent(event)
