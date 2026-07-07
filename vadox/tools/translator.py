# -*- coding: utf-8 -*-
"""
Vadox Übersetzer — 50+ Sprachen, kostenlos via deep-translator
"""
from deep_translator import GoogleTranslator

LANGUAGES = {
    "deutsch":     "de",
    "englisch":    "en",
    "spanisch":    "es",
    "franzoesisch":"fr",
    "italienisch": "it",
    "portugiesisch":"pt",
    "niederlaendisch":"nl",
    "polnisch":    "pl",
    "russisch":    "ru",
    "chinesisch":  "zh-CN",
    "japanisch":   "ja",
    "koreanisch":  "ko",
    "arabisch":    "ar",
    "tuerkisch":   "tr",
    "schwedisch":  "sv",
    "norwegisch":  "no",
    "daenisch":    "da",
    "finnisch":    "fi",
    "griechisch":  "el",
    "ungarisch":   "hu",
    "tschechisch": "cs",
    "rumaenisch":  "ro",
    "ukrainisch":  "uk",
    "hindi":       "hi",
    "vietnamesisch":"vi",
    "indonesisch": "id",
    "thaiisch":    "th",
}

LANG_NAMES = {v: k.capitalize() for k, v in LANGUAGES.items()}


def _resolve_lang(name: str) -> str:
    """Sprachname -> Sprachcode. Akzeptiert Namen und Codes."""
    n = name.lower().strip()
    if n in LANGUAGES:
        return LANGUAGES[n]
    # Direkter Code z.B. "en", "de"
    if n in LANG_NAMES:
        return n
    # Teilmatch
    for key, code in LANGUAGES.items():
        if n in key or key in n:
            return code
    return "en"


def translate_text(text: str, target_lang: str = "en", source_lang: str = "auto") -> str:
    """
    Übersetzt Text in die Zielsprache.
    target_lang: Sprachname auf Deutsch ODER Sprachcode (de, en, es...)
    """
    try:
        target_code = _resolve_lang(target_lang)
        translator = GoogleTranslator(source=source_lang, target=target_code)
        result = translator.translate(text)
        target_name = LANG_NAMES.get(target_code, target_lang.capitalize())
        return f"[{target_name}] {result}"
    except Exception as e:
        return f"Übersetzung fehlgeschlagen: {e}"


def detect_language(text: str) -> str:
    """Erkennt die Sprache eines Textes."""
    try:
        from deep_translator import single_detection
        code = single_detection(text, api_key=None)
        name = LANG_NAMES.get(code, code)
        return f"Erkannte Sprache: {name} ({code})"
    except Exception:
        try:
            # Fallback via GoogleTranslator
            t = GoogleTranslator(source="auto", target="de")
            t.translate(text[:50])
            return "Sprache erkannt (auto-detect)"
        except Exception as e:
            return f"Erkennung fehlgeschlagen: {e}"


def get_supported_languages() -> str:
    langs = [f"{name.capitalize()} ({code})" for name, code in LANGUAGES.items()]
    return "Unterstützte Sprachen:\n" + ", ".join(langs)
