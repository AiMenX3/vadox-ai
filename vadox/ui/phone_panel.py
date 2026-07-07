from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QImage
from io import BytesIO

BG    = "#050d1a"
CARD  = "#071525"
BORDER= "#0a2540"
CYAN  = "#00c8ff"
CYAN_D= "#2a7aaa"
GREEN = "#00ff88"
TEXT  = "#5ab4d8"
TEXTD = "#3a8aaa"


def _lbl(text, size=10, color=TEXT, bold=False):
    l = QLabel(text)
    l.setFont(QFont("Courier New", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    l.setStyleSheet(f"color:{color}; background:transparent;")
    return l


class QRLoader(QThread):
    ready = pyqtSignal(object, str)  # (PIL.Image, url)

    def run(self):
        from vadox.core.phone_server import get_qr_image
        img, url = get_qr_image()
        self.ready.emit(img, url)


class PhonePanel(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VADOX — Phone Link")
        self.setFixedSize(440, 560)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background:{BG}; }}")
        self._build()
        self._start_server()

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
        b_lay.addWidget(_lbl("PHONE LINK", size=13, color=CYAN, bold=True))
        b_lay.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"background:transparent; color:{TEXTD}; font-size:14px; border:none;")
        close_btn.clicked.connect(self.reject)
        b_lay.addWidget(close_btn)
        lay.addWidget(bar)

        # Inhalt
        content = QFrame()
        content.setStyleSheet(f"background:{BG};")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(30, 30, 30, 30)
        c_lay.setSpacing(16)
        c_lay.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Status-Zeile
        status_row = QHBoxLayout()
        self._status_dot = QFrame()
        self._status_dot.setFixedSize(10, 10)
        self._status_dot.setStyleSheet(f"background:{TEXTD}; border-radius:5px;")
        self._status_lbl = _lbl("Server wird gestartet...", size=9, color=TEXTD)
        status_row.addWidget(self._status_dot)
        status_row.addSpacing(6)
        status_row.addWidget(self._status_lbl)
        status_row.addStretch()
        c_lay.addLayout(status_row)

        # QR-Code Bereich
        qr_frame = QFrame()
        qr_frame.setFixedSize(240, 240)
        qr_frame.setStyleSheet(f"""
            QFrame {{ background:{CARD}; border:2px solid {BORDER};
                     border-radius:12px; }}
        """)
        qr_inner = QVBoxLayout(qr_frame)
        qr_inner.setContentsMargins(12, 12, 12, 12)
        qr_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._qr_lbl = QLabel()
        self._qr_lbl.setFixedSize(210, 210)
        self._qr_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qr_lbl.setText("QR-Code wird geladen...")
        self._qr_lbl.setFont(QFont("Courier New", 9))
        self._qr_lbl.setStyleSheet(f"color:{TEXTD}; background:transparent;")
        qr_inner.addWidget(self._qr_lbl)
        c_lay.addWidget(qr_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

        # URL-Anzeige
        self._url_lbl = _lbl("http://...", size=9, color=CYAN_D)
        self._url_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._url_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        c_lay.addWidget(self._url_lbl)

        # Anleitung
        c_lay.addSpacing(8)
        steps = [
            "1.  Handy und PC im gleichen WLAN",
            "2.  QR-Code mit Kamera-App scannen",
            "3.  Vadox im Browser öffnen",
            "4.  Mit Vadox per Chat sprechen",
        ]
        for step in steps:
            c_lay.addWidget(_lbl(step, size=9, color=TEXTD))

        c_lay.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        self._copy_btn = QPushButton("URL kopieren")
        self._copy_btn.setEnabled(False)
        self._copy_btn.setFixedHeight(34)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.setFont(QFont("Courier New", 10))
        self._copy_btn.setStyleSheet(f"""
            QPushButton {{ background:{CARD}; border:1px solid {BORDER};
                color:{CYAN_D}; border-radius:7px; padding:0 14px; }}
            QPushButton:enabled:hover {{ border-color:{CYAN}; color:{CYAN}; }}
            QPushButton:disabled {{ color:{TEXTD}; }}
        """)
        self._copy_btn.clicked.connect(self._copy_url)
        btn_row.addWidget(self._copy_btn)

        close2 = QPushButton("Schließen")
        close2.setFixedHeight(34)
        close2.setCursor(Qt.CursorShape.PointingHandCursor)
        close2.setFont(QFont("Courier New", 10))
        close2.setStyleSheet(f"""
            QPushButton {{ background:#0a2a4a; border:1px solid {CYAN};
                color:{CYAN}; border-radius:7px; padding:0 14px; }}
            QPushButton:hover {{ background:#0f3a60; }}
        """)
        close2.clicked.connect(self.accept)
        btn_row.addWidget(close2)
        c_lay.addLayout(btn_row)

        lay.addWidget(content, stretch=1)
        self._current_url = ""

    def _start_server(self):
        from vadox.core import phone_server
        # Server starten (idempotent)
        phone_server.start(on_message=self._on_phone_message)

        # QR-Code laden
        loader = QRLoader(self)
        loader.ready.connect(self._on_qr_ready)
        loader.start()
        self._loader = loader  # Referenz halten

    def _on_qr_ready(self, pil_img, url: str):
        self._current_url = url
        self._url_lbl.setText(url)
        self._copy_btn.setEnabled(True)
        self._status_dot.setStyleSheet(f"background:{GREEN}; border-radius:5px;")
        self._status_lbl.setText(f"Server aktiv — warte auf Verbindung")
        self._status_lbl.setStyleSheet(f"color:{GREEN}; background:transparent;")

        # PIL-Image → QPixmap
        buf = BytesIO()
        pil_img.save(buf, format="PNG")
        buf.seek(0)
        qimg = QImage.fromData(buf.read())
        px = QPixmap.fromImage(qimg).scaled(
            210, 210,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._qr_lbl.setPixmap(px)
        self._qr_lbl.setText("")

    def _on_phone_message(self, message: str):
        """Nachricht vom Handy empfangen → an Vadox-Chat weiterleiten."""
        from vadox.core import phone_server
        parent = self.parent()
        if parent and hasattr(parent, "_send_message"):
            # Antwort-Callback registrieren
            original_add = parent._add_chat_bubble
            def _intercept(text, is_user=False):
                original_add(text, is_user)
                if not is_user:
                    phone_server.send_response(text)
            parent._add_chat_bubble = _intercept
            parent._send_message(message)

    def _copy_url(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._current_url)
        self._copy_btn.setText("Kopiert!")
        QTimer.singleShot(2000, lambda: self._copy_btn.setText("URL kopieren"))
