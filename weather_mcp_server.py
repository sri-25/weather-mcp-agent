"""
weather_mcp_server.py
FastMCP Server exposing weather lookup and recommendation tools.
"""

import os
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from weather_adapter import WeatherAdapter

# Fetch port from environment variable or default to 8000
port = int(os.getenv("DATABRICKS_APP_PORT", "8000"))

# Initialize FastMCP with host and port passed directly
mcp = FastMCP("WeatherPredictionServer", host="0.0.0.0", port=port)
adapter = WeatherAdapter()


@mcp.tool()
def get_current_weather(location: str) -> Dict[str, Any]:
    """
    Fetches real-time weather conditions for a location.

    Args:
        location: City name or address (e.g., "Chicago, IL", "London", "Tokyo").

    Returns:
        Dict containing temperature, feels_like, humidity, precipitation, and wind speed.
    """
    return adapter.fetch_current_weather(location)


@mcp.tool()
def get_forecast(location: str, days: int = 3) -> Dict[str, Any]:
    """
    Retrieves a multi-day forecast (1 to 7 days) for a location.

    Args:
        location: City name or address (e.g., "Austin, TX").
        days: Number of forecast days to fetch (1 to 7, default: 3).

    Returns:
        Dict containing high/low temperatures, precipitation totals, and rain probabilities.
    """
    return adapter.fetch_forecast(location, days=days)


@mcp.tool()
def predict_umbrella_needed(location: str, target_date_offset: int = 0) -> Dict[str, Any]:
    """
    Evaluates forecast data to provide a recommendation on bringing an umbrella.

    Decision Logic:
      - BRING_UMBRELLA: Rain Probability >= 40% OR Rain Volume >= 2.0 mm
      - OPTIONAL_UMBRELLA: Rain Probability between 20% and 39%
      - NO_UMBRELLA_NEEDED: Rain Probability < 20%

    Args:
        location: City name or address.
        target_date_offset: Day index (0 = today, 1 = tomorrow, 2 = day after, etc.).

    Returns:
        Dict containing recommendation status, reasoning, and underlying weather metrics.
    """
    forecast_data = adapter.fetch_forecast(location, days=target_date_offset + 1)
    if forecast_data.get("status") != "success":
        return forecast_data

    forecasts = forecast_data.get("forecast", [])
    if target_date_offset >= len(forecasts):
        return {
            "status": "error",
            "message": f"Offset {target_date_offset} exceeds max forecast window ({len(forecasts)} days).",
        }

    target_day = forecasts[target_date_offset]
    precip_prob = target_day.get("precip_probability_pct") or 0
    precip_mm = target_day.get("precipitation_mm") or 0.0

    if precip_prob >= 40 or precip_mm >= 2.0:
        recommendation = "BRING_UMBRELLA"
        reasoning = f"High precipitation chance ({precip_prob}%) or expected rainfall ({precip_mm} mm)."
    elif precip_prob >= 20:
        recommendation = "OPTIONAL_UMBRELLA"
        reasoning = f"Moderate precipitation chance ({precip_prob}%). Consider carrying a light umbrella."
    else:
        recommendation = "NO_UMBRELLA_NEEDED"
        reasoning = f"Low precipitation risk ({precip_prob}%, {precip_mm} mm expected)."

    return {
        "status": "success",
        "location": forecast_data["location"],
        "date": target_day["date"],
        "recommendation": recommendation,
        "reasoning": reasoning,
        "metrics": {
            "precipitation_probability_pct": precip_prob,
            "expected_precipitation_mm": precip_mm,
            "temp_high_c": target_day["temp_max_c"],
            "temp_low_c": target_day["temp_min_c"],
        },
    }


if __name__ == "__main__":
    mcp.run(transport="sse")