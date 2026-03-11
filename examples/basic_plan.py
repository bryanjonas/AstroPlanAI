"""
Basic example of using AstroPlanAI to create an imaging session plan.

This demonstrates the full multi-agent workflow:
1. Weather analysis
2. Ephemeris calculations
3. Target recommendations
4. Consolidated scheduling
"""

import asyncio
import os
from pathlib import Path
import sys

# Add parent directory to path to import astroplanai
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from astroplanai.agents.coordinator import create_coordinator_agent
from astroplanai.config import load_config
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown


async def main():
    """Run a basic astrophotography planning session."""
    console = Console()

    # Load configuration
    try:
        config = load_config()
    except ValueError as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        console.print("\n[yellow]Please create a .env file with LLM settings[/yellow]")
        console.print("[yellow]You can copy .env.template to get started[/yellow]")
        return

    console.print(Panel.fit(
        "[bold cyan]AstroPlanAI[/bold cyan]\n"
        "Multi-Agent Astrophotography Planning System\n"
        f"[dim]Using: {config.llm.model}[/dim]",
        border_style="cyan"
    ))

    # Example planning request
    location = {
        "lat": 35.6870,  # Santa Fe, NM
        "lon": -105.9378,
        "elevation": 2134,  # meters
    }

    date_range = {
        "start": "2025-11-10",
        "end": "2025-11-17",
    }

    equipment = {
        "camera": "Canon R6",
        "lens": "400mm f/5.6",
        "focal_length_mm": 400,
        "sensor_width_mm": 36,
        "sensor_height_mm": 24,
        "mount": "Equatorial with tracking",
    }

    console.print("\n[bold]Planning session for:[/bold]")
    console.print(f"  📍 Location: Santa Fe, NM ({location['lat']}, {location['lon']})")
    console.print(f"  📅 Dates: {date_range['start']} to {date_range['end']}")
    console.print(f"  🔭 Equipment: {equipment['camera']}, {equipment['lens']}\n")

    # Create coordinator and run planning
    coordinator = create_coordinator_agent({
        "llm_base_url": config.llm.base_url,
        "llm_api_key": config.llm.api_key,
        "llm_model": config.llm.model,
        "temperature": config.agent.temperature,
        "max_tokens": config.agent.max_tokens,
        "weather_api_key": config.weather_api.open_meteo_api_key,
    })

    try:
        console.print("[bold yellow]Analyzing conditions...[/bold yellow]\n")
        schedule = await coordinator.plan_session(location, date_range, equipment)

        # Display result
        console.print("\n" + "=" * 80)
        console.print(Panel(
            Markdown(schedule),
            title="[bold green]Imaging Session Plan[/bold green]",
            border_style="green",
        ))

    except Exception as e:
        console.print(f"\n[red]Error during planning: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
