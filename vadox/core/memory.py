import json
from pathlib import Path
from datetime import datetime


MEMORY_PATH = Path.home() / ".vadox" / "memory.json"


DEFAULT = {
    "user_name": "",
    "facts": [],
    "preferences": {},
    "last_topics": [],
    "conversation_count": 0,
    "first_seen": "",
    "last_seen": "",
}


def load() -> dict:
    try:
        if MEMORY_PATH.exists():
            return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return dict(DEFAULT)


def save(memory: dict):
    try:
        MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        MEMORY_PATH.write_text(json.dumps(memory, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[Memory] Speichern fehlgeschlagen: {e}")


def remember_fact(fact: str):
    m = load()
    if fact not in m.get("facts", []):
        m.setdefault("facts", []).append(fact)
        if len(m["facts"]) > 50:
            m["facts"] = m["facts"][-50:]
    save(m)


def set_user_name(name: str):
    m = load()
    m["user_name"] = name
    save(m)


def add_topic(topic: str):
    m = load()
    topics = m.get("last_topics", [])
    if topic not in topics:
        topics.insert(0, topic)
    m["last_topics"] = topics[:10]
    save(m)


def record_session():
    m = load()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    if not m.get("first_seen"):
        m["first_seen"] = now
    m["last_seen"] = now
    m["conversation_count"] = m.get("conversation_count", 0) + 1
    save(m)


def build_context() -> str:
    m = load()
    lines = []
    if m.get("user_name"):
        lines.append(f"Der Nutzer heißt {m['user_name']}.")
    if m.get("facts"):
        lines.append("Bekannte Fakten über den Nutzer: " + "; ".join(m["facts"][-10:]) + ".")
    if m.get("preferences"):
        prefs = "; ".join(f"{k}: {v}" for k, v in m["preferences"].items())
        lines.append(f"Vorlieben des Nutzers: {prefs}.")
    if m.get("last_topics"):
        lines.append("Letzte Themen: " + ", ".join(m["last_topics"][:5]) + ".")
    if m.get("conversation_count"):
        lines.append(f"Bisherige Gespräche: {m['conversation_count']}.")
    return " ".join(lines) if lines else ""
