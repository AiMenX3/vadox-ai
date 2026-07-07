"""
Linux Runtime Hook — läuft vor main.py im AppImage/Bundle.
"""
import sys
import os
from pathlib import Path

if getattr(sys, 'frozen', False):
    BASE = Path(sys._MEIPASS)

    cv2_dir = BASE / 'cv2'
    if cv2_dir.exists():
        os.environ['PATH'] = str(cv2_dir) + os.pathsep + os.environ.get('PATH', '')

    os.environ['PATH'] = str(BASE) + os.pathsep + os.environ.get('PATH', '')
    os.environ['DEEPFACE_HOME'] = str(Path.home() / '.deepface')
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

    # Linux: Qt Plattform-Plugin (xcb oder wayland)
    qt_plugins = BASE / 'PyQt6' / 'Qt6' / 'plugins'
    if qt_plugins.exists():
        os.environ['QT_PLUGIN_PATH'] = str(qt_plugins)
