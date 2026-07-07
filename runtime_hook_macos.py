"""
macOS Runtime Hook — läuft vor main.py im App-Bundle.
Setzt Umgebungsvariablen und Pfade für PyInstaller frozen App.
"""
import sys
import os
from pathlib import Path

if getattr(sys, 'frozen', False):
    BASE = Path(sys._MEIPASS)

    # cv2 / OpenCV Bibliotheken finden
    cv2_dir = BASE / 'cv2'
    if cv2_dir.exists():
        os.environ['PATH'] = str(cv2_dir) + os.pathsep + os.environ.get('PATH', '')

    os.environ['PATH'] = str(BASE) + os.pathsep + os.environ.get('PATH', '')

    # DeepFace — Modelle im Home-Verzeichnis speichern (nicht im Bundle)
    os.environ['DEEPFACE_HOME'] = str(Path.home() / '.deepface')

    # TensorFlow — ruhige Ausgabe
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

    # macOS: Qt Plattform-Plugin
    qt_plugins = BASE / 'PyQt6' / 'Qt6' / 'plugins'
    if qt_plugins.exists():
        os.environ['QT_PLUGIN_PATH'] = str(qt_plugins)

    # macOS: Verhindert "This process is not trusted" für Eingabe-Monitoring
    os.environ['QT_MAC_WANTS_LAYER'] = '1'
