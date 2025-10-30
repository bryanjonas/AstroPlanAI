"""Coordinator agent that orchestrates the multi-agent workflow."""

from openai import AsyncOpenAI
from typing import Dict, Any
import asyncio

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
            config: Configuration dictionary with VLLM settings
        """
        self.config = config

        # Initialize OpenAI client for VLLM
        self.client = AsyncOpenAI(
            base_url=config["vllm_base_url"],
            api_key=config.get("vllm_api_key", "not-needed"),
        )

        self.model = config["vllm_model"]
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
        print("🌤️  Fetching weather forecast...")
        print("🌙  Calculating ephemeris data...")
        print("🔭  Selecting optimal targets...")

        # Run data collection in parallel
        weather_data, ephemeris_data, target_data = await asyncio.gather(
            self._get_weather_analysis(location, date_range),
            self._get_ephemeris_data(location, date_range),
            self._get_target_recommendations(location, date_range, equipment),
        )

        # Step 2: Consolidate inputs for scheduler
        consolidated_input = self._consolidate_data(
            weather_data, ephemeris_data, target_data, location, date_range, equipment
        )

        # Step 3: Generate final schedule
        print("\n📅 Generating optimal imaging schedule...")
        schedule = await self._create_schedule(consolidated_input)

        return schedule

    async def _get_weather_analysis(
        self, location: Dict[str, float], date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Get weather forecast analysis from WeatherAgent."""
        # Fetch raw weather data
        forecast = await self.weather_api.get_astronomy_forecast(
            latitude=location["lat"],
            longitude=location["lon"],
            days=7,  # TODO: Calculate from date_range
        )

        # Have the agent analyze it
        prompt = f"""Analyze this astronomical weather forecast for location ({location['lat']}, {location['lon']}).

Weather data: {forecast}

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
        from datetime import datetime
        from astropy.coordinates import EarthLocation

        earth_loc = EarthLocation(
            lat=location["lat"],
            lon=location["lon"],
            height=location.get("elevation", 0),
        )

        # Calculate for each date in range (simplified for now)
        start_date = datetime.fromisoformat(date_range["start"])

        twilight = self.ephemeris_calc.calculate_astronomical_twilight(earth_loc, start_date)
        moon_info = self.ephemeris_calc.calculate_moon_info(earth_loc, start_date)

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
        from datetime import datetime

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


def create_coordinator_agent(config: Dict[str, Any]) -> AstroPlanner:
    """
    Create the main coordinator that orchestrates all sub-agents.

    Args:
        config: Configuration dictionary with VLLM and agent settings

    Returns:
        AstroPlanner instance
    """
    return AstroPlanner(config)
