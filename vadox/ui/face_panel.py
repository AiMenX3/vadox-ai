"""
Vadox Face Panel — Gesichtserkennung + Emotions-Analyse + Bester-Freund Modus
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QImage
import threading

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
PINK  = "#ff6ec7"


def _lbl(text, size=10, color=TEXT, bold=False):
    l = QLabel(text)
    l.setFont(QFont("Courier New", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    l.setStyleSheet(f"color:{color}; background:transparent;")
    return l


class CameraWorker(QThread):
    frame_ready = pyqtSignal(object)
    stopped = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._running = False

    def run(self):
        try:
            import cv2
        except ImportError:
            self.error.emit("OpenCV nicht installiert.")
            self.stopped.emit()
            return
        self._running = True
        import sys, platform as _pl
        if _pl.system() == "Windows" and not getattr(sys, 'frozen', False):
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.error.emit("Keine Webcam gefunden oder bereits in Benutzung.")
            self.stopped.emit()
            return
        while self._running:
            ret, frame = cap.read()
            if ret:
                try:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    self.frame_ready.emit(rgb)
                except Exception:
                    pass
            self.msleep(66)  # ~15fps
        cap.release()
        self.stopped.emit()

    def stop(self):
        self._running = False


class AnalysisWorker(QThread):
    """Analysiert einen einzelnen Frame im Hintergrund."""
    result_ready = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, frame):
        super().__init__()
        self._frame = frame

    def run(self):
        try:
            from vadox.core.face_engine import analyze_single_frame
            import cv2
            bgr = cv2.cvtColor(self._frame, cv2.COLOR_RGB2BGR)
            result = analyze_single_frame(bgr)
            if result:
                self.result_ready.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class FacePanel(QDialog):
    # Signal nach main_window für "Bester Freund" Reaktion
    friend_reaction = pyqtSignal(str, str)  # (emotion, message)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VADOX — AI Freund")
        self.setMinimumSize(720, 580)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background:{BG}; }}")
        self._cam_worker = None
        self._analysis_worker = None
        self._frame_count = 0
        self._analyze_every = 20      # Alle 20 Frames (~1.3 Sek) analysieren
        self._analyzing = False
        self._last_reacted_emotion = ""
        self._last_reaction_frame = -999
        self._reaction_cooldown_frames = 300  # Mindestens 300 Frames (~20 Sek) zwischen Reaktionen
        self._build()
        self._load_profiles()

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
        b_lay.addWidget(_lbl("AI FREUND  ·  EMOTIONS-ANALYSE", size=13, color=CYAN, bold=True))
        b_lay.addStretch()
        b_lay.addWidget(_lbl("● BESTER-FREUND MODUS", size=9, color=PINK))
        b_lay.addSpacing(16)
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"background:transparent; color:{TEXTD}; font-size:14px; border:none;")
        close_btn.clicked.connect(self._on_close)
        b_lay.addWidget(close_btn)
        lay.addWidget(bar)

        # Haupt-Inhalt
        content_widget = QWidget()
        content = QHBoxLayout(content_widget)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # ── Links: Kamera + Emotions-Anzeige ─────────────────────────────────
        self._left = QWidget()
        self._left.setStyleSheet(f"background:{BG};")
        self._left.setFixedWidth(390)
        l_lay = QVBoxLayout(self._left)
        l_lay.setContentsMargins(16, 16, 8, 16)
        l_lay.setSpacing(12)

        # Kamera-Vorschau
        cam_frame = QFrame()
        cam_frame.setFixedSize(358, 240)
        cam_frame.setStyleSheet(f"background:#020810; border:1px solid {BORDER}; border-radius:10px;")
        cam_inner = QVBoxLayout(cam_frame)
        cam_inner.setContentsMargins(4, 4, 4, 4)
        self._cam_lbl = QLabel()
        self._cam_lbl.setFixedSize(348, 230)
        self._cam_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cam_lbl.setText("Kamera nicht aktiv")
        self._cam_lbl.setStyleSheet(f"color:{TEXTD}; font-family:'Courier New'; font-size:10px; background:transparent;")
        cam_inner.addWidget(self._cam_lbl)
        l_lay.addWidget(cam_frame)

        # Kamera-Button
        self._cam_btn = QPushButton("▶  Kamera starten")
        self._cam_btn.setFixedHeight(34)
        self._cam_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cam_btn.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self._cam_btn.setStyleSheet(f"""
            QPushButton {{ background:#0a2a4a; border:1px solid {CYAN};
                color:{CYAN}; border-radius:7px; }}
            QPushButton:hover {{ background:#0f3a60; }}
        """)
        self._cam_btn.clicked.connect(self._toggle_camera)
        l_lay.addWidget(self._cam_btn)

        # Analyse-Status
        self._analysis_lbl = _lbl("Warte auf erstes Bild...", size=9, color=TEXTD)
        l_lay.addWidget(self._analysis_lbl)

        # Emotions-Anzeige — groß + auffällig
        emo_frame = QFrame()
        emo_frame.setStyleSheet(f"background:{CARD}; border:1px solid {BORDER}; border-radius:10px;")
        emo_lay = QVBoxLayout(emo_frame)
        emo_lay.setContentsMargins(16, 12, 16, 12)
        emo_lay.setSpacing(6)

        emo_top = QHBoxLayout()
        self._emo_icon = QLabel("😐")
        self._emo_icon.setFont(QFont("Segoe UI Emoji", 32))
        self._emo_icon.setStyleSheet("background:transparent;")
        emo_top.addWidget(self._emo_icon)
        emo_top.addSpacing(12)

        emo_text = QVBoxLayout()
        self._emo_lbl = QLabel("Warte auf Analyse...")
        self._emo_lbl.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
        self._emo_lbl.setStyleSheet(f"color:{CYAN}; background:transparent;")
        emo_text.addWidget(self._emo_lbl)

        self._emo_conf = _lbl("Konfidenz: –", size=9, color=TEXTD)
        emo_text.addWidget(self._emo_conf)
        emo_top.addLayout(emo_text)
        emo_top.addStretch()
        emo_lay.addLayout(emo_top)

        # Freund-Reaktion Anzeige
        self._friend_frame = QFrame()
        self._friend_frame.setStyleSheet(f"background:#050d1a; border:1px solid {PINK}; border-radius:8px;")
        self._friend_frame.hide()
        friend_lay = QHBoxLayout(self._friend_frame)
        friend_lay.setContentsMargins(12, 8, 12, 8)
        heart_lbl = QLabel("💙")
        heart_lbl.setFont(QFont("Segoe UI Emoji", 16))
        heart_lbl.setStyleSheet("background:transparent;")
        friend_lay.addWidget(heart_lbl)
        friend_lay.addSpacing(8)
        self._friend_msg = QLabel("")
        self._friend_msg.setFont(QFont("Courier New", 9))
        self._friend_msg.setStyleSheet(f"color:{PINK}; background:transparent;")
        self._friend_msg.setWordWrap(True)
        friend_lay.addWidget(self._friend_msg, stretch=1)
        emo_lay.addWidget(self._friend_frame)

        l_lay.addWidget(emo_frame)
        l_lay.addStretch()
        content.addWidget(self._left)

        # Trennlinie
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background:{BORDER};")
        content.addWidget(sep)

        # ── Rechts: Profile ───────────────────────────────────────────────────
        self._right = QWidget()
        self._right.setStyleSheet(f"background:{BG};")
        r_lay = QVBoxLayout(self._right)
        r_lay.setContentsMargins(16, 16, 16, 16)
        r_lay.setSpacing(12)

        r_lay.addWidget(_lbl("PROFILE VERWALTEN", size=10, color=CYAN, bold=True))
        r_lay.addWidget(_lbl(
            "Lege Profile an damit Vadox dich erkennt\nund personalisierten Freund-Modus aktiviert.",
            size=9, color=TEXTD
        ))

        # Neues Profil anlegen
        add_frame = QFrame()
        add_frame.setStyleSheet(f"background:{CARD}; border:1px solid {BORDER}; border-radius:8px;")
        add_lay = QVBoxLayout(add_frame)
        add_lay.setContentsMargins(12, 10, 12, 10)
        add_lay.setSpacing(8)
        add_lay.addWidget(_lbl("Neues Profil anlegen:", size=9, color=TEXTD))

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Name eingeben (z.B. Max)")
        self._name_input.setFixedHeight(32)
        self._name_input.setStyleSheet(f"""
            QLineEdit {{ background:{BG}; border:1px solid {BORDER}; color:{CYAN};
                font-family:'Courier New'; font-size:10px; border-radius:6px; padding:0 8px; }}
            QLineEdit:focus {{ border-color:{CYAN}; }}
        """)
        add_lay.addWidget(self._name_input)

        add_btn = QPushButton("📷  Foto aufnehmen & speichern")
        add_btn.setFixedHeight(32)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        add_btn.setStyleSheet(f"""
            QPushButton {{ background:#0a2a0a; border:1px solid {GREEN};
                color:{GREEN}; border-radius:6px; }}
            QPushButton:hover {{ background:#0f3a0f; }}
        """)
        add_btn.clicked.connect(self._add_profile)
        add_lay.addWidget(add_btn)

        self._add_status = _lbl("", size=9, color=GREEN)
        add_lay.addWidget(self._add_status)
        r_lay.addWidget(add_frame)

        r_lay.addWidget(_lbl("Gespeicherte Profile:", size=9, color=TEXTD))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{BG}; }}
            QScrollBar:vertical {{ width:4px; background:{BG}; }}
            QScrollBar::handle:vertical {{ background:{CYAN_D}; border-radius:2px; }}
        """)
        self._profiles_container = QWidget()
        self._profiles_container.setStyleSheet(f"background:{BG};")
        self._profiles_layout = QVBoxLayout(self._profiles_container)
        self._profiles_layout.setContentsMargins(0, 0, 0, 0)
        self._profiles_layout.setSpacing(4)
        scroll.setWidget(self._profiles_container)
        r_lay.addWidget(scroll, stretch=1)

        content.addWidget(self._right, stretch=1)
        lay.addWidget(content_widget, stretch=1)

        # Fußzeile
        foot = QFrame()
        foot.setFixedHeight(44)
        foot.setStyleSheet(f"background:#040c18; border-top:1px solid {BORDER};")
        f_lay = QHBoxLayout(foot)
        f_lay.setContentsMargins(20, 0, 20, 0)
        self._status_lbl = _lbl("Kamera nicht aktiv", size=9, color=TEXTD)
        f_lay.addWidget(self._status_lbl)
        f_lay.addStretch()
        close2 = QPushButton("Schließen")
        close2.setFixedHeight(32)
        close2.setCursor(Qt.CursorShape.PointingHandCursor)
        close2.setFont(QFont("Courier New", 10))
        close2.setStyleSheet(f"""
            QPushButton {{ background:{CARD}; border:1px solid {BORDER};
                color:{CYAN_D}; border-radius:6px; padding:0 16px; }}
            QPushButton:hover {{ border-color:{CYAN}; color:{CYAN}; }}
        """)
        close2.clicked.connect(self._on_close)
        f_lay.addWidget(close2)
        lay.addWidget(foot)

    # ── Kamera ────────────────────────────────────────────────────────────────
    def _toggle_camera(self):
        if self._cam_worker and self._cam_worker.isRunning():
            self._cam_worker.stop()
            self._cam_btn.setText("▶  Kamera starten")
            self._status_lbl.setText("Kamera gestoppt")
            self._status_lbl.setStyleSheet(f"color:{TEXTD}; background:transparent;")
        else:
            self._cam_btn.setText("⏳  Wird geladen...")
            self._cam_btn.setEnabled(False)
            self._analysis_lbl.setText("KI-Modell wird geladen (~15 Sek)...")
            self._analysis_lbl.setStyleSheet(f"color:{AMBER}; background:transparent;")
            # DeepFace vorab in Hintergrund laden damit erster Frame nicht crasht
            import threading
            threading.Thread(target=self._preload_deepface, daemon=True).start()

    def _preload_deepface(self):
        """Lädt DeepFace/TensorFlow einmal im Hintergrund vor dem Start."""
        steps = [
            "KI-Modell wird geladen...",
            "TensorFlow initialisiert...",
            "Gesichtserkennungs-Modell bereit...",
        ]
        import time
        for i, step in enumerate(steps):
            QTimer.singleShot(i * 800, lambda s=step: (
                self._analysis_lbl.setText(s),
                self._analysis_lbl.setStyleSheet(f"color:{AMBER}; background:transparent;")
            ))
        try:
            import numpy as np
            from vadox.core.face_engine import analyze_single_frame
            dummy = np.zeros((48, 48, 3), dtype=np.uint8)
            analyze_single_frame(dummy)  # einmal warm machen
        except Exception as e:
            print(f"[FacePanel] DeepFace Vorlade-Fehler (nicht kritisch): {e}")
        finally:
            QTimer.singleShot(0, self._start_camera_after_preload)

    def _start_camera_after_preload(self):
        self._cam_worker = CameraWorker()
        self._cam_worker.frame_ready.connect(self._on_frame)
        self._cam_worker.stopped.connect(self._on_cam_stopped)
        self._cam_worker.error.connect(self._on_cam_error)
        self._cam_worker.start()
        self._cam_btn.setText("⏹  Kamera stoppen")
        self._cam_btn.setEnabled(True)
        self._status_lbl.setText("● Kamera aktiv — Emotions-Analyse läuft")
        self._status_lbl.setStyleSheet(f"color:{GREEN}; background:transparent;")
        self._analysis_lbl.setText("Erste Analyse in Kürze...")
        self._analysis_lbl.setStyleSheet(f"color:{CYAN}; background:transparent;")

    def _on_frame(self, frame):
        # Frame im Kamera-Label anzeigen
        h, w, ch = frame.shape
        qimg = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        px = QPixmap.fromImage(qimg).scaled(
            348, 230,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._cam_lbl.setPixmap(px)
        self._cam_lbl.setText("")

        # Alle N Frames analysieren
        self._frame_count += 1
        if self._frame_count % self._analyze_every == 0 and not self._analyzing:
            self._run_analysis(frame)

    def _run_analysis(self, frame):
        """Startet DeepFace Analyse im Hintergrund-Thread."""
        self._analyzing = True
        self._analysis_worker = AnalysisWorker(frame)
        self._analysis_worker.result_ready.connect(self._on_analysis_result)
        self._analysis_worker.error.connect(self._on_analysis_error)
        self._analysis_worker.finished.connect(lambda: setattr(self, '_analyzing', False))
        self._analysis_worker.start()

    def _on_analysis_error(self, msg: str):
        self._analysis_lbl.setText(f"Analyse-Fehler: {msg[:60]}")
        self._analysis_lbl.setStyleSheet(f"color:{RED}; background:transparent;")

    def _on_analysis_result(self, result: dict):
        """Ergebnis im UI anzeigen + Freund-Reaktion auslösen."""
        try:
            emotion  = result.get("emotion", "neutral")
            label_de = result.get("label_de", "Neutral")
            icon     = result.get("icon", "😐")
            conf     = result.get("confidence", 0)

            self._emo_icon.setText(icon)
            self._emo_lbl.setText(label_de)
            self._emo_lbl.setStyleSheet(f"color:{self._emotion_color(emotion)}; background:transparent;")
            self._emo_conf.setText(f"Konfidenz: {conf:.0f}%")
            self._analysis_lbl.setText(f"Letzte Analyse: {label_de} ({conf:.0f}%)")
            self._analysis_lbl.setStyleSheet(f"color:{GREEN}; background:transparent;")

            NEGATIVE = {"sad", "angry", "fear", "disgust"}
            frames_since = self._frame_count - self._last_reaction_frame
            if (emotion in NEGATIVE and conf > 55
                    and frames_since > self._reaction_cooldown_frames):
                self._trigger_friend_reaction(emotion, label_de, icon)
        except Exception as e:
            print(f"[FacePanel] Analyse-Ergebnis Fehler: {e}")

    def _emotion_color(self, emotion: str) -> str:
        return {
            "happy":    GREEN,
            "neutral":  CYAN,
            "surprise": AMBER,
            "sad":      "#88aaff",
            "angry":    RED,
            "fear":     AMBER,
            "disgust":  "#ffaa44",
        }.get(emotion, CYAN)

    def _trigger_friend_reaction(self, emotion: str, label_de: str, icon: str):
        """Bester-Freund Reaktion auf negative Emotion."""
        try:
            import random
            from vadox.core.face_engine import FRIEND_REACTIONS
            reactions = FRIEND_REACTIONS.get(emotion, [])
            if not reactions:
                return
            msg = random.choice(reactions)
            self._last_reaction_frame = self._frame_count
            self._last_reacted_emotion = emotion

            self._friend_msg.setText(msg)
            self._friend_frame.show()
            QTimer.singleShot(8000, self._friend_frame.hide)

            # Signal an main_window — in try/except damit Crash nicht das Panel schließt
            try:
                self.friend_reaction.emit(emotion, msg)
            except Exception as e:
                print(f"[FacePanel] Signal-Fehler: {e}")
        except Exception as e:
            print(f"[FacePanel] Reaktion-Fehler: {e}")

    def _on_cam_stopped(self):
        self._cam_lbl.setText("Kamera nicht aktiv")
        self._cam_lbl.setPixmap(QPixmap())
        self._cam_btn.setText("▶  Kamera starten")
        self._status_lbl.setText("Kamera gestoppt")
        self._status_lbl.setStyleSheet(f"color:{TEXTD}; background:transparent;")

    def _on_cam_error(self, msg: str):
        self._cam_lbl.setText(f"Fehler:\n{msg}")
        self._cam_btn.setText("▶  Kamera starten")
        self._status_lbl.setText(msg)
        self._status_lbl.setStyleSheet(f"color:{RED}; background:transparent;")

    # ── Profile ───────────────────────────────────────────────────────────────
    def _add_profile(self):
        name = self._name_input.text().strip()
        if not name:
            self._add_status.setText("Bitte Namen eingeben.")
            self._add_status.setStyleSheet(f"color:{RED}; background:transparent;")
            return
        self._add_status.setText("Foto wird aufgenommen...")
        self._add_status.setStyleSheet(f"color:{AMBER}; background:transparent;")

        def _capture():
            from vadox.core.face_engine import capture_face_for_profile
            ok, msg = capture_face_for_profile(name)
            QTimer.singleShot(0, lambda: self._on_profile_saved(ok, msg, name))

        threading.Thread(target=_capture, daemon=True).start()

    def _on_profile_saved(self, ok: bool, msg: str, name: str):
        color = GREEN if ok else RED
        self._add_status.setText(msg)
        self._add_status.setStyleSheet(f"color:{color}; background:transparent;")
        if ok:
            self._name_input.clear()
            self._load_profiles()

    def _load_profiles(self):
        for i in reversed(range(self._profiles_layout.count())):
            item = self._profiles_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        from vadox.core.face_engine import get_profiles
        profiles = get_profiles()

        if not profiles:
            self._profiles_layout.addWidget(
                _lbl("Noch keine Profile angelegt.", size=9, color=TEXTD))
            return

        for name in profiles:
            card = QFrame()
            card.setStyleSheet(f"background:{CARD}; border:1px solid {BORDER}; border-radius:6px;")
            c_lay = QHBoxLayout(card)
            c_lay.setContentsMargins(12, 8, 12, 8)
            c_lay.addWidget(_lbl("👤", size=14))
            c_lay.addSpacing(6)
            c_lay.addWidget(_lbl(name, size=10, color=CYAN))
            c_lay.addStretch()
            del_btn = QPushButton("Löschen")
            del_btn.setFixedHeight(24)
            del_btn.setFixedWidth(70)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setFont(QFont("Courier New", 8))
            del_btn.setStyleSheet(f"""
                QPushButton {{ background:transparent; border:1px solid {RED};
                    color:{RED}; border-radius:4px; }}
                QPushButton:hover {{ background:#200a0a; }}
            """)
            del_btn.clicked.connect(lambda checked, n=name: self._delete_profile(n))
            c_lay.addWidget(del_btn)
            self._profiles_layout.addWidget(card)

        self._profiles_layout.addStretch()

    def _delete_profile(self, name: str):
        reply = QMessageBox.question(
            self, "Profil löschen?",
            f"Profil '{name}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from vadox.core.face_engine import delete_profile
            delete_profile(name)
            self._load_profiles()

    def update_emotion(self, emotion_data: dict):
        """Von außen aufrufbar (main_window Hintergrund-Engine)."""
        icon     = emotion_data.get("icon", "😐")
        label_de = emotion_data.get("label_de", "Neutral")
        emotion  = emotion_data.get("emotion", "neutral")
        self._emo_icon.setText(icon)
        self._emo_lbl.setText(label_de)
        self._emo_lbl.setStyleSheet(f"color:{self._emotion_color(emotion)}; background:transparent;")

    def _on_close(self):
        if self._cam_worker and self._cam_worker.isRunning():
            self._cam_worker.stop()
        self.accept()
