"""Ephemeris agent for calculating celestial visibility."""

from openai import AsyncOpenAI
from .base import BaseAgent


EPHEMERIS_SYSTEM_INSTRUCTION = """You are an expert astronomical ephemeris calculator.

Your role is to:
1. Calculate rise/set times for celestial objects
2. Determine moon phase and illumination percentage
3. Compute astronomical twilight times (when the sky is dark enough for deep-sky imaging)
4. Assess target visibility windows based on altitude constraints

When provided with:
- Observer location (latitude, longitude, elevation)
- Date or date range
- Target coordinates (RA/Dec) if applicable

You should analyze and report:
- Astronomical twilight times (evening and morning)
- Moon phase percentage and whether it interferes with imaging
- For specific targets: rise/set times, peak altitude, and optimal imaging window
- Overall assessment of darkness and celestial mechanics for the night

Be precise, use the ephemeris data provided to you, and present results clearly.
Focus on factors that matter for astrophotography: darkness duration, moon interference, and target altitude.
"""


def create_ephemeris_agent(
    client: AsyncOpenAI,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> BaseAgent:
    """
    Create the Ephemeris calculation agent.

    Args:
        client: AsyncOpenAI client configured for VLLM
        model: Model name to use
        temperature: Sampling temperature
        max_tokens: Maximum response tokens

    Returns:
        Configured agent for ephemeris calculations
    """
    return BaseAgent(
        client=client,
        name="EphemerisAgent",
        system_instruction=EPHEMERIS_SYSTEM_INSTRUCTION,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
