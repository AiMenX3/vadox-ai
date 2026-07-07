"""
PDF-Analyse — Dokument einlesen und mit KI zusammenfassen.
"""
import os
from pathlib import Path


def _extract_text_pymupdf(pdf_path: str) -> str:
    """Text aus PDF extrahieren mit PyMuPDF (fitz)."""
    import fitz
    doc  = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def _extract_text_pypdf(pdf_path: str) -> str:
    """Fallback: pypdf."""
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_pdf_text(pdf_path: str) -> str:
    """Extrahiert Text aus einem PDF."""
    if not os.path.exists(pdf_path):
        return f"Datei nicht gefunden: {pdf_path}"
    try:
        return _extract_text_pymupdf(pdf_path)
    except ImportError:
        pass
    try:
        return _extract_text_pypdf(pdf_path)
    except ImportError:
        return "PDF-Bibliothek fehlt. Bitte 'pip install pymupdf' ausführen."
    except Exception as e:
        return f"PDF-Lesefehler: {e}"


def analyze_pdf(pdf_path: str, question: str = "") -> str:
    """
    Liest ein PDF und sendet den Inhalt zur KI-Analyse.
    Gibt eine Zusammenfassung oder Antwort auf die Frage zurück.
    """
    text = extract_pdf_text(pdf_path)
    if not text or len(text.strip()) < 20:
        return f"Das PDF '{Path(pdf_path).name}' enthält keinen lesbaren Text (eventuell gescannt)."

    # Text kürzen falls zu lang (max ~12.000 Zeichen für den API-Kontext)
    max_chars = 12000
    truncated = False
    if len(text) > max_chars:
        text = text[:max_chars]
        truncated = True

    name     = Path(pdf_path).name
    pages_est = text.count('\f') + 1

    if question:
        prompt = f"Frage zum PDF '{name}': {question}\n\nPDF-Inhalt:\n{text}"
    else:
        prompt = (
            f"Fasse das folgende PDF-Dokument '{name}' professionell zusammen. "
            f"Erkenne Typ (Vertrag, Rechnung, Bericht, etc.) und hebe wichtige Punkte hervor.\n\n"
            f"PDF-Inhalt:\n{text}"
        )

    if truncated:
        prompt += f"\n\n[Hinweis: Nur die ersten {max_chars} Zeichen wurden analysiert.]"

    # Direkt an KI weitergeben — tool_executor ruft diese Funktion auf
    # und das Ergebnis geht als Tool-Result zurück an Claude
    return f"__PDF_ANALYZE__{prompt}"


def find_pdfs_on_desktop() -> str:
    """Sucht nach PDFs auf dem Desktop und in Downloads."""
    locations = [Path.home() / "Desktop", Path.home() / "Downloads"]
    found = []
    for loc in locations:
        if loc.exists():
            for pdf in loc.glob("*.pdf"):
                size_mb = pdf.stat().st_size / 1024 / 1024
                found.append(f"  • {pdf.name} ({size_mb:.1f} MB) — {pdf}")
    if not found:
        return "Keine PDFs auf dem Desktop oder in Downloads gefunden."
    return "Gefundene PDFs:\n" + "\n".join(found[:20])
