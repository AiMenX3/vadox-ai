import threading
import time
import speech_recognition as sr


class STTEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 200
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8        # 0.8 Sek Pause = fertig gesprochen (war 2.0 - fuehlte sich traege an)
        self.recognizer.non_speaking_duration = 0.6  # muss <= pause_threshold sein
        self.recognizer.phrase_threshold = 0.2
        self._listening = False
        self._mic_index = self._find_mic()

    def _find_mic(self) -> int | None:
        try:
            names = sr.Microphone.list_microphone_names()
            keywords = ["mikrofon", "microphone", "input", "aufnahme"]
            for i, name in enumerate(names):
                low = name.lower()
                if any(k in low for k in keywords):
                    return i
        except Exception:
            pass
        return None

    def listen_once(self, on_result=None, on_error=None, language="de-DE"):
        if self._listening:
            return
        thread = threading.Thread(
            target=self._listen_thread,
            args=(on_result, on_error, language),
            daemon=True
        )
        thread.start()

    def _listen_thread(self, on_result, on_error, language):
        self._listening = True
        try:
            # Warten bis TTS fertig ist — nicht in eigene Stimme hineinhören
            from vadox.core.tts_engine import is_speaking
            waited = 0
            while is_speaking() and waited < 15:
                time.sleep(0.1)
                waited += 0.1
            # Kurze Pause nach TTS damit Echo abklingt
            if waited > 0:
                time.sleep(0.4)

            mic_kwargs = {}
            if self._mic_index is not None:
                mic_kwargs['device_index'] = self._mic_index

            with sr.Microphone(**mic_kwargs) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=20)

            # Nochmal prüfen — falls TTS zwischenzeitlich gestartet wurde
            if is_speaking():
                if on_error:
                    on_error("Vadox spricht gerade — bitte warten.")
                return

            text = self.recognizer.recognize_google(audio, language=language)
            if on_result:
                on_result(text)

        except sr.WaitTimeoutError:
            if on_error:
                on_error("Timeout, kein Sprachinput erkannt.")
        except sr.UnknownValueError:
            if on_error:
                on_error("Sprache nicht erkannt, bitte nochmal versuchen.")
        except sr.RequestError as e:
            if on_error:
                on_error(f"Google API Fehler: {e}")
        except OSError as e:
            if on_error:
                on_error(f"Mikrofon nicht gefunden: {e}")
        except Exception as e:
            if on_error:
                on_error(f"Fehler: {e}")
        finally:
            self._listening = False
