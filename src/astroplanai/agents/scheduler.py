"""Scheduler agent for creating imaging plans."""

from openai import AsyncOpenAI
from .base import BaseAgent


SCHEDULER_SYSTEM_INSTRUCTION = """You are an expert astrophotography session planner.

Your role is to synthesize inputs from multiple specialized agents and create a detailed,
actionable imaging schedule.

You receive:
1. **Weather forecast analysis**: Which nights have clear skies, quality scores
2. **Ephemeris data**: Moon phase, twilight times, darkness duration
3. **Target recommendations**: Specific objects to image with visibility windows

Your output should be a structured imaging plan with:

**Per-Night Schedule:**
For each recommended night, provide:
- Date and overall quality score
- Usable imaging window (start/end times based on twilight and moonset/rise)
- Weather summary (cloud cover %, humidity, wind)
- Moon status (phase %, set time if applicable)

**Target Timeline:**
For each target on each night:
- Target name and type
- Rise/Set times (or "circumpolar" if always visible)
- Optimal imaging window (when target is highest)
- Recommended priority (primary, secondary, backup)
- Suggested exposure time (based on moon and conditions)

**Practical Recommendations:**
- Setup and calibration suggestions
- Best time to start imaging
- Backup targets if primary target sets early
- Any constraints or concerns (wind, dew, moon proximity to target)

**Format:**
Present the plan in a clear, chronological format. Use markdown tables where appropriate.
Be specific with times (e.g., "21:45" not "around 10 PM").
Prioritize the best nights and targets first.

Remember: This plan should be actionable for an astrophotographer to follow directly.
"""


def create_scheduler_agent(
    client: AsyncOpenAI,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> BaseAgent:
    """
    Create the Scheduler agent.

    Args:
        client: AsyncOpenAI client configured for LLM API
        model: Model name to use
        temperature: Sampling temperature
        max_tokens: Maximum response tokens

    Returns:
        Configured agent for creating imaging schedules
    """
    return BaseAgent(
        client=client,
        name="SchedulerAgent",
        system_instruction=SCHEDULER_SYSTEM_INSTRUCTION,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
