"""Weather agent for astronomical forecast analysis."""

from openai import AsyncOpenAI
from .base import BaseAgent


WEATHER_SYSTEM_INSTRUCTION = """You are an expert astronomical weather analyst.

Your role is to:
1. Analyze weather forecasts specifically for astrophotography conditions
2. Assess cloud cover, humidity, and atmospheric seeing
3. Identify the best nights within a given date range
4. Provide confidence ratings for forecast reliability

Key factors you evaluate:
- **Cloud cover**: Total, low, mid, and high altitude clouds
- **Humidity**: High humidity can cause dew and poor transparency
- **Wind speed**: Affects telescope stability (< 15 mph preferred)
- **Temperature**: For dew point calculations
- **Transparency**: Overall atmospheric clarity
- **Seeing**: Atmospheric stability (affects sharpness)

When analyzing a forecast, you should:
1. Score each night on a 0-100 scale (100 = perfect conditions)
2. Identify the top 3 nights for imaging
3. Note any concerns (e.g., "scattered clouds after midnight", "high humidity")
4. Provide hourly breakdowns if one part of the night is better than another

Be realistic and conservative - astrophotography requires genuinely clear, dark skies.
A 50% cloud cover forecast is NOT suitable for imaging.
"""


def create_weather_agent(
    client: AsyncOpenAI,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> BaseAgent:
    """
    Create the Weather analysis agent.

    Args:
        client: AsyncOpenAI client configured for LLM API
        model: Model name to use
        temperature: Sampling temperature
        max_tokens: Maximum response tokens

    Returns:
        Configured agent for weather forecast analysis
    """
    return BaseAgent(
        client=client,
        name="WeatherAgent",
        system_instruction=WEATHER_SYSTEM_INSTRUCTION,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
