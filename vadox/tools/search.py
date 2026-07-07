try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results, region="de-de"))
        if not results:
            return "Keine Suchergebnisse gefunden."

        lines = [f"Suchergebnisse für '{query}':"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            body = r.get("body", "")[:200]
            lines.append(f"{i}. {title}: {body}")
        return " | ".join(lines)
    except Exception as e:
        return f"Websuche fehlgeschlagen: {e}"


def news_search(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results, region="de-de"))
        if not results:
            return "Keine Nachrichten gefunden."

        lines = [f"Aktuelle Nachrichten zu '{query}':"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            source = r.get("source", "")
            body = r.get("body", "")[:150]
            lines.append(f"{i}. {title} ({source}): {body}")
        return " | ".join(lines)
    except Exception as e:
        return f"Nachrichtensuche fehlgeschlagen: {e}"
