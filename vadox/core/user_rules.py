"""
Nutzer-Regeln und persönliche Anweisungen.
"Wenn ich X sage, mach immer Y" — dauerhaft gespeichert.
"Antworte immer kürzer" — wird in den System-Prompt eingebettet.
"""
import json
from pathlib import Path
from datetime import datetime

RULES_FILE        = Path.home() / ".vadox" / "user_rules.json"
INSTRUCTIONS_FILE = Path.home() / ".vadox" / "user_instructions.json"


def _load_rules() -> dict:
    try:
        if RULES_FILE.exists():
            return json.loads(RULES_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"rules": [], "instructions": []}


def _save_rules(data: dict):
    RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
    RULES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_rule(trigger: str, action: str) -> str:
    """'Wenn ich X sage, mach immer Y' — speichert eine Regel."""
    data = _load_rules()
    # Doppelte vermeiden
    for r in data["rules"]:
        if r["trigger"].lower() == trigger.lower():
            r["action"] = action
            _save_rules(data)
            return f"Regel aktualisiert: Wenn du '{trigger}' sagst → {action}"

    data["rules"].append({
        "trigger": trigger,
        "action":  action,
        "created": datetime.now().strftime("%d.%m.%Y"),
    })
    _save_rules(data)
    return f"Regel gespeichert: Wenn du '{trigger}' sagst → ich werde immer {action}"


def remove_rule(trigger: str) -> str:
    """Löscht eine Regel."""
    data  = _load_rules()
    before = len(data["rules"])
    data["rules"] = [r for r in data["rules"] if r["trigger"].lower() != trigger.lower()]
    if len(data["rules"]) < before:
        _save_rules(data)
        return f"Regel für '{trigger}' gelöscht."
    return f"Keine Regel für '{trigger}' gefunden."


def list_rules() -> str:
    """Zeigt alle gespeicherten Regeln."""
    data = _load_rules()
    rules = data.get("rules", [])
    instr = data.get("instructions", [])

    lines = []
    if rules:
        lines.append(f"Aktive Regeln ({len(rules)}):")
        for r in rules:
            lines.append(f"  Wenn '{r['trigger']}' -> {r['action']}")
    if instr:
        lines.append(f"\nPersönliche Anweisungen ({len(instr)}):")
        for i in instr:
            lines.append(f"  • {i['text']}")
    if not lines:
        return "Noch keine Regeln oder Anweisungen gespeichert."
    return "\n".join(lines)


def add_instruction(instruction: str) -> str:
    """
    Fügt eine dauerhafte Verhaltensanweisung hinzu.
    z.B. "Antworte immer kürzer" oder "Nenn mich immer Chef"
    """
    data = _load_rules()
    if "instructions" not in data:
        data["instructions"] = []

    # Duplikate vermeiden
    for i in data["instructions"]:
        if i["text"].lower() == instruction.lower():
            return f"Diese Anweisung ist bereits aktiv: '{instruction}'"

    data["instructions"].append({
        "text":    instruction,
        "created": datetime.now().strftime("%d.%m.%Y"),
    })
    _save_rules(data)
    return f"Anweisung dauerhaft gespeichert: '{instruction}' — ich werde das ab sofort immer beachten."


def remove_instruction(text: str) -> str:
    """Löscht eine Verhaltensanweisung."""
    data = _load_rules()
    before = len(data.get("instructions", []))
    data["instructions"] = [
        i for i in data.get("instructions", [])
        if text.lower() not in i["text"].lower()
    ]
    if len(data.get("instructions", [])) < before:
        _save_rules(data)
        return f"Anweisung entfernt."
    return "Anweisung nicht gefunden."


def build_rules_context() -> str:
    """Gibt den Kontext für den System-Prompt zurück."""
    data  = _load_rules()
    rules = data.get("rules", [])
    instr = data.get("instructions", [])

    parts = []
    if instr:
        parts.append("PERSÖNLICHE ANWEISUNGEN (immer befolgen):\n" +
                     "\n".join(f"- {i['text']}" for i in instr))
    if rules:
        parts.append("AUTOMATISCHE REGELN (auf Trigger reagieren - diese Regeln immer beachten):\n" +
                     "\n".join(f"- Wenn Nutzer '{r['trigger']}' sagt oder schreibt: {r['action']}" for r in rules))
    return "\n\n".join(parts)


def check_triggers(user_message: str) -> str | None:
    """
    Prüft ob eine Nutzer-Nachricht einen Trigger enthält.
    Gibt die Aktion zurück oder None.
    """
    data  = _load_rules()
    rules = data.get("rules", [])
    msg_lower = user_message.lower()

    for rule in rules:
        trigger = rule["trigger"].lower()
        if trigger in msg_lower:
            return rule["action"]
    return None
