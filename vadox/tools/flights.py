"""
Flugsuche Tool — sucht Flüge via Google Flights / Kayak ohne API-Key.
Öffnet Browser mit vorausgefüllter Suche und gibt direkten Link zurück.
"""
import webbrowser
import urllib.parse
from datetime import datetime, timedelta


# Häufige IATA-Codes für deutsche Städte
AIRPORT_CODES = {
    "berlin":     "BER",
    "münchen":    "MUC",
    "munich":     "MUC",
    "frankfurt":  "FRA",
    "hamburg":    "HAM",
    "düsseldorf": "DUS",
    "dusseldorf": "DUS",
    "köln":       "CGN",
    "cologne":    "CGN",
    "stuttgart":  "STR",
    "nürnberg":   "NUE",
    "nuremberg":  "NUE",
    "hannover":   "HAJ",
    "vienna":     "VIE",
    "wien":       "VIE",
    "zürich":     "ZRH",
    "zurich":     "ZRH",
    "paris":      "CDG",
    "london":     "LHR",
    "amsterdam":  "AMS",
    "barcelona":  "BCN",
    "madrid":     "MAD",
    "rome":       "FCO",
    "rom":        "FCO",
    "istanbul":   "IST",
    "dubai":      "DXB",
    "new york":   "JFK",
    "los angeles":"LAX",
    "tokyo":      "NRT",
    "tokio":      "NRT",
    "bangkok":    "BKK",
    "singapur":   "SIN",
    "singapore":  "SIN",
}


def _resolve_airport(city: str) -> str:
    """Gibt IATA-Code zurück wenn bekannt, sonst den Input."""
    return AIRPORT_CODES.get(city.lower().strip(), city.upper().strip())


def search_flights(
    origin: str,
    destination: str,
    date: str = "",
    return_date: str = "",
    passengers: int = 1,
) -> str:
    """
    Sucht Flüge und öffnet Google Flights im Browser.

    origin:      Abflugort (Stadt oder IATA-Code)
    destination: Zielort (Stadt oder IATA-Code)
    date:        Abflugdatum (TT.MM.JJJJ oder 'morgen', 'übermorgen', 'nächste woche')
    return_date: Rückflugdatum (leer = nur Hinflug)
    passengers:  Anzahl Passagiere
    """
    try:
        orig = _resolve_airport(origin)
        dest = _resolve_airport(destination)

        # Datum auflösen
        dep_date = _parse_date(date)
        ret_date = _parse_date(return_date) if return_date else ""

        # Google Flights URL aufbauen
        if ret_date:
            url = (
                f"https://www.google.com/travel/flights/search?"
                f"tfs=CBwQAhoeEgoyMDI1LTAxLTAxagcIARIDe3tvcmlnfX1yBwgBEgN7e2Rlc3R9fQ"
            )
            # Einfachere direkte URL
            url = f"https://www.google.com/travel/flights?q=Flüge+von+{orig}+nach+{dest}+am+{dep_date}"
        else:
            url = f"https://www.google.com/travel/flights?q=Flüge+von+{orig}+nach+{dest}+am+{dep_date}"

        # Kayak als Alternative (oft besser für direkte Suche)
        kayak_url = _build_kayak_url(orig, dest, dep_date, ret_date, passengers)

        webbrowser.open(kayak_url)

        msg = (
            f"Flugsuche geöffnet:\n"
            f"Von: {orig} ({origin})\n"
            f"Nach: {dest} ({destination})\n"
            f"Abflug: {dep_date or 'flexibel'}\n"
        )
        if ret_date:
            msg += f"Rückflug: {ret_date}\n"
        msg += f"Passagiere: {passengers}\n\n"
        msg += f"Kayak: {kayak_url}\n"
        msg += f"Google Flights: {url}"

        return msg

    except Exception as e:
        return f"Flugsuche Fehler: {e}"


def _build_kayak_url(orig: str, dest: str, dep: str, ret: str, pax: int) -> str:
    """Baut Kayak-Such-URL auf."""
    # Kayak Datumsformat: JJJJ-MM-TT
    dep_k = _convert_to_iso(dep)
    base  = f"https://www.kayak.de/flights/{orig}-{dest}/{dep_k}"
    if ret:
        ret_k  = _convert_to_iso(ret)
        base  += f"/{ret_k}"
    base += f"/{pax}adults"
    return base


def _parse_date(date_str: str) -> str:
    """Wandelt Datumsangaben in TT.MM.JJJJ um."""
    if not date_str:
        return ""
    today = datetime.today()
    d = date_str.lower().strip()
    if d in ("heute", "today"):
        return today.strftime("%d.%m.%Y")
    if d in ("morgen", "tomorrow"):
        return (today + timedelta(days=1)).strftime("%d.%m.%Y")
    if d in ("übermorgen", "day after tomorrow"):
        return (today + timedelta(days=2)).strftime("%d.%m.%Y")
    if "nächste woche" in d or "next week" in d:
        return (today + timedelta(weeks=1)).strftime("%d.%m.%Y")
    return date_str  # Schon im richtigen Format


def _convert_to_iso(date_str: str) -> str:
    """Wandelt TT.MM.JJJJ in JJJJ-MM-TT um."""
    if not date_str:
        return datetime.today().strftime("%Y-%m-%d")
    parts = date_str.split(".")
    if len(parts) == 3:
        return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
    return date_str


def get_cheap_flights(destination: str, from_city: str = "Frankfurt") -> str:
    """Sucht günstige Flüge zu einem Ziel (flexibles Datum)."""
    orig = _resolve_airport(from_city)
    dest = _resolve_airport(destination)

    # Skyscanner flexible Suche
    url = f"https://www.skyscanner.de/transport/flüge/{orig.lower()}/{dest.lower()}/"
    webbrowser.open(url)
    return (
        f"Skyscanner geöffnet für günstige Flüge:\n"
        f"Von {from_city} ({orig}) nach {destination} ({dest})\n"
        f"Flexibles Datum — beste Preise werden angezeigt."
    )


def check_flight_status(flight_number: str) -> str:
    """Prüft den Status eines Fluges (z.B. LH123)."""
    url = f"https://www.flightradar24.com/data/flights/{flight_number.upper()}"
    webbrowser.open(url)
    return f"Flugstatus für {flight_number.upper()} auf FlightRadar24 geöffnet."
