import requests
from datetime import datetime, timedelta


WMO_CODES = {
    0: "klarer Himmel", 1: "überwiegend klar", 2: "teilweise bewölkt", 3: "bedeckt",
    45: "neblig", 48: "gefrierender Nebel",
    51: "leichter Nieselregen", 53: "mäßiger Nieselregen", 55: "starker Nieselregen",
    61: "leichter Regen", 63: "mäßiger Regen", 65: "starker Regen",
    71: "leichter Schneefall", 73: "mäßiger Schneefall", 75: "starker Schneefall",
    80: "leichte Schauer", 81: "mäßige Schauer", 82: "starke Schauer",
    95: "Gewitter", 96: "Gewitter mit Hagel", 99: "starkes Gewitter mit Hagel",
}


def get_coords(city: str) -> tuple[float, float, str]:
    resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "de"},
        timeout=5
    )
    results = resp.json().get("results", [])
    if not results:
        raise ValueError(f"Stadt '{city}' nicht gefunden.")
    r = results[0]
    return r["latitude"], r["longitude"], r["name"]


def get_weather(city: str = "Berlin", days: int = 1) -> str:
    try:
        lat, lon, name = get_coords(city)
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum,windspeed_10m_max",
                "current_weather": True,
                "timezone": "auto",
                "forecast_days": min(days + 1, 7),
            },
            timeout=5
        )
        data = resp.json()
        current = data.get("current_weather", {})
        daily = data.get("daily", {})

        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        codes = daily.get("weathercode", [])
        precip = daily.get("precipitation_sum", [])
        wind = daily.get("windspeed_10m_max", [])

        lines = []

        if days <= 1:
            cur_temp = current.get("temperature", "?")
            cur_wind = current.get("windspeed", "?")
            cur_code = current.get("weathercode", 0)
            cur_desc = WMO_CODES.get(cur_code, "unbekannt")
            lines.append(f"Aktuelles Wetter in {name}: {cur_desc}, {cur_temp} Grad Celsius, Wind {cur_wind} km/h.")

            if len(dates) > 1:
                idx = 1
                desc = WMO_CODES.get(codes[idx], "unbekannt")
                lines.append(
                    f"Morgen: {desc}, maximal {max_temps[idx]} Grad, minimal {min_temps[idx]} Grad, "
                    f"Niederschlag {precip[idx]} mm, Wind bis {wind[idx]} km/h."
                )
        else:
            for i in range(1, min(days + 1, len(dates))):
                date_obj = datetime.strptime(dates[i], "%Y-%m-%d")
                day_name = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"][date_obj.weekday()]
                desc = WMO_CODES.get(codes[i], "unbekannt")
                lines.append(
                    f"{day_name} {dates[i]}: {desc}, max {max_temps[i]} Grad, min {min_temps[i]} Grad, "
                    f"Niederschlag {precip[i]} mm."
                )

        return " ".join(lines)

    except Exception as e:
        return f"Wetterdaten konnten nicht abgerufen werden: {e}"
