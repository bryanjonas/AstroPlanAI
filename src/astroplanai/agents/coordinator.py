"""Coordinator agent that orchestrates the multi-agent workflow."""

from openai import AsyncOpenAI
from typing import Dict, Any, Callable, Optional
import asyncio
from datetime import datetime, timedelta

from .weather import create_weather_agent
from .ephemeris import create_ephemeris_agent
from .target_selection import create_target_selection_agent
from .scheduler import create_scheduler_agent
from .base import BaseAgent

from ..tools.ephemeris_calculator import EphemerisCalculator
from ..tools.weather_api import WeatherAPITool
from ..tools.target_database import TargetDatabase


class AstroPlanner:
    """Main coordinator for the multi-agent astrophotography planning system."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AstroPlanner with configuration.

        Args:
            config: Configuration dictionary with LLM settings
        """
        self.config = config

        # Support both new llm_* keys and legacy vllm_* keys
        self.client = AsyncOpenAI(
            base_url=config.get("llm_base_url") or config.get("vllm_base_url"),
            api_key=config.get("llm_api_key") or config.get("vllm_api_key", "not-needed"),
        )

        self.model = config.get("llm_model") or config.get("vllm_model")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4096)

        # Initialize tools
        self.ephemeris_calc = EphemerisCalculator()
        self.weather_api = WeatherAPITool(
            api_key=config.get("weather_api_key")
        )
        self.target_db = TargetDatabase()

        # Initialize agents (lazy loading)
        self._weather_agent = None
        self._ephemeris_agent = None
        self._target_agent = None
        self._scheduler_agent = None

    @property
    def weather_agent(self) -> BaseAgent:
        """Lazy load weather agent."""
        if self._weather_agent is None:
            self._weather_agent = create_weather_agent(
                self.client, self.model, self.temperature, self.max_tokens
            )
        return self._weather_agent

    @property
    def ephemeris_agent(self) -> BaseAgent:
        """Lazy load ephemeris agent."""
        if self._ephemeris_agent is None:
            self._ephemeris_agent = create_ephemeris_agent(
                self.client, self.model, self.temperature, self.max_tokens
            )
        return self._ephemeris_agent

    @property
    def target_agent(self) -> BaseAgent:
        """Lazy load target selection agent."""
        if self._target_agent is None:
            self._target_agent = create_target_selection_agent(
                self.client, self.model, self.temperature, self.max_tokens
            )
        return self._target_agent

    @property
    def scheduler_agent(self) -> BaseAgent:
        """Lazy load scheduler agent."""
        if self._scheduler_agent is None:
            self._scheduler_agent = create_scheduler_agent(
                self.client, self.model, self.temperature, self.max_tokens
            )
        return self._scheduler_agent

    async def plan_session(
        self,
        location: Dict[str, float],
        date_range: Dict[str, str],
        equipment: Dict[str, Any],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Create a comprehensive astrophotography session plan.

        Args:
            location: Dict with 'lat', 'lon', 'elevation' (optional)
            date_range: Dict with 'start' and 'end' dates (YYYY-MM-DD format)
            equipment: Dict with equipment specs (focal_length, sensor_size, etc.)

        Returns:
            Complete imaging session plan as formatted text
        """
        # Step 1: Gather data from parallel agents
        self._log_progress("🌤️  Fetching weather forecast...", progress_callback)
        self._log_progress("🌙  Calculating ephemeris data...", progress_callback)
        self._log_progress("🔭  Selecting optimal targets...", progress_callback)

        # Run data collection in parallel; return_exceptions=True allows partial failures
        results = await asyncio.gather(
            self._get_weather_analysis(location, date_range),
            self._get_ephemeris_data(location, date_range),
            self._get_target_recommendations(location, date_range, equipment),
            return_exceptions=True,
        )

        weather_data, ephemeris_data, target_data = results

        # Handle partial failures gracefully
        if isinstance(weather_data, Exception):
            weather_data = {"raw_forecast": {}, "analysis": f"Weather data unavailable: {weather_data}"}
        if isinstance(ephemeris_data, Exception):
            ephemeris_data = {"twilight": {}, "moon": {}, "analysis": f"Ephemeris data unavailable: {ephemeris_data}"}
        if isinstance(target_data, Exception):
            target_data = {"available_targets": [], "recommendations": f"Target data unavailable: {target_data}"}

        # Step 2: Consolidate inputs for scheduler
        self._log_progress("📦  Consolidating agent outputs...", progress_callback)
        consolidated_input = self._consolidate_data(
            weather_data, ephemeris_data, target_data, location, date_range, equipment
        )

        # Step 3: Generate final schedule
        self._log_progress("📅  Generating optimal imaging schedule...", progress_callback)
        schedule = await self._create_schedule(consolidated_input)
        self._log_progress("✅  Planning complete!", progress_callback)

        return schedule

    def _summarize_weather_for_llm(self, forecast: dict) -> list:
        """Summarize hourly weather data into compact per-night summaries for the LLM."""
        hourly = forecast.get("hourly", {})
        times = hourly.get("time", [])
        cloud = hourly.get("cloud_cover", [])
        humidity = hourly.get("relative_humidity_2m", [])
        wind = hourly.get("wind_speed_10m", [])

        nights: Dict[str, Dict] = {}
        for i, time_str in enumerate(times):
            d = datetime.fromisoformat(time_str)
            hour = d.hour
            if hour >= 20:
                date_key = d.date().isoformat()
            elif hour <= 4:
                date_key = (d.date() - timedelta(days=1)).isoformat()
            else:
                continue  # Skip daytime hours

            if date_key not in nights:
                nights[date_key] = {"cloud": [], "humidity": [], "wind": []}
            if i < len(cloud):
                nights[date_key]["cloud"].append(cloud[i])
            if i < len(humidity):
                nights[date_key]["humidity"].append(humidity[i])
            if i < len(wind):
                nights[date_key]["wind"].append(wind[i])

        summaries = []
        for date_key in sorted(nights.keys()):
            n = nights[date_key]
            if not n["cloud"]:
                continue
            cloud_avg = sum(n["cloud"]) / len(n["cloud"])
            cloud_max = max(n["cloud"])
            humidity_avg = sum(n["humidity"]) / len(n["humidity"]) if n["humidity"] else 0
            wind_avg = sum(n["wind"]) / len(n["wind"]) if n["wind"] else 0

            if cloud_avg < 20:
                seeing = "excellent"
            elif cloud_avg < 40:
                seeing = "good"
            elif cloud_avg < 60:
                seeing = "fair"
            else:
                seeing = "poor"

            summaries.append({
                "date": date_key,
                "cloud_pct_avg": round(cloud_avg),
                "cloud_pct_max": round(cloud_max),
                "humidity_avg": round(humidity_avg),
                "wind_avg_kmh": round(wind_avg),
                "seeing_score": seeing,
            })

        return summaries

    async def _get_weather_analysis(
        self, location: Dict[str, float], date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Get weather forecast analysis from WeatherAgent."""
        # Calculate the number of days from the date range
        days = max(
            1,
            (datetime.fromisoformat(date_range["end"]) - datetime.fromisoformat(date_range["start"])).days + 1,
        )
        forecast = await self.weather_api.get_astronomy_forecast(
            latitude=location["lat"],
            longitude=location["lon"],
            days=min(days, 16),
        )

        # Summarize forecast to reduce token count for the LLM
        night_summaries = self._summarize_weather_for_llm(forecast)

        prompt = f"""Analyze this astronomical weather forecast for location ({location['lat']}, {location['lon']}).

Night summaries: {night_summaries}

Provide:
1. Quality score (0-100) for each night
2. Top 3 nights ranked by imaging suitability
3. Specific concerns for each night (clouds, wind, humidity)
4. Overall forecast reliability assessment
"""

        analysis = await self.weather_agent.generate(prompt)
        return {"raw_forecast": forecast, "analysis": analysis}

    async def _get_ephemeris_data(
        self, location: Dict[str, float], date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Get ephemeris calculations from EphemerisAgent."""
        from astropy.coordinates import EarthLocation

        earth_loc = EarthLocation(
            lat=location["lat"],
            lon=location["lon"],
            height=location.get("elevation", 0),
        )

        start_date = datetime.fromisoformat(date_range["start"])

        # Run both sync calculations in parallel threads to avoid blocking the event loop
        twilight, moon_info = await asyncio.gather(
            asyncio.to_thread(self.ephemeris_calc.calculate_astronomical_twilight, earth_loc, start_date),
            asyncio.to_thread(self.ephemeris_calc.calculate_moon_info, earth_loc, start_date),
        )

        prompt = f"""Analyze these ephemeris calculations for astrophotography planning:

Twilight times: {twilight}
Moon information: {moon_info}

Provide:
1. Duration of astronomical darkness
2. Moon interference assessment (% illumination and whether it's problematic)
3. Best imaging window (after evening twilight, considering moon)
4. Any constraints or recommendations
"""

        analysis = await self.ephemeris_agent.generate(prompt)
        return {
            "twilight": twilight,
            "moon": moon_info,
            "analysis": analysis,
        }

    async def _get_target_recommendations(
        self, location: Dict[str, float], date_range: Dict[str, str], equipment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get target recommendations from TargetSelectionAgent."""
        # Get seasonal targets
        month = datetime.fromisoformat(date_range["start"]).month
        seasonal_targets = self.target_db.filter_by_season(month)

        # Format target info
        target_list = "\n".join([
            f"- {t.name} ({t.common_name}): {t.target_type.value}, "
            f"Mag {t.magnitude}, Size {t.size_arcmin}'"
            for t in seasonal_targets[:15]  # Limit to top 15
        ])

        prompt = f"""Recommend astrophotography targets for these conditions:

Location: Lat {location['lat']}, Lon {location['lon']}
Month: {month}
Equipment: {equipment}

Available targets this season:
{target_list}

Provide 3-5 target recommendations with:
1. Target name and type
2. Why it's suitable for this equipment and season
3. Approximate imaging window (altitude-based)
4. Priority ranking (primary/secondary/backup)
"""

        recommendations = await self.target_agent.generate(prompt)
        return {
            "available_targets": [
                {"name": t.name, "common_name": t.common_name, "ra": t.ra, "dec": t.dec}
                for t in seasonal_targets
            ],
            "recommendations": recommendations,
        }

    def _consolidate_data(
        self,
        weather_data: Dict,
        ephemeris_data: Dict,
        target_data: Dict,
        location: Dict,
        date_range: Dict,
        equipment: Dict,
    ) -> str:
        """Consolidate all agent outputs into a single prompt for the scheduler."""
        return f"""Create a detailed astrophotography imaging schedule with this information:

LOCATION: {location}
DATE RANGE: {date_range}
EQUIPMENT: {equipment}

WEATHER ANALYSIS:
{weather_data['analysis']}

EPHEMERIS DATA:
{ephemeris_data['analysis']}

TARGET RECOMMENDATIONS:
{target_data['recommendations']}

Generate a complete, actionable imaging plan with specific times and priorities.
"""

    async def _create_schedule(self, consolidated_input: str) -> str:
        """Generate final schedule using SchedulerAgent."""
        schedule = await self.scheduler_agent.generate(consolidated_input)
        return schedule

    def _log_progress(
        self,
        message: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Log progress to console and optional callback."""
        print(message)
        if progress_callback:
            progress_callback(message)


def create_coordinator_agent(config: Dict[str, Any]) -> AstroPlanner:
    """
    Create the main coordinator that orchestrates all sub-agents.

    Args:
        config: Configuration dictionary with LLM and agent settings

    Returns:
        AstroPlanner instance
    """
    return AstroPlanner(config)
