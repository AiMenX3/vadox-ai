"""
Vadox Wake-Word Engine — "Hey Jarvis" Erkennung
Nutzt openWakeWord (kostenlos, kein Account, läuft lokal)
"""
import sys
import threading
import numpy as np
from pathlib import Path
import logging
import os

# Log-Datei neben der EXE oder im App-Verzeichnis
_log_path = Path(sys.executable).parent / "vadox_wakeword.log" if getattr(sys, 'frozen', False) \
    else Path(__file__).parent.parent.parent / "vadox_wakeword.log"
logging.basicConfig(
    filename=str(_log_path),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)
_log = logging.getLogger("wake_word")

_thread: threading.Thread | None = None
_running = False
_on_detected_callback = None

WAKE_WORD_MODEL = "hey_jarvis_v0.1"
SENSITIVITY = 0.5

_AGC_TARGET_PEAK = 12000   # Ziel-Aussteuerung fuer openWakeWord (int16, max 32767)
_AGC_MAX_GAIN    = 16.0    # Deckel gegen Rauschverstaerkung bei sehr leisem Signal
_AGC_NOISE_FLOOR = 40      # Peaks darunter gelten als Stille, werden nicht verstaerkt


def _auto_gain(audio: np.ndarray) -> np.ndarray:
    """Hebt zu leise Mikrofon-Eingaben auf einen nutzbaren Pegel an, bevor sie
    ans Wake-Word-Modell gehen. Betrifft nicht nur macOS: leise USB-Mikrofone,
    Distanz zum Laptop oder niedrige System-Eingangslautstaerke tritt auf jeder
    Plattform auf und laesst openWakeWord sonst nie zuverlaessig erkennen."""
    peak = int(np.abs(audio).max())
    if peak < _AGC_NOISE_FLOOR:
        return audio
    gain = min(_AGC_MAX_GAIN, _AGC_TARGET_PEAK / peak)
    if gain <= 1.0:
        return audio
    boosted = audio.astype(np.float32) * gain
    return np.clip(boosted, -32768, 32767).astype(np.int16)


def _get_models_dir() -> str:
    """
    Gibt das Verzeichnis der ONNX-Modelle zurück.
    Im EXE-Modus liegen sie unter sys._MEIPASS/openwakeword/resources/models/
    Im Dev-Modus werden sie aus dem installierten Paket gelesen.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller EXE — Modelle sind im Bundle
        base = Path(sys._MEIPASS)
        candidates = [
            base / "openwakeword" / "resources" / "models",
            base / "resources" / "models",
            base / "models",
        ]
        for c in candidates:
            if c.exists():
                return str(c)
        # Fallback: aus installiertem Paket lesen (erfordert Paket im Bundle)
    # Dev-Modus oder Fallback
    import openwakeword
    pkg_dir = Path(openwakeword.__file__).parent
    models_dir = pkg_dir / "resources" / "models"
    return str(models_dir)


def start(on_detected, model: str = WAKE_WORD_MODEL, sensitivity: float = SENSITIVITY):
    global _thread, _running, _on_detected_callback
    if _running:
        return
    _on_detected_callback = on_detected
    _running = True
    _thread = threading.Thread(
        target=_run,
        args=(model, sensitivity),
        daemon=True,
        name="WakeWord"
    )
    _thread.start()


def stop():
    global _running
    _running = False


def is_running() -> bool:
    return _running


def _run(model: str, sensitivity: float):
    global _running
    try:
        _log.info("WakeWord-Thread gestartet")
        import pyaudio
        _log.info("pyaudio importiert")
        from openwakeword.model import Model
        _log.info("openwakeword importiert")

        models_dir = _get_models_dir()
        _log.info(f"Modell-Verzeichnis: {models_dir}")

        # Modell-Datei: erst als vollständigen Pfad versuchen
        model_file = str(Path(models_dir) / f"{model}.onnx")
        _log.info(f"Suche Modell: {model_file} — existiert: {Path(model_file).exists()}")

        if not Path(model_file).exists() and not getattr(sys, 'frozen', False):
            # Dev-Modus: Modelle wurden nie heruntergeladen (frisches Setup) — einmalig nachholen
            _log.warning(f"Modell fehlt, lade openwakeword-Modelle nach: {model_file}")
            from openwakeword.utils import download_models
            download_models()

        if Path(model_file).exists():
            oww = Model(wakeword_models=[model_file], inference_framework="onnx")
        else:
            # Fallback: openwakeword findet es selbst
            _log.warning(f"Modell nicht gefunden, versuche direkt: {model}")
            oww = Model(wakeword_models=[model], inference_framework="onnx")

        _log.info("Modell geladen")

        # PyAudio initialisieren
        p_audio = pyaudio.PyAudio()
        _log.info(f"PyAudio: {p_audio.get_device_count()} Geräte gefunden")

        # Bestes Eingabegerät finden — bevorzuge Standard-Gerät
        input_device = None
        default_input = None
        try:
            default_info = p_audio.get_default_input_device_info()
            default_input = int(default_info["index"])
            _log.info(f"Standard-Eingabegerät: {default_input} — {default_info['name']}")
        except Exception:
            pass

        for i in range(p_audio.get_device_count()):
            info = p_audio.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                input_device = i
                _log.debug(f"Gefundenes Eingabegerät [{i}]: {info['name']}")
                if default_input is not None:
                    input_device = default_input
                break

        _log.info(f"Verwende Eingabegerät: {input_device}")

        # Natürliche Sample-Rate des Geräts nutzen und selbst auf 16kHz resampeln,
        # statt PortAudio intern resamplen zu lassen — auf macOS/CoreAudio (oft 44.1/48kHz
        # native Geräte-Rate) verzerrt PortAudios eingebautes Resampling auf 16kHz das Signal
        # so stark, dass openWakeWord das Wake-Word nie erkennt, obwohl Audio ankommt.
        target_rate = 16000
        native_rate = target_rate
        try:
            if input_device is not None:
                dev_info = p_audio.get_device_info_by_index(input_device)
                native_rate = int(dev_info.get("defaultSampleRate") or target_rate)
        except Exception:
            native_rate = target_rate

        chunk_target = 1280  # 80ms bei 16kHz
        chunk_native = int(round(chunk_target * native_rate / target_rate))

        stream_kwargs = dict(
            format=pyaudio.paInt16,
            channels=1,
            rate=native_rate,
            input=True,
            frames_per_buffer=chunk_native,
        )
        if input_device is not None:
            stream_kwargs["input_device_index"] = input_device

        stream = p_audio.open(**stream_kwargs)
        _log.info(f"Audio-Stream geöffnet — höre auf '{model}' (native Rate: {native_rate}Hz)")
        print(f"[WakeWord] Höre auf '{model}' — Mikrofon aktiv (Gerät {input_device})")

        _chunk_count = 0
        _max_score_window = 0.0
        while _running:
            try:
                raw = stream.read(chunk_native, exception_on_overflow=False)
            except OSError:
                _log.warning("OSError beim Lesen des Audio-Streams")
                break
            audio_data = np.frombuffer(raw, dtype=np.int16)

            if native_rate != target_rate:
                from scipy.signal import resample_poly
                resampled = resample_poly(audio_data.astype(np.float32), target_rate, native_rate)
                audio_data = np.clip(resampled, -32768, 32767).astype(np.int16)

            # Auto-Gain: leise Mikrofone (Distanz zum Laptop, schwache Eingangsstärke,
            # externe Interfaces mit niedrigem Pegel — betrifft Windows genauso wie
            # macOS) sonst nie eine Erkennung erreichen, weil openWakeWord auf
            # normal ausgesteuertes Audio trainiert ist. Peak wird auf einen
            # Zielwert angehoben, reine Stille/Rauschen bleibt unverstärkt.
            pre_peak = int(np.abs(audio_data).max())
            audio_data = _auto_gain(audio_data)

            _chunk_count += 1
            prediction = oww.predict(audio_data)
            if prediction:
                _max_score_window = max(_max_score_window, max(prediction.values()))

            if _chunk_count % 12 == 0:  # ca. alle 1s loggen
                post_peak = int(np.abs(audio_data).max())
                rms  = float(np.sqrt(np.mean(audio_data.astype(np.float64) ** 2)))
                _log.debug(f"Pegel — Peak roh: {pre_peak}  nach Gain: {post_peak}  RMS: {rms:.0f}  MaxScore(1s): {_max_score_window:.4f}")
                _max_score_window = 0.0

            for name, score in prediction.items():
                if score >= 0.15:
                    _log.debug(f"Score '{name}': {score:.3f}")
                if score >= sensitivity:
                    _log.info(f"Wake-Word erkannt: '{name}' (Score: {score:.2f})")
                    print(f"[WakeWord] '{name}' erkannt! Score: {score:.2f}")
                    oww.reset()
                    if _on_detected_callback:
                        _on_detected_callback()
                    break

        stream.stop_stream()
        stream.close()
        p_audio.terminate()
        _log.info("WakeWord-Thread beendet")

    except ImportError as e:
        _log.error(f"Import-Fehler: {e}", exc_info=True)
        print(f"[WakeWord] Library fehlt: {e}")
        _running = False
    except Exception as e:
        _log.error(f"Unbekannter Fehler: {e}", exc_info=True)
        print(f"[WakeWord] Fehler: {e}")
        _running = False
