"""
weather_adapter.py
Broker module for calling Open-Meteo REST APIs.
Converts location names to lat/lon and formats weather metrics into clean dicts.
"""

from typing import Any, Dict, Optional, Tuple
import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherAdapter:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _geocode(self, location: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """Resolves location string to (latitude, longitude, formatted_name)."""
        try:
            params = {"name": location, "count": 1, "language": "en", "format": "json"}
            res = requests.get(GEOCODING_URL, params=params, timeout=self.timeout)
            res.raise_for_status()
            data = res.json()

            results = data.get("results")
            if not results:
                return None, None, None

            top = results[0]
            lat = top.get("latitude")
            lon = top.get("longitude")
            formatted_name = f"{top.get('name')}, {top.get('country')}"
            return lat, lon, formatted_name
        except Exception:
            return None, None, None

    def fetch_current_weather(self, location: str) -> Dict[str, Any]:
        """Fetches current real-time weather metrics."""
        lat, lon, resolved_name = self._geocode(location)
        if lat is None or lon is None:
            return {"status": "error", "message": f"Could not locate or geocode location: '{location}'"}

        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "current": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "apparent_temperature",
                    "precipitation",
                    "wind_speed_10m",
                ],
                "timezone": "auto",
            }
            res = requests.get(FORECAST_URL, params=params, timeout=self.timeout)
            res.raise_for_status()
            data = res.json()

            current = data.get("current", {})
            units = data.get("current_units", {})

            return {
                "status": "success",
                "location": resolved_name,
                "latitude": lat,
                "longitude": lon,
                "current": {
                    "temperature": f"{current.get('temperature_2m')} {units.get('temperature_2m', '°C')}",
                    "feels_like": f"{current.get('apparent_temperature')} {units.get('apparent_temperature', '°C')}",
                    "humidity": f"{current.get('relative_humidity_2m')}{units.get('relative_humidity_2m', '%')}",
                    "precipitation": f"{current.get('precipitation')} {units.get('precipitation', 'mm')}",
                    "wind_speed": f"{current.get('wind_speed_10m')} {units.get('wind_speed_10m', 'km/h')}",
                },
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to retrieve current weather: {str(e)}"}

    def fetch_forecast(self, location: str, days: int = 3) -> Dict[str, Any]:
        """Fetches a multi-day forecast (1 to 7 days)."""
        days = min(max(1, days), 7)
        lat, lon, resolved_name = self._geocode(location)
        if lat is None or lon is None:
            return {"status": "error", "message": f"Could not locate or geocode location: '{location}'"}

        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                ],
                "forecast_days": days,
                "timezone": "auto",
            }
            res = requests.get(FORECAST_URL, params=params, timeout=self.timeout)
            res.raise_for_status()
            data = res.json()

            daily = data.get("daily", {})
            dates = daily.get("time", [])

            forecast_list = []
            for idx, date_str in enumerate(dates):
                forecast_list.append({
                    "date": date_str,
                    "temp_max_c": daily["temperature_2m_max"][idx],
                    "temp_min_c": daily["temperature_2m_min"][idx],
                    "precipitation_mm": daily["precipitation_sum"][idx],
                    "precip_probability_pct": daily["precipitation_probability_max"][idx],
                    "max_wind_kmh": daily["wind_speed_10m_max"][idx],
                })

            return {
                "status": "success",
                "location": resolved_name,
                "forecast_days": days,
                "forecast": forecast_list,
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to retrieve forecast: {str(e)}"}
