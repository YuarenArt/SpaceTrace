from skyfield.api import load, EarthSatellite
from datetime import datetime, timedelta
from typing import List, Tuple
import numpy as np
from poliastro.twobody.angles import M_to_nu
from pandas import date_range

from .orbital_data_processor import OrbitalDataProcessorInterface

class SkyfieldOrbitalDataProcessor(OrbitalDataProcessorInterface):
    """
    Implementation of OrbitalDataProcessorInterface using Skyfield.
    Supports deep space orbits (periods > 225 minutes).
    Optimized for performance using vectorized computations.
    """

    def __init__(self, tle_name: str, tle1: str, tle2: str, log_callback=None):
        """
        Initialize with TLE data and a logger.

        :param tle_name: Name of the satellite.
        :param tle1: First TLE line.
        :param tle2: Second TLE line.
        :param log_callback: Optional logging function (defaults to print).
        :raises ValueError: If TLE data is invalid or satellite initialization fails.
        """
        self.log_callback = log_callback or (lambda msg, lvl="INFO": print(f"[{lvl}] {msg}"))
        self._log(f"Initializing SkyfieldOrbitalDataProcessor with name={tle_name}, line1={tle1[:20]}..., line2={tle2[:20]}...", "DEBUG")

        try:
            self.ts = load.timescale()  # Create timescale for time conversions
            self.satellite = EarthSatellite(tle1, tle2, tle_name, self.ts)  # Initialize satellite
            self.inclination = float(self.satellite.model.inclo) * (180.0 / np.pi)  # Derive inclination in degrees
            self._log(f"Inclination derived: {self.inclination}", "DEBUG")
        except Exception as e:
            self._log(f"Failed to initialize satellite: {str(e)}", "ERROR")
            raise ValueError(f"Failed to initialize satellite with TLE data: {str(e)}")

    def _log(self, message: str, level: str = "INFO"):
        """
        Log a message using the provided callback.

        :param message: The message to log.
        :param level: Log level ("INFO", "DEBUG", "WARNING", "ERROR").
        """
        if self.log_callback:
            self.log_callback(message, level)

    def get_coord(self, time_utc: datetime) -> Tuple[float, float, float]:
        """
        Obtain geodetic position (longitude, latitude, altitude) at specified UTC time.

        :param time_utc: Time in UTC format.
        :return: Tuple of (longitude, latitude, altitude) in degrees and kilometers.
        """
        self._log(f"Getting coordinates for time: {time_utc}", "DEBUG")
        t = self.ts.utc(time_utc.year, time_utc.month, time_utc.day,
                        time_utc.hour, time_utc.minute, time_utc.second)
        geocentric = self.satellite.at(t)  # Position in geocentric system
        subpoint = geocentric.subpoint()  # Convert to geodetic coordinates
        lon = subpoint.longitude.degrees
        lat = subpoint.latitude.degrees
        alt = subpoint.elevation.km
        return lon, lat, alt

    def compute_orbital_parameters(
        self,
        times: List[datetime]
    ) -> List[Tuple[datetime, float, float, float, float, float, float, float, float]]:
        """
        Compute orbital parameters for a list of datetimes.

        :param times: List of datetime objects.
        :return: List of tuples containing (time, lon, lat, alt, speed, azimuth, trajectory_arc, true_anomaly, inclination).
        :raises RuntimeError: If computation fails.
        """
        self._log(f"Computing orbital parameters for {len(times)} times", "DEBUG")

        try:
            # Vectorized time conversion
            t = self.ts.utc([t.year for t in times], [t.month for t in times],
                            [t.day for t in times], [t.hour for t in times],
                            [t.minute for t in times], [t.second for t in times])
            
            # Vectorized position and velocity computation
            geocentrics = self.satellite.at(t)
            subpoints = geocentrics.subpoint()
            lons = subpoints.longitude.degrees
            lats = subpoints.latitude.degrees
            alts = subpoints.elevation.km
            velocities = geocentrics.velocity.km_per_s

            lons_rad = np.radians(lons)
            lats_rad = np.radians(lats)
            vx, vy, vz = velocities

            # Compute azimuth
            east = -np.sin(lons_rad) * vx + np.cos(lons_rad) * vy
            north = (
                -np.sin(lats_rad) * np.cos(lons_rad) * vx -
                np.sin(lats_rad) * np.sin(lons_rad) * vy +
                np.cos(lats_rad) * vz
            )
            azimuth = (np.degrees(np.arctan2(east, north)) + 360) % 360

            # Compute trajectory arc
            up = (
                np.cos(lats_rad) * np.cos(lons_rad) * vx +
                np.cos(lats_rad) * np.sin(lons_rad) * vy +
                np.sin(lats_rad) * vz
            )
            horizontal_speed = np.hypot(east, north)
            trajectory_arc = np.degrees(np.arctan2(up, horizontal_speed))

            # Compute true anomaly
            e = self.satellite.model.ecco  # Eccentricity
            M0_deg = self.satellite.model.mo  # Mean anomaly at epoch
            n = self.satellite.model.no_kozai  # Mean motion in radians per minute
            t0 = np.datetime64(self.satellite.epoch.utc_datetime())
            times_np = np.array([np.datetime64(t) for t in times])
            times_sec = (times_np - t0) / np.timedelta64(1, 's')
            M0_rad = np.radians(M0_deg)
            n_rad_per_sec = n * (np.pi / (180 * 60))  # Convert to rad/sec
            M = M0_rad + n_rad_per_sec * times_sec
            true_anomaly = (np.degrees(M_to_nu(M, e)) + 360) % 360

            # Compile results
            results = [
                (
                    times[i],
                    round(float(lons[i]), 4),
                    round(float(lats[i]), 4),
                    round(float(alts[i]), 4),
                    round(float(np.linalg.norm(velocities[:, i])), 4),
                    round(float(azimuth[i]), 4),
                    round(float(trajectory_arc[i]), 4),
                    round(float(true_anomaly[i]), 4),
                    round(float(self.inclination), 4)
                )
                for i in range(len(times))
            ]

            self._log(f"Computed {len(results)} orbital parameter sets", "INFO")
            return results
        except Exception as e:
            self._log(f"Failed to compute orbital parameters: {str(e)}", "ERROR")
            raise RuntimeError(f"Failed to compute orbital parameters: {str(e)}")

    def propagate(
        self,
        start: datetime,
        duration_hours: float,
        step_minutes: float
    ) -> List[Tuple[datetime, float, float, float, float, float, float, float, float]]:
        """
        Generate orbital parameters from start time over a given duration with specified step size.

        :param start: Start time in UTC.
        :param duration_hours: Duration in hours.
        :param step_minutes: Step size in minutes.
        :return: List of tuples with orbital parameters.
        """
        self._log(f"Propagating orbit: start={start}, duration={duration_hours}h, step={step_minutes}m", "INFO")

        # Generate time steps using pandas
        end = start + timedelta(hours=duration_hours)
        times = date_range(start=start, end=end, freq=f"{step_minutes}min").to_pydatetime().tolist()

        self._log(f"Generated {len(times)} time steps", "DEBUG")
        return self.compute_orbital_parameters(times)