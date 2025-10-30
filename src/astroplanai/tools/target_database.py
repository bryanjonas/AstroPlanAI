"""Target database for deep-sky objects and celestial targets."""

from typing import List, Dict, Optional
from enum import Enum


class TargetType(Enum):
    """Types of astronomical targets."""

    GALAXY = "galaxy"
    NEBULA = "nebula"
    STAR_CLUSTER = "star_cluster"
    PLANETARY_NEBULA = "planetary_nebula"
    PLANET = "planet"
    SUPERNOVA_REMNANT = "supernova_remnant"


class Target:
    """Represents an astronomical target."""

    def __init__(
        self,
        name: str,
        common_name: Optional[str],
        ra: float,
        dec: float,
        magnitude: float,
        target_type: TargetType,
        size_arcmin: Optional[float] = None,
        best_months: Optional[List[int]] = None,
    ):
        """
        Initialize a target.

        Args:
            name: Catalog name (e.g., M31, NGC 7000)
            common_name: Common name (e.g., Andromeda Galaxy)
            ra: Right ascension in degrees
            dec: Declination in degrees
            magnitude: Visual magnitude
            target_type: Type of object
            size_arcmin: Angular size in arcminutes
            best_months: List of best months for imaging (1-12)
        """
        self.name = name
        self.common_name = common_name
        self.ra = ra
        self.dec = dec
        self.magnitude = magnitude
        self.target_type = target_type
        self.size_arcmin = size_arcmin
        self.best_months = best_months or []


class TargetDatabase:
    """Database of popular astrophotography targets."""

    def __init__(self):
        """Initialize with a curated list of popular targets."""
        self.targets = self._load_default_targets()

    def _load_default_targets(self) -> List[Target]:
        """Load a default set of popular astrophotography targets."""
        return [
            # Messier objects
            Target("M31", "Andromeda Galaxy", 10.68, 41.27, 3.4, TargetType.GALAXY, 178, [9, 10, 11, 12]),
            Target("M42", "Orion Nebula", 83.82, -5.39, 4.0, TargetType.NEBULA, 65, [11, 12, 1, 2]),
            Target("M45", "Pleiades", 56.75, 24.12, 1.6, TargetType.STAR_CLUSTER, 110, [11, 12, 1, 2]),
            Target("M51", "Whirlpool Galaxy", 202.47, 47.20, 8.4, TargetType.GALAXY, 11, [3, 4, 5, 6]),
            Target("M81", "Bode's Galaxy", 148.89, 69.07, 6.9, TargetType.GALAXY, 26, [1, 2, 3, 4, 5]),
            Target("M82", "Cigar Galaxy", 148.97, 69.68, 8.4, TargetType.GALAXY, 11, [1, 2, 3, 4, 5]),
            Target("M8", "Lagoon Nebula", 270.92, -24.38, 6.0, TargetType.NEBULA, 90, [6, 7, 8]),
            Target("M16", "Eagle Nebula", 274.70, -13.80, 6.4, TargetType.NEBULA, 7, [6, 7, 8]),
            Target("M27", "Dumbbell Nebula", 299.90, 22.72, 7.5, TargetType.PLANETARY_NEBULA, 8, [6, 7, 8, 9]),
            Target("M57", "Ring Nebula", 283.40, 33.03, 8.8, TargetType.PLANETARY_NEBULA, 1.4, [5, 6, 7, 8]),

            # NGC objects
            Target("NGC 7000", "North America Nebula", 312.23, 44.53, 4.0, TargetType.NEBULA, 120, [6, 7, 8, 9]),
            Target("NGC 281", "Pacman Nebula", 11.52, 56.60, 7.4, TargetType.NEBULA, 35, [10, 11, 12]),
            Target("NGC 6992", "Eastern Veil Nebula", 312.90, 31.72, 7.0, TargetType.SUPERNOVA_REMNANT, 60, [6, 7, 8, 9]),
            Target("NGC 891", "Silver Sliver Galaxy", 35.64, 42.35, 10.0, TargetType.GALAXY, 13, [10, 11, 12, 1]),
            Target("NGC 2237", "Rosette Nebula", 97.99, 5.03, 6.0, TargetType.NEBULA, 80, [12, 1, 2, 3]),
            Target("NGC 7293", "Helix Nebula", 337.41, -20.84, 7.6, TargetType.PLANETARY_NEBULA, 16, [8, 9, 10]),

            # IC objects
            Target("IC 1396", "Elephant Trunk Nebula", 324.13, 57.50, 3.5, TargetType.NEBULA, 170, [7, 8, 9, 10]),
            Target("IC 5070", "Pelican Nebula", 311.83, 44.37, 8.0, TargetType.NEBULA, 60, [6, 7, 8, 9]),
        ]

    def search_by_name(self, query: str) -> List[Target]:
        """
        Search for targets by name (case-insensitive).

        Args:
            query: Search string

        Returns:
            List of matching targets
        """
        query_lower = query.lower()
        return [
            t for t in self.targets
            if query_lower in t.name.lower() or (t.common_name and query_lower in t.common_name.lower())
        ]

    def filter_by_season(self, month: int) -> List[Target]:
        """
        Get targets best visible in a given month.

        Args:
            month: Month (1-12)

        Returns:
            List of targets best in that month
        """
        return [t for t in self.targets if month in t.best_months]

    def filter_by_type(self, target_type: TargetType) -> List[Target]:
        """
        Filter targets by type.

        Args:
            target_type: Type of target

        Returns:
            List of matching targets
        """
        return [t for t in self.targets if t.target_type == target_type]

    def filter_by_size(self, max_size_arcmin: float) -> List[Target]:
        """
        Filter targets that fit within a field of view.

        Args:
            max_size_arcmin: Maximum size in arcminutes

        Returns:
            List of targets that fit
        """
        return [
            t for t in self.targets
            if t.size_arcmin and t.size_arcmin <= max_size_arcmin
        ]

    def get_all_targets(self) -> List[Target]:
        """Get all targets in the database."""
        return self.targets
