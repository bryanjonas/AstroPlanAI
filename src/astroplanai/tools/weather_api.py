"""Weather API integration for astronomy forecasts."""

import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class WeatherAPITool:
    """Tool for fetching astronomical weather forecasts."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather API tool.

        Args:
            api_key: Optional API key for premium services
        """
        self.api_key = api_key
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        # Persistent client for connection reuse across requests
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the persistent HTTP client."""
        await self.client.aclose()

    async def get_astronomy_forecast(
        self, latitude: float, longitude: float, days: int = 7
    ) -> Dict[str, any]:
        """
        Get astronomical weather forecast using Open-Meteo API.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            days: Number of forecast days (1-16)

        Returns:
            Dictionary containing cloud cover, humidity, and other relevant data
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": [
                "cloud_cover",
                "cloud_cover_low",
                "cloud_cover_mid",
                "cloud_cover_high",
                "relative_humidity_2m",
                "dew_point_2m",
                "temperature_2m",
                "wind_speed_10m",
            ],
            "daily": ["sunrise", "sunset"],
            "forecast_days": days,
            "timezone": "auto",
        }

        response = await self.client.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json()

    def parse_forecast_for_night(
        self, forecast_data: Dict, night_date: datetime
    ) -> Dict[str, any]:
        """
        Parse forecast data for a specific night's imaging window.

        Args:
            forecast_data: Raw forecast data from API
            night_date: The night to analyze (evening date)

        Returns:
            Summary of conditions for that night
        """
        hourly = forecast_data.get("hourly", {})
        times = hourly.get("time", [])

        # Find evening hours (e.g., 8 PM to 4 AM)
        night_indices = []
        target_date_str = night_date.strftime("%Y-%m-%d")

        for i, time_str in enumerate(times):
            dt = datetime.fromisoformat(time_str)
            if dt.date().isoformat() == target_date_str and dt.hour >= 20:
                night_indices.append(i)
            elif dt.date().isoformat() == (night_date.date() + timedelta(days=1)).isoformat() and dt.hour <= 4:
                night_indices.append(i)

        if not night_indices:
            return {"error": "No data for specified night"}

        # Calculate average/min/max for the night
        cloud_cover = [hourly["cloud_cover"][i] for i in night_indices]
        humidity = [hourly["relative_humidity_2m"][i] for i in night_indices]
        wind_speed = [hourly["wind_speed_10m"][i] for i in night_indices]

        return {
            "date": target_date_str,
            "cloud_cover_avg": sum(cloud_cover) / len(cloud_cover),
            "cloud_cover_max": max(cloud_cover),
            "humidity_avg": sum(humidity) / len(humidity),
            "wind_speed_avg": sum(wind_speed) / len(wind_speed),
            "wind_speed_max": max(wind_speed),
            "hours_analyzed": len(night_indices),
        }

    def calculate_quality_score(self, night_summary: Dict) -> float:
        """
        Calculate an overall imaging quality score (0-100).

        Args:
            night_summary: Parsed night forecast summary

        Returns:
            Quality score where 100 is perfect conditions
        """
        if "error" in night_summary:
            return 0.0

        # Scoring factors (adjust weights as needed)
        cloud_score = max(0, 100 - night_summary["cloud_cover_avg"])
        humidity_score = max(0, 100 - night_summary["humidity_avg"])
        wind_score = max(0, 100 - night_summary["wind_speed_avg"] * 2)

        # Weighted average
        total_score = (cloud_score * 0.6) + (humidity_score * 0.2) + (wind_score * 0.2)

        return round(total_score, 1)
