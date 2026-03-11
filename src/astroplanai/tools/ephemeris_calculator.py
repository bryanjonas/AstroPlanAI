"""Ephemeris calculations using AstroPy."""

from datetime import datetime, timedelta
from typing import Dict, Any
import numpy as np
from astropy.coordinates import EarthLocation, AltAz, SkyCoord, get_sun, get_body
from astropy.time import Time, TimeDelta
import astropy.units as u


class EphemerisCalculator:
    """Calculate celestial object positions and visibility windows."""

    def __init__(self):
        """Initialize the ephemeris calculator."""
        self._twilight_cache: Dict[tuple, Dict] = {}
        self._moon_cache: Dict[tuple, Dict] = {}

    # --------------------------------------------------------------
    def get_location(self, lat: float, lon: float, elevation: float = 0) -> EarthLocation:
        """Create an Earth location object."""
        return EarthLocation(lat=lat * u.deg, lon=lon * u.deg, height=elevation * u.m)

    # --------------------------------------------------------------
    def calculate_astronomical_twilight(
        self, location: EarthLocation, date: datetime
    ) -> Dict[str, datetime]:
        """
        Calculate sunset, astronomical twilight, and sunrise times.

        Args:
            location: Observer's location
            date: Date for calculation

        Returns:
            Dictionary with sunset, twilight_evening, twilight_morning, sunrise
        """
        cache_key = (
            round(float(location.lat.deg), 4),
            round(float(location.lon.deg), 4),
            round(float(location.height.to(u.m).value), 1),
            date.date().isoformat(),
        )
        if cache_key in self._twilight_cache:
            return self._twilight_cache[cache_key]

        # Use astropy Time object for better accuracy
        time_start = Time(date)
        # Sample every 10 minutes (144 samples) — sufficient for twilight detection (~±5 min accuracy)
        times = time_start + TimeDelta(np.arange(0, 144) * 600, format="sec")

        altaz_frame = AltAz(obstime=times, location=location)
        sun_altitudes = get_sun(times).transform_to(altaz_frame).alt.deg

        # Identify transitions through altitude thresholds
        sunset, twilight_evening, twilight_morning, sunrise = None, None, None, None

        # Iterate through the day's altitudes to find events
        for i in range(1, len(sun_altitudes)):
            if sun_altitudes[i - 1] > 0 and sun_altitudes[i] <= 0 and sunset is None:
                sunset = times[i]
            if sun_altitudes[i - 1] > -18 and sun_altitudes[i] <= -18 and twilight_evening is None:
                twilight_evening = times[i]
            if sun_altitudes[i - 1] <= -18 and sun_altitudes[i] > -18:
                if twilight_morning is None:
                    twilight_morning = times[i]
            if sun_altitudes[i - 1] <= 0 and sun_altitudes[i] > 0:
                if sunrise is None:
                    sunrise = times[i]

        result = {
            "sunset": sunset.datetime if sunset else None,
            "twilight_evening": twilight_evening.datetime if twilight_evening else None,
            "twilight_morning": twilight_morning.datetime if twilight_morning else None,
            "sunrise": sunrise.datetime if sunrise else None,
        }
        self._twilight_cache[cache_key] = result
        return result

    # --------------------------------------------------------------
    def calculate_moon_info(
        self, location: EarthLocation, date: datetime
    ) -> Dict[str, Any]:
        """Calculate moon phase and illumination."""
        cache_key = (
            round(float(location.lat.deg), 4),
            round(float(location.lon.deg), 4),
            round(float(location.height.to(u.m).value), 1),
            date.date().isoformat(),
        )
        if cache_key in self._moon_cache:
            return self._moon_cache[cache_key]

        time = Time(date)
        moon = get_body("moon", time)
        sun = get_sun(time)

        # Compute elongation between Moon and Sun
        elongation = moon.separation(sun)
        phase_angle = elongation.deg
        illumination = (1 + np.cos(np.deg2rad(phase_angle))) / 2 * 100

        # Compute moon position for given location
        moon_altaz = moon.transform_to(AltAz(obstime=time, location=location))

        result = {
            "illumination_percent": float(illumination),
            "altitude_deg": float(moon_altaz.alt.deg),
            "azimuth_deg": float(moon_altaz.az.deg),
            "phase_angle_deg": float(phase_angle),
        }
        self._moon_cache[cache_key] = result
        return result

    # --------------------------------------------------------------
    def calculate_target_visibility(
        self,
        target_ra: float,
        target_dec: float,
        location: EarthLocation,
        date: datetime,
        min_altitude: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Calculate when a target is visible above minimum altitude.
        """
        target = SkyCoord(ra=target_ra * u.deg, dec=target_dec * u.deg)
        time_start = Time(date)
        times = time_start + TimeDelta(np.arange(0, 24) * 3600, format="sec")  # hourly samples

        altaz = target.transform_to(AltAz(obstime=times, location=location))
        altitudes = altaz.alt.deg

        max_altitude = np.max(altitudes)
        max_time = times[np.argmax(altitudes)]

        # Detect rise/set crossings
        rise_time, set_time = None, None
        for i in range(1, len(altitudes)):
            if altitudes[i - 1] < min_altitude <= altitudes[i] and rise_time is None:
                rise_time = times[i]
            if altitudes[i - 1] >= min_altitude > altitudes[i] and set_time is None:
                set_time = times[i]

        return {
            "max_altitude_deg": float(max_altitude),
            "max_altitude_time": max_time.datetime,
            "rise_time": rise_time.datetime if rise_time else None,
            "set_time": set_time.datetime if set_time else None,
            "is_visible": bool(max_altitude >= min_altitude),
        }
