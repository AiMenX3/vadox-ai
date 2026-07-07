# -*- mode: python ; coding: utf-8 -*-
"""
VADOX Build-Spec — macOS (.app Bundle)
Alle Module: Kamera (cv2/deepface), ElevenLabs, TTS, STT,
PDF-Analyse, Telegram, Selbstentwicklung, System-Steuerung usw.
"""
import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

block_cipher = None

# ── cv2 vollständig sammeln ───────────────────────────────────────────────────
cv2_datas, cv2_binaries, cv2_hiddenimports = collect_all('cv2')

# ── sounddevice ──────────────────────────────────────────────────────────────
sd_datas, sd_binaries, sd_hiddenimports = collect_all('sounddevice')

# ── PyMuPDF (fitz) ───────────────────────────────────────────────────────────
fitz_datas, fitz_binaries, fitz_hiddenimports = collect_all('fitz')

# ── yt-dlp ───────────────────────────────────────────────────────────────────
ytdlp_datas, ytdlp_binaries, ytdlp_hiddenimports = collect_all('yt_dlp')

# ── edge-tts ─────────────────────────────────────────────────────────────────
edgetss_datas, edgetss_binaries, edgetss_hiddenimports = collect_all('edge_tts')

# ── Alle datas kombinieren ────────────────────────────────────────────────────
all_datas = (
    cv2_datas + sd_datas + fitz_datas + ytdlp_datas + edgetss_datas +
    [
        ('vadox/ui',    'vadox/ui'),
        ('vadox/core',  'vadox/core'),
        ('vadox/tools', 'vadox/tools'),
    ]
)

# Assets einbinden falls vorhanden
if Path('assets').exists():
    all_datas.append(('assets', 'assets'))

# ── OpenWakeWord Modelle ──────────────────────────────────────────────────────
import openwakeword as _oww
_oww_models_src = str(Path(_oww.__file__).parent / "resources" / "models")
all_datas.append((_oww_models_src, "openwakeword/resources/models"))

all_binaries = cv2_binaries + sd_binaries + fitz_binaries + ytdlp_binaries + edgetss_binaries

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=[
        # ── PyQt6 ────────────────────────────────────────────────────────────
        'PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui',
        'PyQt6.QtNetwork', 'PyQt6.sip',

        # ── KI-Anbieter ───────────────────────────────────────────────────────
        'anthropic', 'anthropic._streaming', 'anthropic.types',
        'openai', 'openai._streaming',
        'google.generativeai',

        # ── ElevenLabs ────────────────────────────────────────────────────────
        'elevenlabs', 'elevenlabs.client', 'elevenlabs.types',

        # ── TTS ───────────────────────────────────────────────────────────────
        'edge_tts', 'edge_tts.communicate',
        'sounddevice', 'soundfile', 'cffi', '_cffi_backend',
        'pygame', 'pygame.mixer',

        # ── STT ───────────────────────────────────────────────────────────────
        'speech_recognition',
        'pyaudio',

        # ── Kamera / Face ─────────────────────────────────────────────────────
        'cv2',
        'deepface', 'deepface.DeepFace',
        'deepface.core', 'deepface.core.detector',
        'deepface.core.recognition',
        'deepface.detectors',
        'deepface.models',
        'tensorflow', 'tensorflow.python',
        'tf_keras', 'keras',
        'numpy', 'numpy.core', 'numpy.core._multiarray_umath',

        # ── Wake-Word ─────────────────────────────────────────────────────────
        'openwakeword', 'openwakeword.model', 'openwakeword.utils',
        'onnxruntime', 'onnxruntime.capi',

        # ── PDF-Analyse ───────────────────────────────────────────────────────
        'fitz', 'pymupdf',

        # ── Office / Präsentationen ───────────────────────────────────────────
        'pptx', 'pptx.util', 'pptx.dml.color',
        'pptx.enum.text', 'pptx.oxml.ns',
        'lxml', 'lxml.etree', 'lxml._elementpath',
        'zipfile',

        # ── System-Steuerung (plattformübergreifend) ─────────────────────────
        'psutil', 'pyperclip', 'ctypes',

        # ── Netzwerk / Web ────────────────────────────────────────────────────
        'requests', 'requests.adapters', 'requests.auth',
        'ddgs', 'httpx', 'httpcore',
        'urllib3', 'certifi',

        # ── E-Mail ────────────────────────────────────────────────────────────
        'imaplib', 'smtplib', 'email', 'email.header',
        'email.mime.text', 'email.mime.multipart',
        'exchangelib', 'exchangelib.autodiscover',

        # ── Kalender ──────────────────────────────────────────────────────────
        'caldav', 'icalendar', 'vobject',

        # ── Browser ───────────────────────────────────────────────────────────
        'playwright', 'playwright.sync_api', 'playwright.async_api',

        # ── YouTube ───────────────────────────────────────────────────────────
        'yt_dlp', 'yt_dlp.extractor', 'yt_dlp.downloader',

        # ── Spotify ───────────────────────────────────────────────────────────
        'spotipy',

        # ── Smart Home ────────────────────────────────────────────────────────
        'flask', 'flask.cli', 'werkzeug', 'werkzeug.serving',
        'qrcode', 'qrcode.image.pil',

        # ── Bildverarbeitung ──────────────────────────────────────────────────
        'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont',
        'pyautogui',

        # ── Vadox Module ──────────────────────────────────────────────────────
        'vadox.core.ai_engine',
        'vadox.core.tts_engine',
        'vadox.core.stt_engine',
        'vadox.core.tool_definitions',
        'vadox.core.tool_executor',
        'vadox.core.memory',
        'vadox.core.settings',
        'vadox.core.face_engine',
        'vadox.core.dynamic_tools',
        'vadox.core.user_rules',
        'vadox.core.feedback',
        'vadox.core.briefing',
        'vadox.core.agent_scheduler',
        'vadox.tools.weather',
        'vadox.tools.search',
        'vadox.tools.files',
        'vadox.tools.pc_control',
        'vadox.tools.email_tool',
        'vadox.tools.calendar_tool',
        'vadox.tools.presentation',
        'vadox.tools.browser',
        'vadox.tools.whatsapp',
        'vadox.tools.screen_ai',
        'vadox.tools.youtube',
        'vadox.tools.flights',
        'vadox.tools.gaming',
        'vadox.tools.system_control',
        'vadox.tools.smarthome',
        'vadox.tools.translator',
        'vadox.tools.image_fetcher',
        'vadox.tools.telegram_bot',
        'vadox.tools.pdf_analyzer',
        'vadox.tools.spotify',
        'vadox.tools.autostart',
        'vadox.ui.main_window',
        'vadox.ui.settings_panel',
        'vadox.ui.face_panel',

        # ── Standard-Bibliotheken ─────────────────────────────────────────────
        'asyncio', 'json', 'base64', 'threading', 'queue',
        'socket', 'io', 'os', 'sys', 'pathlib', 'datetime',
        'subprocess', 'shutil', 'zipfile', 'tempfile', 'importlib',
        'importlib.util', 'importlib.machinery',
        're', 'struct', 'traceback', 'logging', 'hashlib',

    ] + cv2_hiddenimports + sd_hiddenimports + fitz_hiddenimports
      + ytdlp_hiddenimports + edgetss_hiddenimports,

    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook_macos.py'],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'pandas',
        'notebook', 'jupyter', 'IPython',
        'test', 'tests', 'unittest',
        # Windows-spezifisch ausschließen
        'pycaw', 'comtypes', 'winreg',
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Vadox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,          # macOS: Drag&Drop Unterstützung
    target_arch=None,             # None = Universal (Intel + Apple Silicon)
    codesign_identity=None,       # Für kostenpflichtigen Developer-Account eintragen
    entitlements_file='entitlements.plist',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=['cv2*.so', '_cv2*.so', 'Qt6*.dylib'],
    name='Vadox',
)

# macOS .app Bundle
app = BUNDLE(
    coll,
    name='Vadox.app',
    icon='assets/icon.icns' if Path('assets/icon.icns').exists() else None,
    bundle_identifier='ai.vadox.app',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDisplayName': 'Vadox',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSMicrophoneUsageDescription': 'Vadox benötigt das Mikrofon für Spracheingabe und Hey-Jarvis Wake-Word.',
        'NSCameraUsageDescription': 'Vadox benötigt die Kamera für die Gesichtserkennung und KI-Freund-Funktion.',
        'NSAppleEventsUsageDescription': 'Vadox nutzt AppleScript für Systemsteuerung (Lautstärke, Autostart).',
        'LSUIElement': False,
    },
)
