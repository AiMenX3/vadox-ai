# -*- coding: utf-8 -*-
"""
PyInstaller Runtime Hook — wird vor dem Start von main.py ausgeführt.
Fixes: cv2 DLL-Pfade, deepface Modell-Cache, sys.path für custom tools.
"""
import sys
import os
from pathlib import Path

# ── 1. Bundle-Basis ermitteln ─────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE = Path(sys._MEIPASS)
else:
    BASE = Path(__file__).parent

# ── 2. cv2 DLL-Pfad setzen (Windows Kamera-Fix) ──────────────────────────────
# OpenCV sucht seine DLLs über PATH — wir stellen sicher dass der Bundle-Ordner zuerst kommt
cv2_dir = BASE / 'cv2'
if cv2_dir.exists():
    os.environ['PATH'] = str(cv2_dir) + os.pathsep + os.environ.get('PATH', '')

# Direkt im Bundle-Root auch prüfen (PyInstaller packt manchmal so)
os.environ['PATH'] = str(BASE) + os.pathsep + os.environ.get('PATH', '')

# ── 3. DeepFace Modell-Cache auf ~/.deepface zeigen ──────────────────────────
# DeepFace lädt Modelle beim ersten Start in diesen Ordner
deepface_home = Path.home() / '.deepface'
deepface_home.mkdir(parents=True, exist_ok=True)
os.environ['DEEPFACE_HOME'] = str(deepface_home)

# ── 4. TensorFlow Warnungen unterdrücken (saubereres Log) ─────────────────────
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# ── 5. Vadox Custom Tools Pfad ────────────────────────────────────────────────
custom_tools = Path.home() / '.vadox' / 'custom_tools'
custom_tools.mkdir(parents=True, exist_ok=True)
if str(custom_tools) not in sys.path:
    sys.path.insert(0, str(custom_tools))

# ── 6. Pygame Audio ohne Display initialisieren ───────────────────────────────
os.environ.setdefault('SDL_AUDIODRIVER', 'directsound')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

# ── 7. openwakeword custom_verifier_model mocken ─────────────────────────────
# custom_verifier_model.py braucht scipy + sklearn, die im Bundle fehlen.
# Wir nutzen kein Custom-Modell — einfacher Stub verhindert den Import-Fehler.
import types as _types, sys as _sys

def _stub_module(name, **attrs):
    m = _types.ModuleType(name)
    m.__dict__.update(attrs)
    _sys.modules[name] = m
    return m

# Scipy komplett stubben (wird von sklearn/openwakeword gebraucht)
_scipy = _stub_module('scipy')
for _sub in [
    'scipy._lib', 'scipy._lib._ccallback', 'scipy._lib._util',
    'scipy.sparse', 'scipy.sparse.linalg', 'scipy.sparse.csgraph',
    'scipy.special', 'scipy.special._ufuncs',
    'scipy.linalg', 'scipy.optimize', 'scipy.integrate',
    'scipy.stats', 'scipy.signal', 'scipy.interpolate',
    'scipy.io', 'scipy.fft',
]:
    _sub_m = _stub_module(_sub)
    _sub_m.LowLevelCallable = object
    # Submodul auch als Attribut am Parent registrieren
    _parts = _sub.split('.')
    if len(_parts) > 1:
        _parent = _sys.modules.get('.'.join(_parts[:-1]))
        if _parent:
            setattr(_parent, _parts[-1], _sub_m)

# sklearn stubben (wird von custom_verifier_model gebraucht)
for _sk in [
    'sklearn', 'sklearn.base', 'sklearn.utils', 'sklearn.utils._chunking',
    'sklearn.utils._param_validation', 'sklearn.pipeline',
    'sklearn.preprocessing', 'sklearn.linear_model',
]:
    _stub_module(_sk)

# openwakeword.custom_verifier_model direkt stubben
_oww_cvm = _stub_module('openwakeword.custom_verifier_model')
_oww_cvm.CustomVerifierModel = object
_oww_cvm.train_custom_verifier = lambda *a, **kw: None
