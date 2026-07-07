import asyncio
import threading
from pathlib import Path

_browser = None
_page = None
_playwright = None
_lock = threading.Lock()


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _ensure_browser():
    global _browser, _page, _playwright
    from playwright.async_api import async_playwright
    if _browser is None or not _browser.is_connected():
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(headless=False, slow_mo=50)
        context = await _browser.new_context()
        _page = await context.new_page()
    return _page


def browser_navigate(url: str) -> str:
    try:
        if not url.startswith("http"):
            url = "https://" + url

        async def _go():
            page = await _ensure_browser()
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            title = await page.title()
            return title

        with _lock:
            title = _run_async(_go())
        return f"Seite geöffnet: {title} ({url})"
    except Exception as e:
        return f"Navigation fehlgeschlagen: {e}"


def browser_click(selector: str) -> str:
    try:
        async def _click():
            page = await _ensure_browser()
            await page.click(selector, timeout=5000)
            return "Geklickt"

        with _lock:
            _run_async(_click())
        return f"Element geklickt: {selector}"
    except Exception as e:
        return f"Klick fehlgeschlagen: {e}"


def browser_type(selector: str, text: str) -> str:
    try:
        async def _type():
            page = await _ensure_browser()
            await page.fill(selector, text)

        with _lock:
            _run_async(_type())
        return f"Text eingegeben in {selector}: {text}"
    except Exception as e:
        return f"Texteingabe fehlgeschlagen: {e}"


def browser_get_text() -> str:
    try:
        async def _get():
            page = await _ensure_browser()
            text = await page.inner_text("body")
            return text[:3000]

        with _lock:
            text = _run_async(_get())
        return f"Seiteninhalt: {text}"
    except Exception as e:
        return f"Text lesen fehlgeschlagen: {e}"


def browser_screenshot(save_path: str = None) -> str:
    try:
        if not save_path:
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(Path.home() / "Desktop" / f"browser_{ts}.png")

        async def _shot():
            page = await _ensure_browser()
            await page.screenshot(path=save_path, full_page=False)

        with _lock:
            _run_async(_shot())
        return f"Browser-Screenshot gespeichert: {save_path}"
    except Exception as e:
        return f"Browser-Screenshot fehlgeschlagen: {e}"


def browser_search_google(query: str) -> str:
    try:
        import urllib.parse
        url = f"https://www.google.de/search?q={urllib.parse.quote(query)}"

        async def _search():
            page = await _ensure_browser()
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            results = []
            items = await page.query_selector_all("h3")
            for item in items[:5]:
                text = await item.inner_text()
                if text.strip():
                    results.append(text.strip())
            return results

        with _lock:
            results = _run_async(_search())

        if results:
            return f"Google-Suche '{query}': " + " | ".join(results)
        return f"Suche nach '{query}' durchgeführt, keine Ergebnisse extrahiert."
    except Exception as e:
        return f"Google-Suche fehlgeschlagen: {e}"


def browser_fill_form(fields: dict) -> str:
    try:
        async def _fill():
            page = await _ensure_browser()
            for selector, value in fields.items():
                await page.fill(selector, str(value))

        with _lock:
            _run_async(_fill())
        return f"Formular ausgefüllt: {list(fields.keys())}"
    except Exception as e:
        return f"Formular ausfüllen fehlgeschlagen: {e}"


def browser_scroll(direction: str = "down", amount: int = 500) -> str:
    try:
        async def _scroll():
            page = await _ensure_browser()
            dy = amount if direction == "down" else -amount
            await page.evaluate(f"window.scrollBy(0, {dy})")

        with _lock:
            _run_async(_scroll())
        return f"Gescrollt: {direction}"
    except Exception as e:
        return f"Scrollen fehlgeschlagen: {e}"


def browser_close() -> str:
    global _browser, _page, _playwright
    try:
        async def _close():
            global _browser, _page, _playwright
            if _page:
                await _page.close()
            if _browser:
                await _browser.close()
            if _playwright:
                await _playwright.stop()
            _browser = _page = _playwright = None

        _run_async(_close())
        return "Browser geschlossen."
    except Exception as e:
        return f"Browser schließen fehlgeschlagen: {e}"
