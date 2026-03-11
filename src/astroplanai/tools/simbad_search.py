"""SIMBAD astronomical database search tool."""

import httpx
from typing import Dict, List, Optional, Any
import json


class SimbadSearch:
    """Search SIMBAD astronomical database for celestial objects."""

    def __init__(self):
        """Initialize SIMBAD search client."""
        self.base_url = "https://simbad.u-strasbg.fr/simbad/sim-script"
        self.tap_url = "https://simbad.u-strasbg.fr/simbad/sim-tap/sync"
        # Persistent client for connection reuse across requests
        self.client = httpx.AsyncClient(timeout=15.0)

    async def close(self):
        """Close the persistent HTTP client."""
        await self.client.aclose()

    async def search_object(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search for an astronomical object by name.

        Args:
            query: Object name (e.g., "M31", "NGC 7000", "Andromeda")

        Returns:
            Dictionary with object information or None if not found
        """
        script = f"""
output console=off script=off
format object fmt1 "%IDLIST(1) | %COO(A D;ICRS) | %COO(E) | %OTYPE | %FLUXLIST(V)[%flux(V)] | %DIM(A) %DIM(B) %DIM(angle)"
query {query}
        """.strip()

        try:
            response = await self.client.post(
                self.base_url,
                data={"script": script},
            )

            if response.status_code != 200:
                return None

            # Parse SIMBAD output
            lines = response.text.strip().split('\n')

            # Filter out error messages and empty lines
            data_lines = [
                line for line in lines
                if line and not line.startswith('::')
            ]

            if not data_lines:
                return None

            # Parse the formatted output
            # Format: NAME | RA DEC | ERROR | TYPE | MAG | SIZE_A SIZE_B ANGLE
            parts = data_lines[0].split('|')

            if len(parts) < 4:
                return None

            name = parts[0].strip()
            coords = parts[1].strip().split()
            obj_type = parts[3].strip() if len(parts) > 3 else "Unknown"

            # Parse magnitude if available
            magnitude = None
            if len(parts) > 4 and parts[4].strip():
                try:
                    magnitude = float(parts[4].strip())
                except (ValueError, IndexError):
                    pass

            # Parse size if available
            size_arcmin = None
            if len(parts) > 5:
                size_parts = parts[5].strip().split()
                if len(size_parts) > 0:
                    try:
                        # Convert arcseconds to arcminutes
                        size_arcmin = float(size_parts[0]) / 60.0
                    except (ValueError, IndexError):
                        pass

            # Parse RA/Dec
            ra = None
            dec = None
            if len(coords) >= 2:
                try:
                    # RA in format: HH MM SS.S
                    ra_parts = coords[0:3]
                    ra_h = float(ra_parts[0]) if len(ra_parts) > 0 else 0
                    ra_m = float(ra_parts[1]) if len(ra_parts) > 1 else 0
                    ra_s = float(ra_parts[2]) if len(ra_parts) > 2 else 0
                    ra = (ra_h + ra_m/60 + ra_s/3600) * 15  # Convert to degrees

                    # Dec in format: +/-DD MM SS.S
                    dec_parts = coords[3:6]
                    dec_d = float(dec_parts[0]) if len(dec_parts) > 0 else 0
                    dec_m = float(dec_parts[1]) if len(dec_parts) > 1 else 0
                    dec_s = float(dec_parts[2]) if len(dec_parts) > 2 else 0
                    dec_sign = -1 if dec_d < 0 else 1
                    dec = dec_d + dec_sign * (dec_m/60 + dec_s/3600)
                except (ValueError, IndexError):
                    pass

            return {
                "name": name,
                "ra": ra,
                "dec": dec,
                "object_type": obj_type,
                "magnitude": magnitude,
                "size_arcmin": size_arcmin,
                "source": "SIMBAD",
            }

        except Exception as e:
            print(f"SIMBAD search error: {e}")
            return None

    async def search_region(
        self,
        ra: float,
        dec: float,
        radius_arcmin: float = 60.0,
        max_results: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search for objects in a region of sky.

        Args:
            ra: Right ascension in degrees
            dec: Declination in degrees
            radius_arcmin: Search radius in arcminutes
            max_results: Maximum number of results

        Returns:
            List of objects found in the region
        """
        # Convert RA/Dec to SIMBAD format
        ra_h = int(ra / 15)
        ra_m = int((ra / 15 - ra_h) * 60)
        ra_s = ((ra / 15 - ra_h) * 60 - ra_m) * 60

        dec_sign = '+' if dec >= 0 else '-'
        dec_d = int(abs(dec))
        dec_m = int((abs(dec) - dec_d) * 60)
        dec_s = ((abs(dec) - dec_d) * 60 - dec_m) * 60

        coords = f"{ra_h:02d} {ra_m:02d} {ra_s:05.2f} {dec_sign}{dec_d:02d} {dec_m:02d} {dec_s:05.2f}"

        script = f"""
output console=off script=off
format object fmt1 "%IDLIST(1) | %COO(A D;ICRS) | %OTYPE | %FLUXLIST(V)[%flux(V)]"
query region {coords} radius={radius_arcmin}m frame=ICRS
        """.strip()

        try:
            response = await self.client.post(
                self.base_url,
                data={"script": script},
            )

            if response.status_code != 200:
                return []

            lines = response.text.strip().split('\n')
            data_lines = [
                line for line in lines
                if line and not line.startswith('::')
            ]

            results = []
            for line in data_lines[:max_results]:
                parts = line.split('|')
                if len(parts) >= 3:
                    results.append({
                        "name": parts[0].strip(),
                        "coordinates": parts[1].strip(),
                        "object_type": parts[2].strip(),
                        "magnitude": parts[3].strip() if len(parts) > 3 else None,
                        "source": "SIMBAD",
                    })

            return results

        except Exception as e:
            print(f"SIMBAD region search error: {e}")
            return []

    def format_object_info(self, obj_data: Dict[str, Any]) -> str:
        """
        Format object information for display.

        Args:
            obj_data: Object data dictionary

        Returns:
            Formatted string
        """
        if not obj_data:
            return "Object not found"

        lines = [
            f"Name: {obj_data['name']}",
            f"Type: {obj_data['object_type']}",
        ]

        if obj_data.get('ra') and obj_data.get('dec'):
            lines.append(f"Coordinates: RA {obj_data['ra']:.4f}°, Dec {obj_data['dec']:.4f}°")

        if obj_data.get('magnitude'):
            lines.append(f"Magnitude: {obj_data['magnitude']:.1f}")

        if obj_data.get('size_arcmin'):
            lines.append(f"Size: {obj_data['size_arcmin']:.1f} arcmin")

        lines.append(f"Source: {obj_data.get('source', 'Unknown')}")

        return '\n'.join(lines)
