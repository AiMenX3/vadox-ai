# -*- coding: utf-8 -*-
"""
Vadox Face Engine - Gesichtserkennung + Emotions-Analyse + Bester Freund Reaktionen
"""
import threading
import json
from pathlib import Path
from datetime import datetime, timedelta

_thread = None
_running = False
_on_result_callback = None

PROFILES_DIR = Path.home() / ".vadox" / "faces"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

EMOTION_DE = {
    "happy":    ("Gluecklich",   "😊"),
    "sad":      ("Traurig",      "😢"),
    "angry":    ("Wuetend",      "😠"),
    "surprise": ("Ueberrascht",  "😲"),
    "fear":     ("Aengstlich",   "😨"),
    "disgust":  ("Angewidert",   "🤢"),
    "neutral":  ("Neutral",      "😐"),
}

FRIEND_REACTIONS = {
    "sad": [
        "Hey, du siehst gerade etwas traurig aus. Alles okay bei dir?",
        "Ich merke dass du gerade nicht so gut drauf bist. Moechtest du darueber reden?",
        "Du wirkst gerade ein bisschen down. Soll ich Musik fuer dich abspielen?",
    ],
    "angry": [
        "Hey, du siehst gestresst aus. Was ist passiert?",
        "Ich sehe dass dich gerade etwas aergert. Kann ich helfen?",
        "Kurze Pause vielleicht? Ich kann etwas entspannende Musik spielen wenn du moechtest.",
    ],
    "fear": [
        "Alles gut bei dir? Du siehst etwas angespannt aus.",
        "Hey, ich bin hier. Moechtest du mir sagen was dich beschaeftigt?",
    ],
    "disgust": [
        "Du siehst nicht begeistert aus gerade. Alles okay?",
        "Ist alles in Ordnung? Du wirkst etwas unwohl.",
    ],
    "surprise": [
        "Oh, hat dich etwas ueberrascht?",
        "Du schaust ueberrascht - alles gut?",
    ],
}

_last_reaction_time = None
_last_reacted_emotion = ""
_reaction_cooldown_minutes = 10
_last_emotion = ""
_last_person = ""
_known_faces = {}


def load_profiles():
    global _known_faces
    _known_faces = {}
    for f in PROFILES_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            _known_faces[data["name"]] = data.get("img_path", "")
        except Exception:
            continue


def save_profile(name, img_path):
    profile = {
        "name": name,
        "img_path": img_path,
        "created": datetime.now().isoformat(),
    }
    path = PROFILES_DIR / f"{name.lower().replace(' ', '_')}.json"
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    _known_faces[name] = img_path


def delete_profile(name):
    path = PROFILES_DIR / f"{name.lower().replace(' ', '_')}.json"
    if path.exists():
        path.unlink()
        _known_faces.pop(name, None)
        img = PROFILES_DIR / f"{name.lower().replace(' ', '_')}.jpg"
        if img.exists():
            img.unlink()
        return True
    return False


def get_profiles():
    load_profiles()
    return list(_known_faces.keys())


def _open_camera(index=0):
    """Öffnet Kamera — CAP_DSHOW nur auf Windows im Dev-Modus."""
    import cv2, sys, platform
    if platform.system() == "Windows" and not getattr(sys, 'frozen', False):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(index)
    return cap


def capture_face_for_profile(name):
    try:
        import cv2
        cap = _open_camera(0)
        if not cap.isOpened():
            return False, "Keine Webcam gefunden."
        for _ in range(5):
            cap.read()
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return False, "Bild konnte nicht aufgenommen werden."
        img_path = str(PROFILES_DIR / f"{name.lower().replace(' ', '_')}.jpg")
        cv2.imwrite(img_path, frame)
        save_profile(name, img_path)
        return True, f"Profil fuer '{name}' gespeichert."
    except Exception as e:
        return False, f"Fehler: {e}"


def _should_react(emotion):
    global _last_reaction_time, _last_reacted_emotion
    if emotion not in FRIEND_REACTIONS:
        return False
    now = datetime.now()
    if _last_reaction_time is None:
        return True
    if now - _last_reaction_time < timedelta(minutes=_reaction_cooldown_minutes):
        return False
    return True


def analyze_single_frame(frame):
    try:
        from deepface import DeepFace
        result = DeepFace.analyze(
            frame,
            actions=["emotion"],
            enforce_detection=False,
            silent=True,
        )
        if isinstance(result, list):
            result = result[0]
        dominant = result.get("dominant_emotion", "neutral")
        emotions = result.get("emotion", {})
        confidence = emotions.get(dominant, 0)
        de_label, icon = EMOTION_DE.get(dominant, (dominant, "😐"))
        return {
            "emotion":      dominant,
            "label_de":     de_label,
            "icon":         icon,
            "confidence":   round(confidence, 1),
            "all_emotions": {k: round(v, 1) for k, v in emotions.items()},
        }
    except Exception:
        return None


def _run_background():
    global _running, _last_emotion, _last_person
    global _last_reaction_time, _last_reacted_emotion
    try:
        import cv2
        cap = _open_camera(0)
        if not cap.isOpened():
            print("[FaceEngine] Keine Webcam.")
            _running = False
            return

        frame_count = 0
        print("[FaceEngine] Hintergrund-Analyse gestartet")

        while _running:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            if frame_count % 30 != 0:
                continue

            result = analyze_single_frame(frame)
            if not result:
                continue

            emotion = result["emotion"]
            confidence = result["confidence"]

            if emotion != _last_emotion:
                _last_emotion = emotion
                if _on_result_callback:
                    _on_result_callback("emotion", result)

            if confidence > 55 and _should_react(emotion):
                import random
                reactions = FRIEND_REACTIONS.get(emotion, [])
                if reactions:
                    msg = random.choice(reactions)
                    _last_reaction_time = datetime.now()
                    _last_reacted_emotion = emotion
                    if _on_result_callback:
                        _on_result_callback("friend_reaction", {
                            "emotion":  emotion,
                            "label_de": result["label_de"],
                            "icon":     result["icon"],
                            "message":  msg,
                        })

        cap.release()
    except Exception as e:
        print(f"[FaceEngine] Fehler: {e}")
    finally:
        _running = False


def start(on_result=None):
    global _thread, _running, _on_result_callback
    if _running:
        return
    _on_result_callback = on_result
    _running = True
    _thread = threading.Thread(target=_run_background, daemon=True, name="FaceEngine")
    _thread.start()


def stop():
    global _running
    _running = False


def is_running():
    return _running


def get_last_emotion():
    de_label, icon = EMOTION_DE.get(_last_emotion, ("Neutral", "😐"))
    return {"emotion": _last_emotion, "label_de": de_label, "icon": icon}


def get_last_person():
    return _last_person or "Unbekannt"
