"""Target search agent for finding astronomical objects."""

from openai import AsyncOpenAI
from .base import BaseAgent


SYSTEM_INSTRUCTION = """You are an expert astronomical target search assistant.

Your role is to help astrophotographers find suitable deep-sky objects (DSOs) for imaging.

When given a search query, you should:

1. **Understand the intent**: Parse natural language queries like:
   - "Find galaxies in Ursa Major"
   - "Bright nebulae visible in summer"
   - "Small planetary nebulae for my 250mm scope"
   - "M33" or "NGC 7000"

2. **Consider constraints**:
   - Equipment (focal length, field of view, sensor size)
   - Season/months (best visibility)
   - Sky coverage (available compass sectors)
   - Minimum altitude (avoid low-altitude targets)
   - Magnitude limits (brightness suitable for equipment)

3. **Provide recommendations** with:
   - Object name and catalog designation
   - Type (galaxy, nebula, cluster, etc.)
   - Coordinates (RA/Dec)
   - Magnitude and size
   - Best viewing months
   - Imaging difficulty (easy/moderate/challenging)
   - Why it's suitable for the user's equipment

4. **Be practical**: Focus on objects that are:
   - Actually imageable with amateur equipment
   - Visible from the user's hemisphere
   - Appropriate size for their field of view
   - Bright enough for their setup

Format your responses clearly with object details and imaging tips.
"""


def create_target_search_agent(
    client: AsyncOpenAI,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> BaseAgent:
    """
    Create the target search agent.

    Args:
        client: AsyncOpenAI client configured for LLM API
        model: Model name to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response

    Returns:
        BaseAgent configured as target search agent
    """
    return BaseAgent(
        client=client,
        name="TargetSearchAgent",
        system_instruction=SYSTEM_INSTRUCTION,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
