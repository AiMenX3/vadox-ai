import re
import os
import asyncio
import tempfile
import threading
import queue

# Globales Flag: TTS spricht gerade — STT darf NICHT lauschen
_speaking = False


def is_speaking() -> bool:
    return _speaking


def clean_for_speech(text: str) -> str:
    text = re.sub(r'[#*_`~]', '', text)
    text = re.sub(r'^\s*[-•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    emoji_pattern = re.compile(
        "[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF" u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0" u"\U000024C2-\U0001F251" "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _play_audio_file(path: str, stop_check=None):
    """Spielt eine MP3-Datei ab. stop_check() gibt True zurück zum Unterbrechen."""
    try:
        import pygame
        pygame.mixer.pre_init(44100, -16, 2, 512)
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        import time
        while pygame.mixer.music.get_busy():
            if stop_check and stop_check():
                pygame.mixer.music.stop()
                break
            time.sleep(0.05)
        pygame.mixer.music.stop()
    except Exception as e:
        print(f"[Audio-Fehler] {e}")


class TTSEngine:
    def __init__(self, voice: str = "de-DE-KatjaNeural"):
        self.voice       = voice          # Edge-TTS Stimme (Fallback)
        self._lock       = threading.Lock()
        self._busy       = False
        self._stop_flag  = False

        # ElevenLabs-Einstellungen (werden aus settings geladen)
        self._eleven_key   = ""
        self._eleven_voice = "W2KR2ct3bRh7HcawFJB4"  # Vadox JARVIS-Stimme
        self._use_eleven   = False
        self._load_settings()

    def _load_settings(self):
        try:
            from vadox.core import settings
            cfg = settings.load()
            self._eleven_key   = cfg.get("elevenlabs_api_key", "")
            self._eleven_voice = cfg.get("elevenlabs_voice_id", "W2KR2ct3bRh7HcawFJB4")
            self._use_eleven   = bool(self._eleven_key) and cfg.get("elevenlabs_enabled", False)
            # Edge-TTS Stimme aus Einstellungen
            self.voice = cfg.get("tts_voice", "de-DE-KatjaNeural")
        except Exception:
            pass

    def reload_settings(self):
        self._load_settings()

    @property
    def busy(self) -> bool:
        return self._busy

    def stop(self):
        self._stop_flag = True
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

    def speak(self, text: str, on_done=None):
        cleaned = clean_for_speech(text)
        if not cleaned:
            if on_done:
                on_done()
            return
        if self._busy:
            self.stop()
        self._stop_flag = False
        threading.Thread(
            target=self._speak_thread,
            args=(cleaned, on_done),
            daemon=True
        ).start()

    def _speak_thread(self, text: str, on_done=None):
        global _speaking
        with self._lock:
            self._busy  = True
            _speaking   = True
            tmp_path    = None
            try:
                self._load_settings()

                if self._use_eleven and self._eleven_key:
                    print(f"[TTS] ElevenLabs Stream → Voice {self._eleven_voice[:8]}...")
                    ok = self._stream_elevenlabs(text)
                    if ok:
                        return  # Streaming hat alles erledigt
                    print("[TTS] ElevenLabs fehlgeschlagen — Fallback auf Edge-TTS")

                # Fallback auf Edge-TTS
                print(f"[TTS] Edge-TTS → {self.voice}")
                tmp_path = self._synthesize_edge(text)

                if not tmp_path or os.path.getsize(tmp_path) < 100:
                    return

                if self._stop_flag:
                    return

                _play_audio_file(tmp_path, stop_check=lambda: self._stop_flag)

            except Exception as e:
                print(f"[TTS Fehler] {e}")
            finally:
                self._busy      = False
                _speaking       = False
                self._stop_flag = False
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                if on_done:
                    on_done()

    def _stream_elevenlabs(self, text: str) -> bool:
        """
        Streamt PCM-Audio direkt von ElevenLabs → sounddevice.
        Startet Wiedergabe sobald erster Chunk ankommt (~200ms).
        Gibt True zurück wenn erfolgreich.
        """
        try:
            import sounddevice as sd
            from elevenlabs.client import ElevenLabs
            from elevenlabs import VoiceSettings

            SAMPLE_RATE = 22050
            CHANNELS    = 1

            client = ElevenLabs(api_key=self._eleven_key)

            stream = client.text_to_speech.stream(
                voice_id=self._eleven_voice,
                text=text,
                model_id="eleven_turbo_v2_5",
                output_format="pcm_22050",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.8,
                    style=0.0,
                    use_speaker_boost=True,
                ),
            )

            with sd.RawOutputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=4096,
            ) as audio_out:
                for chunk in stream:
                    if self._stop_flag:
                        break
                    if chunk:
                        audio_out.write(chunk)

            return True

        except Exception as e:
            print(f"[ElevenLabs Stream Fehler] {e}")
            return False

    def _synthesize_elevenlabs(self, text: str) -> str | None:
        """Synthetisiert Text mit ElevenLabs API. Gibt MP3-Pfad zurück."""
        try:
            from elevenlabs.client import ElevenLabs
            from elevenlabs import VoiceSettings

            client = ElevenLabs(api_key=self._eleven_key)

            audio = client.text_to_speech.convert(
                text=text,
                voice_id=self._eleven_voice,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.8,
                    style=0.2,
                    use_speaker_boost=True,
                ),
            )

            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            for chunk in audio:
                if chunk:
                    tmp.write(chunk)
            tmp.close()
            return tmp.name

        except Exception as e:
            print(f"[ElevenLabs Fehler] {e} — Fallback auf Edge-TTS")
            return None

    def _synthesize_edge(self, text: str) -> str | None:
        """Synthetisiert Text mit Edge-TTS (kostenlos, Microsoft)."""
        try:
            import edge_tts

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _save():
                tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                p   = tmp.name
                tmp.close()
                communicate = edge_tts.Communicate(text, self.voice)
                with open(p, "wb") as f:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])
                return p

            path = loop.run_until_complete(_save())
            loop.close()
            return path

        except Exception as e:
            print(f"[Edge-TTS Fehler] {e}")
            return None


class SentenceSpeechQueue:
    """Sammelt gestreamten Antwort-Text und spricht ihn Satz für Satz, sobald
    ein Satz fertig ist — statt auf die komplette Antwort zu warten. Sätze
    werden streng nacheinander abgespielt (nie überlappend), auch während
    weiterer Text noch von der API hereinkommt."""

    _SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')

    def __init__(self, tts: "TTSEngine"):
        self._tts        = tts
        self._buffer      = ""
        self._queue: "queue.Queue" = queue.Queue()
        self._worker      = None
        self._on_done_cb  = None
        self._lock        = threading.Lock()

    def reset(self):
        """Für einen neuen Gesprächs-Zug: Puffer/Queue leeren (laufende Wiedergabe
        wird davon nicht gestoppt — das übernimmt TTSEngine.speak() selbst)."""
        with self._lock:
            self._buffer = ""
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
            self._on_done_cb = None

    def feed(self, chunk: str):
        """Nimmt einen gestreamten Text-Chunk entgegen und legt jeden fertigen
        Satz sofort zum Sprechen in die Queue."""
        with self._lock:
            self._buffer += chunk
            parts = self._SENTENCE_SPLIT.split(self._buffer)
            if len(parts) > 1:
                complete, self._buffer = parts[:-1], parts[-1]
                for sentence in complete:
                    sentence = sentence.strip()
                    if sentence:
                        self._queue.put(sentence)
        self._ensure_worker()

    def finish(self, on_done=None):
        """Antwort ist vollständig — restlichen Puffer als letzten Satz einreihen
        und on_done aufrufen, sobald die Queue wirklich leer gesprochen ist."""
        with self._lock:
            remainder = self._buffer.strip()
            self._buffer = ""
            if remainder:
                self._queue.put(remainder)
            self._on_done_cb = on_done
            self._queue.put(None)  # Sentinel: Ende dieses Zugs
        self._ensure_worker()

    def _ensure_worker(self):
        if self._worker is None or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._run_worker, daemon=True)
            self._worker.start()

    def _run_worker(self):
        while True:
            item = self._queue.get()
            if item is None:
                cb, self._on_done_cb = self._on_done_cb, None
                if cb:
                    cb()
                return
            done_evt = threading.Event()
            self._tts.speak(item, on_done=done_evt.set)
            done_evt.wait()


# ── Verfügbare ElevenLabs-Stimmen (für Einstellungen) ────────────────────────

ELEVENLABS_VOICES = {
    # Männlich (Englisch — gut für JARVIS-Style)
    "Daniel (tief, ruhig)":       "onwK4e9ZLuTAKqWW03F9",
    "Antoni (klar, professionell)":"ErXwobaYiN019PkySvjV",
    "Josh (warm, freundlich)":     "TxGEqnHWrfWFTfGW9XjX",
    "Arnold (kraftvoll)":          "VR6AewLTigWG4xSOukaG",
    # Männlich (Deutsch)
    "Florian (Deutsch, tief)":     "AZnzlk1XvdvUeBnXmlld",
    # Weiblich
    "Rachel (klar, neutral)":      "21m00Tcm4TlvDq8ikWAM",
    "Domi (selbstbewusst)":        "AZnzlk1XvdvUeBnXmlld",
}
