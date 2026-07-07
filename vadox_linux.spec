# -*- mode: python ; coding: utf-8 -*-
"""
VADOX Build-Spec — Linux
"""
import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None

cv2_datas, cv2_binaries, cv2_hiddenimports       = collect_all('cv2')
sd_datas, sd_binaries, sd_hiddenimports           = collect_all('sounddevice')
fitz_datas, fitz_binaries, fitz_hiddenimports     = collect_all('fitz')
ytdlp_datas, ytdlp_binaries, ytdlp_hiddenimports = collect_all('yt_dlp')
edgetss_datas, edgetss_binaries, edgetss_hiddenimports = collect_all('edge_tts')

all_datas = (
    cv2_datas + sd_datas + fitz_datas + ytdlp_datas + edgetss_datas +
    [
        ('vadox/ui',    'vadox/ui'),
        ('vadox/core',  'vadox/core'),
        ('vadox/tools', 'vadox/tools'),
    ]
)

if Path('assets').exists():
    all_datas.append(('assets', 'assets'))

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
        'PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui',
        'PyQt6.QtNetwork', 'PyQt6.sip',
        'anthropic', 'anthropic._streaming', 'anthropic.types',
        'openai', 'openai._streaming',
        'google.generativeai',
        'elevenlabs', 'elevenlabs.client', 'elevenlabs.types',
        'edge_tts', 'edge_tts.communicate',
        'sounddevice', 'soundfile', 'cffi', '_cffi_backend',
        'pygame', 'pygame.mixer',
        'speech_recognition', 'pyaudio',
        'cv2',
        'deepface', 'deepface.DeepFace',
        'deepface.core', 'deepface.core.detector',
        'deepface.detectors', 'deepface.models',
        'tensorflow', 'tensorflow.python',
        'tf_keras', 'keras',
        'numpy', 'numpy.core', 'numpy.core._multiarray_umath',
        'openwakeword', 'openwakeword.model', 'openwakeword.utils',
        'onnxruntime', 'onnxruntime.capi',
        'fitz', 'pymupdf',
        'pptx', 'pptx.util', 'pptx.dml.color',
        'lxml', 'lxml.etree', 'lxml._elementpath',
        'psutil', 'pyperclip', 'ctypes',
        'requests', 'requests.adapters',
        'ddgs', 'httpx', 'httpcore', 'urllib3', 'certifi',
        'imaplib', 'smtplib', 'email', 'email.header',
        'exchangelib', 'exchangelib.autodiscover',
        'caldav', 'icalendar', 'vobject',
        'playwright', 'playwright.sync_api',
        'yt_dlp', 'yt_dlp.extractor', 'yt_dlp.downloader',
        'spotipy',
        'flask', 'flask.cli', 'werkzeug',
        'PIL', 'PIL.Image', 'PIL.ImageDraw',
        'pyautogui',
        'vadox.core.ai_engine', 'vadox.core.tts_engine', 'vadox.core.stt_engine',
        'vadox.core.tool_definitions', 'vadox.core.tool_executor',
        'vadox.core.memory', 'vadox.core.settings', 'vadox.core.face_engine',
        'vadox.core.dynamic_tools', 'vadox.core.user_rules',
        'vadox.core.feedback', 'vadox.core.briefing', 'vadox.core.agent_scheduler',
        'vadox.tools.weather', 'vadox.tools.search', 'vadox.tools.files',
        'vadox.tools.pc_control', 'vadox.tools.email_tool', 'vadox.tools.calendar_tool',
        'vadox.tools.presentation', 'vadox.tools.browser', 'vadox.tools.whatsapp',
        'vadox.tools.screen_ai', 'vadox.tools.youtube', 'vadox.tools.flights',
        'vadox.tools.gaming', 'vadox.tools.system_control', 'vadox.tools.smarthome',
        'vadox.tools.translator', 'vadox.tools.image_fetcher',
        'vadox.tools.telegram_bot', 'vadox.tools.pdf_analyzer',
        'vadox.tools.spotify', 'vadox.tools.autostart',
        'vadox.ui.main_window', 'vadox.ui.settings_panel', 'vadox.ui.face_panel',
        'asyncio', 'json', 'base64', 'threading', 'queue',
        'socket', 'io', 'os', 'sys', 'pathlib', 'datetime',
        'subprocess', 'shutil', 'zipfile', 'tempfile', 'importlib',
        're', 'struct', 'traceback', 'logging', 'hashlib',
    ] + cv2_hiddenimports + sd_hiddenimports + fitz_hiddenimports
      + ytdlp_hiddenimports + edgetss_hiddenimports,

    hookspath=[],
    runtime_hooks=['runtime_hook_linux.py'],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'pandas',
        'notebook', 'jupyter', 'IPython',
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
    strip=False,
    upx=True,
    console=False,
    cipher=block_cipher,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=['cv2*.so', '_cv2*.so'],
    name='Vadox',
)
