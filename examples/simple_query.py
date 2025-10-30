"""
Simplified example that demonstrates individual agent capabilities.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from astroplanai.tools.ephemeris_calculator import EphemerisCalculator
from astroplanai.tools.target_database import TargetDatabase
from astroplanai.config import load_config
from datetime import datetime
from astropy.coordinates import EarthLocation
from rich.console import Console
from rich.table import Table


async def demonstrate_tools():
    """Demonstrate the core calculation tools."""
    console = Console()

    console.print("\n[bold cyan]AstroPlanAI Tools Demo[/bold cyan]\n")

    # Ephemeris calculations
    console.print("[bold]1. Ephemeris Calculator[/bold]")
    calc = EphemerisCalculator()
    location = EarthLocation(lat=35.6870, lon=-105.9378, height=2134)
    date = datetime(2025, 11, 15, 20, 0, 0)

    twilight = calc.calculate_astronomical_twilight(location, date)
    moon = calc.calculate_moon_info(location, date)

    console.print(f"  Sunset: {twilight.get('sunset')}")
    console.print(f"  Evening twilight: {twilight.get('twilight_evening')}")
    console.print(f"  Morning twilight: {twilight.get('twilight_morning')}")
    console.print(f"  Moon illumination: {moon['illumination_percent']:.1f}%")

    # Target visibility
    console.print("\n[bold]2. Target Visibility (M31 - Andromeda Galaxy)[/bold]")
    m31_ra = 10.68  # degrees
    m31_dec = 41.27

    visibility = calc.calculate_target_visibility(
        m31_ra, m31_dec, location, date, min_altitude=30
    )

    console.print(f"  Max altitude: {visibility['max_altitude_deg']:.1f}°")
    console.print(f"  Max altitude time: {visibility['max_altitude_time']}")
    console.print(f"  Visible: {'Yes' if visibility['is_visible'] else 'No'}")

    # Target database
    console.print("\n[bold]3. Target Database (November targets)[/bold]")
    db = TargetDatabase()
    november_targets = db.filter_by_season(11)

    table = Table(title="Popular Targets for November")
    table.add_column("Name", style="cyan")
    table.add_column("Common Name", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Magnitude", justify="right")
    table.add_column("Size", justify="right")

    for target in november_targets[:5]:
        table.add_row(
            target.name,
            target.common_name or "-",
            target.target_type.value,
            f"{target.magnitude:.1f}",
            f"{target.size_arcmin:.0f}'" if target.size_arcmin else "-",
        )

    console.print(table)


if __name__ == "__main__":
    asyncio.run(demonstrate_tools())
