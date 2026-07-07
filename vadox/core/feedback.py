"""
Feedback-System — Vadox lernt aus Daumen hoch/runter.
Positives und negatives Feedback wird gespeichert und beeinflusst zukünftige Antworten.
"""
import json
from pathlib import Path
from datetime import datetime

FEEDBACK_FILE = Path.home() / ".vadox" / "feedback.json"
MAX_EXAMPLES  = 20  # Maximale Anzahl gespeicherter Beispiele


def _load() -> dict:
    try:
        if FEEDBACK_FILE.exists():
            return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"positive": [], "negative": [], "corrections": []}


def _save(data: dict):
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    FEEDBACK_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_positive(user_msg: str, ai_response: str):
    """Speichert eine gute Antwort als positives Beispiel."""
    data = _load()
    data["positive"].append({
        "user":     user_msg[:200],
        "response": ai_response[:400],
        "date":     datetime.now().strftime("%d.%m.%Y"),
    })
    # Nur die neuesten MAX_EXAMPLES behalten
    data["positive"] = data["positive"][-MAX_EXAMPLES:]
    _save(data)


def save_negative(user_msg: str, ai_response: str, correction: str = ""):
    """Speichert eine schlechte Antwort als negatives Beispiel."""
    data = _load()
    entry = {
        "user":     user_msg[:200],
        "response": ai_response[:400],
        "date":     datetime.now().strftime("%d.%m.%Y"),
    }
    if correction:
        entry["correction"] = correction
        data["corrections"].append(entry)
        data["corrections"] = data["corrections"][-MAX_EXAMPLES:]
    else:
        data["negative"].append(entry)
        data["negative"] = data["negative"][-MAX_EXAMPLES:]
    _save(data)


def save_correction(user_msg: str, ai_response: str, correct_answer: str):
    """Speichert eine Korrektur: 'Das war falsch, richtig wäre...'"""
    data = _load()
    data["corrections"].append({
        "user":       user_msg[:200],
        "wrong":      ai_response[:300],
        "correct":    correct_answer[:300],
        "date":       datetime.now().strftime("%d.%m.%Y"),
    })
    data["corrections"] = data["corrections"][-MAX_EXAMPLES:]
    _save(data)


def build_feedback_context() -> str:
    """Erzeugt Kontext für den System-Prompt basierend auf Feedback."""
    data        = _load()
    corrections = data.get("corrections", [])
    negative    = data.get("negative", [])

    parts = []

    if corrections:
        lines = ["KORREKTUREN (diese Fehler wurden in der Vergangenheit gemacht — nicht wiederholen):"]
        for c in corrections[-5:]:
            lines.append(f"- Frage: '{c['user'][:80]}' → Falsch: '{c.get('wrong','?')[:80]}' → Richtig: '{c.get('correct','?')[:80]}'")
        parts.append("\n".join(lines))

    if negative:
        lines = ["SCHLECHTE ANTWORTEN (diese Art von Antworten nicht wiederholen):"]
        for n in negative[-3:]:
            lines.append(f"- Auf '{n['user'][:60]}' war folgende Antwort schlecht: '{n['response'][:80]}'")
        parts.append("\n".join(lines))

    return "\n\n".join(parts)


def get_stats() -> str:
    """Feedback-Statistik."""
    data = _load()
    pos  = len(data.get("positive", []))
    neg  = len(data.get("negative", []))
    cor  = len(data.get("corrections", []))
    total = pos + neg
    pct   = int(pos / total * 100) if total > 0 else 0
    return (
        f"Feedback-Statistik:\n"
        f"  Daumen hoch: {pos}\n"
        f"  Daumen runter: {neg}\n"
        f"  Korrekturen: {cor}\n"
        f"  Zufriedenheit: {pct}%"
    )
