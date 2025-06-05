from datetime import datetime, timedelta
from typing import List, Tuple
import numpy as np
from pyorbital.orbital import Orbital
from poliastro.twobody.angles import M_to_nu

from .orbital_data_processor import OrbitalDataProcessorInterface

class PyOrbitalDataProcessor(OrbitalDataProcessorInterface):
    """
    Concrete implementation of OrbitalDataProcessorInterface using pyorbital.
    """
    def __init__(self, tle_name: str, tle1: str, tle2: str, inclination: float, log_callback=None):

        self.log_callback = log_callback or (lambda msg, lvl="INFO": print(f"[{lvl}] {msg}"))
        self._log(f"Initializing PyOrbitalDataProcessor with name={tle_name}, line1={tle1[:20]}..., line2={tle2[:20]}...", "DEBUG")
        
        try:
            self.orb = Orbital(tle_name, line1=tle1, line2=tle2)
            self.inclination = float(self.orb.tle.inclination)  # Derive from TLE
            self._log(f"Inclination derived: {self.inclination}", "DEBUG")
        except Exception as e:
            self._log(f"Failed to initialize Orbital with TLE data: {str(e)}", "ERROR")
            raise ValueError(f"Failed to initialize Orbital with TLE data: {str(e)}")
        
    def _log(self, message, level="INFO"):
        """
        Log a message using the provided callback.

        :param message: The log message.
        :param level: Log level ("INFO", "DEBUG", "WARNING", "ERROR").
        """
        if self.log_callback:
            self.log_callback(message, level)

    def get_coord(self, time_utc: datetime) -> Tuple[float, float, float]:
        """
        Obtain geodetic position (lon, lat, alt) at specified UTC time.
        """
        self._log(f"Getting coordinates for time: {time_utc}", "DEBUG")

        lon, lat, alt = self.orb.get_lonlatalt(time_utc)
        return lon, lat, alt

    def compute_orbital_parameters(
        self,
        times: List[datetime]
    ) -> List[Tuple[datetime, float, float, float, float, float, float, float, float]]:
        """
        Compute orbital parameters for given list of datetimes.

        :param times: List of datetime objects.
        :return: List of tuples containing orbital parameters.
        :raises RuntimeError: If computation fails.
        """

        self._log(f"Computing orbital parameters for {len(times)} times", "DEBUG")

        try:
            times_np = np.array([np.datetime64(t) for t in times])
            _, velocities = self.orb.get_position(times_np, normalize=False)
            lons, lats, alts = self.get_coord(times_np)

            lons_rad = np.radians(lons)
            lats_rad = np.radians(lats)
            vx, vy, vz = velocities

            east = -np.sin(lons_rad) * vx + np.cos(lons_rad) * vy
            north = (
                -np.sin(lats_rad) * np.cos(lons_rad) * vx -
                np.sin(lats_rad) * np.sin(lons_rad) * vy +
                np.cos(lats_rad) * vz
            )
            up = (
                np.cos(lats_rad) * np.cos(lons_rad) * vx +
                np.cos(lats_rad) * np.sin(lons_rad) * vy +
                np.sin(lats_rad) * vz
            )
            azimuth = (np.degrees(np.arctan2(east, north)) + 360) % 360
            horizontal_speed = np.hypot(east, north)
            trajectory_arc = np.degrees(np.arctan2(up, horizontal_speed))

            e = self.orb.tle.excentricity
            M0_deg = self.orb.tle.mean_anomaly
            n = self.orb.tle.mean_motion
            t0 = np.datetime64(self.orb.tle.epoch)
            times_sec = (times_np - t0) / np.timedelta64(1, 's')
            M0_rad = np.radians(M0_deg)
            M = M0_rad + n * times_sec
            true_anomaly = (np.degrees(M_to_nu(M, e)) + 360) % 360

            results = []
            for i, t in enumerate(times):
                results.append((
                    t,
                    round(float(lons[i]), 4),
                    round(float(lats[i]), 4),
                    round(float(alts[i]), 4),
                    round(float(np.linalg.norm(velocities[:, i])), 4),
                    round(float(azimuth[i]), 4),
                    round(float(trajectory_arc[i]), 4),
                    round(float(true_anomaly[i]), 4),
                    round(float(self.inclination), 4)
                ))

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
        Generate orbital parameters from start time over given duration and step size.
        """

        self._log(f"Propagating orbit: start={start}, duration={duration_hours}h, step={step_minutes}m", "INFO")

        end = start + timedelta(hours=duration_hours)
        step = timedelta(minutes=step_minutes)
        times = []
        current = start
        while current <= end:
            times.append(current)
            current += step
            
        self._log(f"Generated {len(times)} time steps", "DEBUG")
        return self.compute_orbital_parameters(times)