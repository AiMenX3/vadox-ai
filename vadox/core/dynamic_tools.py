"""
Dynamisches Tool-System — Vadox kann zur Laufzeit neue Tools schreiben und registrieren.
Neue Tools werden in ~/.vadox/custom_tools/ gespeichert und sofort nutzbar.
"""
import json
import sys
import importlib
from pathlib import Path

CUSTOM_TOOLS_DIR  = Path.home() / ".vadox" / "custom_tools"
CUSTOM_TOOLS_JSON = Path.home() / ".vadox" / "custom_tool_definitions.json"

# Laufzeit-Registry für dynamisch geladene Tools
_dynamic_definitions: list = []
_dynamic_handlers:    dict = {}


def _ensure_dirs():
    CUSTOM_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    if not CUSTOM_TOOLS_JSON.exists():
        CUSTOM_TOOLS_JSON.write_text("[]", encoding="utf-8")


def _is_valid_tool_def(defn: dict) -> bool:
    """Prüft, ob eine Tool-Definition ein gültiges Anthropic-Tool-Schema hat.
    Ein kaputtes Schema würde sonst JEDEN Chat-Aufruf scheitern lassen,
    weil alle Tool-Definitionen bei jeder Anfrage mitgeschickt werden."""
    if not isinstance(defn, dict):
        return False
    if not defn.get("name") or not isinstance(defn.get("name"), str):
        return False
    schema = defn.get("input_schema")
    if not isinstance(schema, dict) or schema.get("type") != "object":
        return False
    if not isinstance(schema.get("properties", {}), dict):
        return False
    return True


def _save_defs(defs: list):
    CUSTOM_TOOLS_JSON.write_text(json.dumps(defs, ensure_ascii=False, indent=2), encoding="utf-8")


def load_dynamic_tools():
    """Lädt alle custom Tools beim Start. Muss einmal aufgerufen werden.
    Kaputte Tools (fehlerhafter Code oder ungültiges Schema) werden übersprungen
    und automatisch aus der Registrierung entfernt, statt den Rest der App zu blockieren."""
    _ensure_dirs()
    global _dynamic_definitions, _dynamic_handlers
    try:
        defs = json.loads(CUSTOM_TOOLS_JSON.read_text(encoding="utf-8"))
        if not isinstance(defs, list):
            defs = []
    except Exception:
        defs = []

    _dynamic_definitions.clear()
    _dynamic_handlers.clear()

    # Custom-Tools-Ordner zum Python-Pfad hinzufügen
    tools_str = str(CUSTOM_TOOLS_DIR)
    if tools_str not in sys.path:
        sys.path.insert(0, tools_str)

    still_valid = []
    dropped     = []
    for d in defs:
        module_name = d.get("module")
        func_name   = d.get("function")
        defn        = d.get("definition", {})
        name        = defn.get("name", module_name or "?")

        if not module_name or not func_name or not _is_valid_tool_def(defn):
            dropped.append(name)
            print(f"[DynTools] Ungültiges Tool entfernt: {name}")
            continue

        try:
            mod  = importlib.import_module(module_name)
            func = getattr(mod, func_name)
            if not callable(func):
                raise TypeError(f"{func_name} ist nicht aufrufbar")
            _dynamic_definitions.append(defn)
            _dynamic_handlers[defn["name"]] = func
            still_valid.append(d)
        except Exception as e:
            dropped.append(name)
            print(f"[DynTools] Kaputtes Tool automatisch entfernt: {name} ({module_name}.{func_name}): {e}")

    # Registrierung bereinigen, damit kaputte Tools nicht bei jedem Start erneut versucht werden
    if dropped:
        try:
            _save_defs(still_valid)
        except Exception as e:
            print(f"[DynTools] Konnte bereinigte Registrierung nicht speichern: {e}")

    return _dynamic_definitions


def get_dynamic_definitions() -> list:
    return list(_dynamic_definitions)


def execute_dynamic_tool(name: str, inputs: dict) -> str | None:
    """Führt ein dynamisches Tool aus. Gibt None zurück wenn nicht gefunden."""
    func = _dynamic_handlers.get(name)
    if func is None:
        return None
    try:
        return func(**inputs)
    except Exception as e:
        return f"Tool-Fehler ({name}): {e}"


def register_new_tool(
    tool_name:   str,
    description: str,
    python_code: str,
    parameters:  dict,
    func_name:   str = "run",
) -> str:
    """
    Schreibt ein neues Tool:
    1. Python-Datei speichern
    2. Tool-Definition registrieren
    3. Sofort in Laufzeit laden
    """
    _ensure_dirs()

    if not tool_name or not tool_name.strip():
        return "Tool konnte nicht erstellt werden: kein Name angegeben."

    # Dateiname aus Tool-Name ableiten
    safe_name   = tool_name.replace("-", "_").replace(" ", "_").lower()
    module_name = f"tool_{safe_name}"
    py_file     = CUSTOM_TOOLS_DIR / f"{module_name}.py"

    # Tool-Definition
    tool_def = {
        "name":         tool_name,
        "description":  description,
        "input_schema": {
            "type":       "object",
            "properties": parameters if isinstance(parameters, dict) else {},
            "required":   list(parameters.keys()) if isinstance(parameters, dict) else [],
        }
    }

    if not _is_valid_tool_def(tool_def):
        return f"Tool '{tool_name}' konnte nicht erstellt werden: ungültiges Schema."

    # Python-Code erst probeweise schreiben und laden — nichts wird dauerhaft
    # registriert, solange der Code nicht sauber importiert und aufrufbar ist.
    py_file.write_text(python_code, encoding="utf-8")

    tools_str = str(CUSTOM_TOOLS_DIR)
    if tools_str not in sys.path:
        sys.path.insert(0, tools_str)

    try:
        if module_name in sys.modules:
            mod = importlib.reload(sys.modules[module_name])
        else:
            mod = importlib.import_module(module_name)
        func = getattr(mod, func_name)
        if not callable(func):
            raise TypeError(f"{func_name} ist nicht aufrufbar")
    except Exception as e:
        # Fehlerhaften Code sofort wieder entfernen, statt eine kaputte Datei liegen zu lassen
        try:
            py_file.unlink()
        except Exception:
            pass
        sys.modules.pop(module_name, None)
        return f"Tool '{tool_name}' konnte nicht geladen werden und wurde verworfen: {e}"

    # Erst jetzt, nach erfolgreichem Test-Import, dauerhaft registrieren
    try:
        defs = json.loads(CUSTOM_TOOLS_JSON.read_text(encoding="utf-8"))
        if not isinstance(defs, list):
            defs = []
    except Exception:
        defs = []

    defs = [d for d in defs if d.get("definition", {}).get("name") != tool_name]
    defs.append({
        "definition": tool_def,
        "module":     module_name,
        "function":   func_name,
    })
    _save_defs(defs)

    _dynamic_definitions.append(tool_def)
    _dynamic_handlers[tool_name] = func
    return f"Neues Tool '{tool_name}' erfolgreich erstellt und aktiviert! Du kannst es ab sofort benutzen."


def list_custom_tools() -> str:
    """Listet alle selbst erstellten Tools auf."""
    _ensure_dirs()
    try:
        defs = json.loads(CUSTOM_TOOLS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return "Noch keine eigenen Tools erstellt."

    if not defs:
        return "Noch keine eigenen Tools erstellt."

    lines = [f"Eigene Tools ({len(defs)}):"]
    for d in defs:
        defn = d.get("definition", {})
        lines.append(f"  • {defn.get('name', '?')} — {defn.get('description', '')[:60]}")
    return "\n".join(lines)
