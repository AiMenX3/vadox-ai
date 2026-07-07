import threading
from vadox.core.tool_definitions import TOOLS
from vadox.core.tool_executor import execute_tool
from vadox.core import memory
from vadox.core.dynamic_tools import load_dynamic_tools, get_dynamic_definitions, execute_dynamic_tool

# Dynamische Tools beim Start laden — darf niemals die KI-Engine selbst lahmlegen,
# sonst würde ein einziges kaputtes selbstgeschriebenes Tool den ganzen Chat blockieren.
try:
    load_dynamic_tools()
except Exception as e:
    print(f"[DynTools] Laden der dynamischen Tools fehlgeschlagen, überspringe: {e}")

BASE_SYSTEM_DE = """Du bist Vadox, ein hochentwickelter KI-Assistent für den Desktop.
Du antwortest auf Deutsch, präzise und direkt.
Du verwendest in deinen Antworten keine Markdown-Formatierungen wie Rauten, Sternchen, Bindestriche als Aufzählungen oder Emojis.
Schreibe in klaren, natürlichen Sätzen ohne Sonderzeichen.
Du hast Zugriff auf Tools für Wetter, Websuche, Dateiverwaltung, Browser-Automation und PC-Steuerung.
Nutze diese Tools aktiv wenn der Nutzer nach aktuellen Infos, Wetter, Dateien, Browser-Aktionen oder Systeminformationen fragt.
Wenn der Nutzer dir etwas über sich erzählt (Name, Beruf, Vorlieben), nutze das remember_fact Tool um es zu speichern.
Nach einem Tool-Aufruf formuliere die Antwort als natürlichen Satz ohne Aufzählungszeichen.

WICHTIG für open_application: Wenn der Nutzer eine App öffnen möchte, übergib den Namen GENAU so wie der Nutzer ihn gesagt hat, ohne ihn umzuschreiben oder zu übersetzen. Das System sucht die App selbst auf dem Computer. Beispiele: "roblox studio" -> app_name="roblox studio", "metin2" -> app_name="metin2", "discord" -> app_name="discord". Niemals den Namen in einen Dateipfad oder exe-Namen umwandeln.

SELBSTENTWICKLUNG: Du kannst neue Tools erstellen mit create_new_tool. Wenn ein Nutzer eine Funktion wünscht die du nicht hast, schreibe selbst den Python-Code dafür und registriere ihn. Nutze add_user_rule für "Wenn X dann Y"-Regeln. Nutze add_user_instruction für dauerhafte Verhaltensänderungen.

COMPUTER USE — DESKTOP & BROWSER STEUERN:
Du kannst den Bildschirm sehen und vollständig steuern. Nutze diese Tools IMMER wenn der Nutzer möchte dass du etwas auf dem Bildschirm tust:
- computer_read_screen: Zuerst aufrufen um zu sehen was auf dem Bildschirm ist
- computer_find_and_click: Element auf dem Bildschirm suchen und anklicken (z.B. "Vorname Feld", "Speichern Button")
- computer_type: Text in aktives Feld eintippen
- computer_key: Tasten drücken (enter, tab, ctrl+v usw.)
- computer_scroll: Scrollen
- computer_drag: Drag & Drop
- browser_computer_use: Browser öffnen und komplexe Web-Aufgaben erledigen (Facebook posten, WordPress bearbeiten usw.)
WICHTIG: Niemals sagen dass du den Bildschirm nicht sehen kannst — nutze immer computer_read_screen zuerst!
Arbeite Schritt für Schritt: Lesen → Klicken → Tippen → Bestätigen → Prüfen."""

BASE_SYSTEM_EN = """You are Vadox, a highly advanced AI assistant for the desktop.
You respond in English, concisely and directly.
Do not use Markdown formatting such as hashes, asterisks, dashes for bullet points or emojis in your responses.
Write in clear, natural sentences without special characters.
You have access to tools for weather, web search, file management, browser automation and PC control.
Use these tools actively when the user asks about current information, weather, files, browser actions or system information.
When the user tells you something about themselves (name, job, preferences), use the remember_fact tool to save it.
After a tool call, formulate the response as a natural sentence without bullet points.

IMPORTANT for open_application: When the user wants to open an app, pass the name EXACTLY as the user said it, without rewriting or translating it. The system finds the app itself on the computer.

SELF-DEVELOPMENT: You can create new tools with create_new_tool. If a user wants a function you don't have, write the Python code yourself and register it. Use add_user_rule for "When X then Y" rules. Use add_user_instruction for permanent behavior changes."""


def _get_language() -> str:
    """Gibt die eingestellte Sprache zurück ('de' oder 'en')."""
    try:
        from vadox.core import settings
        cfg = settings.load()
        lang = cfg.get("ui_language", "de")
        return lang if lang in ("de", "en") else "de"
    except Exception:
        return "de"


def _build_system() -> str:
    from vadox.core.user_rules import build_rules_context
    from vadox.core.feedback import build_feedback_context
    from datetime import datetime
    import locale

    lang = _get_language()
    sys_prompt = BASE_SYSTEM_EN if lang == "en" else BASE_SYSTEM_DE

    # Aktuelles Datum und Uhrzeit vom System
    now = datetime.now()
    if lang == "en":
        dt_str = now.strftime("Today is %A, %B %d, %Y. Current time: %H:%M.")
    else:
        tage = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
        monate = ["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
        dt_str = f"Heute ist {tage[now.weekday()]}, der {now.day}. {monate[now.month-1]} {now.year}. Aktuelle Uhrzeit: {now.strftime('%H:%M')} Uhr."
    sys_prompt += f"\n\n{dt_str}"

    ctx = memory.build_context()
    if ctx:
        label = "What you know about the user:" if lang == "en" else "Was du über den Nutzer weißt:"
        sys_prompt += f"\n\n{label} {ctx}"

    rules_ctx = build_rules_context()
    if rules_ctx:
        sys_prompt += f"\n\n{rules_ctx}"

    feedback_ctx = build_feedback_context()
    if feedback_ctx:
        sys_prompt += f"\n\n{feedback_ctx}"

    return sys_prompt


def _all_tools() -> list:
    """Kombiniert Standard-Tools + dynamisch erstellte Tools."""
    return TOOLS + get_dynamic_definitions()


# Diese Tools werden für Claude durch Anthropics eigenes, serverseitiges
# web_search-Tool ersetzt (schneller, aktueller, kein DDG-Scraping) —
# sonst gäbe es einen Namenskonflikt zwischen dem clientseitigen Tool
# "web_search" und Anthropics eingebautem Tool gleichen Namens.
_CLAUDE_NATIVE_SEARCH_TOOLS = {"web_search", "news_search"}


def _claude_tools() -> list:
    """Tool-Liste für Claude: DDG-basierte Such-Tools raus, natives
    Claude-Websuche-Tool rein."""
    tools = [t for t in _all_tools() if t["name"] not in _CLAUDE_NATIVE_SEARCH_TOOLS]
    tools.append({"type": "web_search_20260209", "name": "web_search"})
    return tools


def _execute_any_tool(name: str, inputs: dict) -> str:
    """Führt Standard- oder dynamisches Tool aus."""
    result = execute_dynamic_tool(name, inputs)
    if result is not None:
        return result
    return execute_tool(name, inputs)


# ── Gemini Tool-Format-Konverter ─────────────────────────────────────────────

# Diese Tools werden für Gemini durch Googles eigenes Grounding-Suchtool ersetzt
# (schneller, aktueller, kein DDG-Scraping) — analog zu Claudes natives web_search.
_GEMINI_NATIVE_SEARCH_TOOLS = {"web_search", "news_search"}


def _sanitize_schema_for_gemini(schema):
    """Entfernt Felder, die Geminis Schema-Proto nicht kennt (z.B. 'default'),
    rekursiv über properties/items hinweg."""
    if isinstance(schema, dict):
        cleaned = {k: _sanitize_schema_for_gemini(v) for k, v in schema.items() if k != "default"}
        return cleaned
    if isinstance(schema, list):
        return [_sanitize_schema_for_gemini(v) for v in schema]
    return schema


def _tools_for_gemini():
    from google.generativeai.types import FunctionDeclaration, Tool
    declarations = []
    for t in _all_tools():
        if t["name"] in _GEMINI_NATIVE_SEARCH_TOOLS:
            continue
        declarations.append(FunctionDeclaration(
            name=t["name"],
            description=t["description"],
            parameters=_sanitize_schema_for_gemini(t["input_schema"]),
        ))
    return [
        Tool(function_declarations=declarations),
        Tool(google_search_retrieval={}),
    ]


# Diese Tools werden für OpenRouter durch das native ":online"-Web-Plugin
# ersetzt (schneller, aktueller, kein DDG-Scraping) — analog zu Claude/Gemini.
_OPENROUTER_NATIVE_SEARCH_TOOLS = {"web_search", "news_search"}


# ── OpenAI-kompatibler Client (für OpenAI, OpenRouter, Ollama) ───────────────
def _make_openai_client(provider: str, api_key: str):
    from openai import OpenAI
    if provider == "openrouter":
        return OpenAI(
            api_key=api_key or "dummy",
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://vadox.ai",
                "X-Title": "Vadox",
            }
        )
    elif provider == "ollama":
        return OpenAI(
            api_key="ollama",
            base_url="http://localhost:11434/v1",
        )
    else:
        return OpenAI(api_key=api_key)


def test_api_connection(provider: str, key: str, model: str) -> tuple[bool, str]:
    """Schickt eine minimale Testanfrage, um einen API-Key sofort zu validieren
    statt den Nutzer erst beim ersten echten Chat scheitern zu lassen."""
    try:
        if provider == "claude":
            from anthropic import Anthropic
            c = Anthropic(api_key=key)
            c.messages.create(model=model, max_tokens=10,
                               messages=[{"role": "user", "content": "Hi"}])
            return True, "Verbunden"
        elif provider in ("openai", "openrouter", "ollama"):
            c = _make_openai_client(provider, key)
            if provider == "ollama":
                import requests
                r = requests.get("http://localhost:11434/api/tags", timeout=4)
                models_list = [m["name"] for m in r.json().get("models", [])]
                if models_list:
                    return True, f"Verbunden — {len(models_list)} Modelle gefunden"
                return True, "Ollama läuft — noch kein Modell installiert (ollama pull llama3.3)"
            c.chat.completions.create(
                model=model, max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True, "Verbunden"
        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=key)
            m = genai.GenerativeModel(model)
            m.generate_content("Hi")
            return True, "Verbunden"
        return False, f"Unbekannter Provider: {provider}"
    except Exception as e:
        msg = str(e)
        low = msg.lower()
        if "authentication" in low or "api key" in low or "401" in low or "invalid_api_key" in low or "unauthorized" in low:
            return False, "API-Key ungültig — bitte prüfen."
        if "429" in low or "rate limit" in low or "quota" in low or "insufficient_quota" in low:
            return False, "Kein Guthaben/Kontingent auf diesem Account."
        return False, f"Verbindung fehlgeschlagen: {msg[:120]}"


# ── Haupt-Engine ─────────────────────────────────────────────────────────────
class AIEngine:
    # Modelle pro Provider
    PROVIDERS = {
        "claude":      ["claude-opus-4-8", "claude-sonnet-5", "claude-haiku-4-5"],
        "openai":      ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "gemini":      ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
        "openrouter":  [
            "anthropic/claude-sonnet-4-5",
            "openai/gpt-4o",
            "google/gemini-2.0-flash-001",
            "meta-llama/llama-3.3-70b-instruct",
            "mistralai/mistral-large",
            "deepseek/deepseek-r1",
            "qwen/qwen-2.5-72b-instruct",
        ],
        "ollama":      [
            "llama3.3",
            "llama3.1",
            "mistral",
            "gemma3",
            "phi4",
            "qwen2.5",
            "deepseek-r1",
        ],
    }

    def __init__(self, provider: str = "claude", api_key: str = "",
                 model: str = "claude-sonnet-5"):
        self.provider = provider
        self.api_key  = api_key
        self.model    = model
        self.history  = []
        self._client  = None
        self._init_client()

    def _init_client(self):
        if self.provider == "claude":
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        elif self.provider in ("openai", "openrouter", "ollama"):
            self._client = _make_openai_client(self.provider, self.api_key)
        elif self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=_build_system(),
                tools=_tools_for_gemini(),
            )

    def reconfigure(self, provider: str, api_key: str, model: str):
        self.provider = provider
        self.api_key  = api_key
        self.model    = model
        self.history  = []
        self._init_client()

    def chat(self, user_message: str, on_chunk=None, on_done=None, on_tool_use=None):
        thread = threading.Thread(
            target=self._route,
            args=(user_message, on_chunk, on_done, on_tool_use),
            daemon=True
        )
        thread.start()

    def _route(self, msg, on_chunk, on_done, on_tool_use):
        if self.provider == "claude":
            self._chat_claude(msg, on_chunk, on_done, on_tool_use)
        elif self.provider in ("openai", "openrouter", "ollama"):
            self._chat_openai(msg, on_chunk, on_done, on_tool_use)
        elif self.provider == "gemini":
            self._chat_gemini(msg, on_chunk, on_done, on_tool_use)

    # ── Claude ────────────────────────────────────────────────────────────────
    def _chat_claude(self, user_message, on_chunk, on_done, on_tool_use):
        self.history.append({"role": "user", "content": user_message})
        full_response = ""
        try:
            messages = list(self.history)
            while True:
                round_text = ""
                with self._client.messages.stream(
                    model=self.model,
                    max_tokens=4096,
                    system=_build_system(),
                    tools=_claude_tools(),
                    messages=messages,
                ) as stream:
                    for event in stream:
                        if event.type == "content_block_delta" and event.delta.type == "text_delta":
                            round_text += event.delta.text
                            if on_chunk:
                                on_chunk(event.delta.text)
                    response = stream.get_final_message()

                if response.stop_reason == "tool_use":
                    full_response += round_text
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            if on_tool_use:
                                on_tool_use(block.name)
                            result = _execute_any_tool(block.name, block.input)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result,
                            })
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})
                    continue
                if response.stop_reason == "pause_turn":
                    # Anthropics serverseitige Websuche hat ihr internes
                    # Iterationslimit erreicht — unverändert weiterlaufen lassen,
                    # der Server macht dort weiter, wo er aufgehört hat.
                    full_response += round_text
                    messages.append({"role": "assistant", "content": response.content})
                    continue
                if response.stop_reason == "max_tokens":
                    err = "Die Antwort war zu lang. Bitte formuliere die Anfrage kürzer."
                    if on_chunk: on_chunk(err)
                    full_response = err
                    break
                full_response += round_text
                if not full_response:
                    err = "Keine Antwort erhalten. Bitte versuche es nochmal."
                    if on_chunk: on_chunk(err)
                    full_response = err
                break
            self.history.append({"role": "assistant", "content": full_response})
        except Exception as e:
            import traceback, sys
            tb = traceback.format_exc()
            err = f"Claude Fehler: {e}"
            # Fehler in Log-Datei schreiben
            try:
                log_path = (
                    Path(sys.executable).parent / "vadox_ai_error.log"
                    if getattr(sys, 'frozen', False)
                    else Path(__file__).parent.parent.parent / "vadox_ai_error.log"
                )
                with open(log_path, "a", encoding="utf-8") as f:
                    from datetime import datetime
                    f.write(f"\n[{datetime.now()}] MODEL={self.model}\n{tb}\n")
            except Exception:
                pass
            if on_chunk: on_chunk(err)
            full_response = err
        finally:
            if on_done: on_done(full_response)

    # ── OpenAI / OpenRouter / Ollama ─────────────────────────────────────────
    def _chat_openai(self, user_message, on_chunk, on_done, on_tool_use):
        import json
        self.history.append({"role": "user", "content": user_message})
        full_response = ""
        try:
            # Ollama hat begrenzte Tool-Unterstützung — ohne Tools wenn Modell es nicht kann
            use_tools = self.provider != "ollama"

            # OpenRouter: natives Web-Plugin (":online"-Suffix) ersetzt die
            # DDG-basierten Such-Tools — schneller, aktueller, kein Scraping.
            is_openrouter_online = self.provider == "openrouter"
            skip_tools = _OPENROUTER_NATIVE_SEARCH_TOOLS if is_openrouter_online else set()

            oai_tools = []
            if use_tools:
                for t in _all_tools():
                    if t["name"] in skip_tools:
                        continue
                    oai_tools.append({
                        "type": "function",
                        "function": {
                            "name": t["name"],
                            "description": t["description"],
                            "parameters": t["input_schema"],
                        }
                    })

            messages = [{"role": "system", "content": _build_system()}] + list(self.history)

            model_name = self.model
            if is_openrouter_online and not model_name.endswith(":online"):
                model_name = f"{model_name}:online"

            kwargs = dict(
                model=model_name,
                messages=messages,
                max_tokens=4096,
            )
            if use_tools and oai_tools:
                kwargs["tools"] = oai_tools
                kwargs["tool_choice"] = "auto"

            # OpenRouter: Extra-Header für Modell-Auswahl
            if self.provider == "openrouter":
                kwargs["extra_headers"] = {
                    "HTTP-Referer": "https://vadox.ai",
                    "X-Title": "Vadox",
                }

            while True:
                response = self._client.chat.completions.create(**kwargs)
                choice = response.choices[0]

                if use_tools and choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                    tool_calls = choice.message.tool_calls
                    messages.append(choice.message)
                    for tc in tool_calls:
                        if on_tool_use:
                            on_tool_use(tc.function.name)
                        try:
                            args = json.loads(tc.function.arguments)
                        except Exception:
                            args = {}
                        result = _execute_any_tool(tc.function.name, args)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result,
                        })
                    kwargs["messages"] = messages
                    continue

                text = choice.message.content or ""
                full_response = text
                if on_chunk: on_chunk(text)
                break

            self.history.append({"role": "assistant", "content": full_response})
        except Exception as e:
            provider_name = {
                "openai": "OpenAI",
                "openrouter": "OpenRouter",
                "ollama": "Ollama",
            }.get(self.provider, self.provider)
            err = f"{provider_name} Fehler: {e}"
            if self.provider == "ollama" and "connection" in str(e).lower():
                err = "Ollama nicht erreichbar. Bitte Ollama starten: ollama serve"
            if on_chunk: on_chunk(err)
            full_response = err
        finally:
            if on_done: on_done(full_response)

    # ── Gemini ────────────────────────────────────────────────────────────────
    def _chat_gemini(self, user_message, on_chunk, on_done, on_tool_use):
        full_response = ""
        try:
            import google.generativeai as genai
            chat = self._client.start_chat(history=[])

            while True:
                response = chat.send_message(user_message)
                part = response.candidates[0].content.parts[0]

                if hasattr(part, "function_call") and part.function_call.name:
                    fc = part.function_call
                    if on_tool_use:
                        on_tool_use(fc.name)
                    args = dict(fc.args)
                    result = _execute_any_tool(fc.name, args)
                    user_message = f"Tool-Ergebnis für {fc.name}: {result}. Antworte jetzt dem Nutzer."
                    continue

                full_response = part.text
                if on_chunk: on_chunk(full_response)
                break

            self.history.append({"role": "assistant", "content": full_response})
        except Exception as e:
            err = f"Gemini Fehler: {e}"
            if on_chunk: on_chunk(err)
            full_response = err
        finally:
            if on_done: on_done(full_response)

    def clear_history(self):
        self.history = []
