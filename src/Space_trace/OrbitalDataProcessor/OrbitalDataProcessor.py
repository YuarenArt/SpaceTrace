from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Tuple

class OrbitalDataProcessorInterface(ABC):
    """
    Interface for orbital data processing engines.
    Provides methods for position retrieval and orbit propagation.
    """

    @abstractmethod
    def get_coord(self, time_utc: datetime) -> Tuple[float, float, float]:
        """
        Return longitude, latitude, and altitude at given UTC time.
        """
        pass

    @abstractmethod
    def compute_orbital_parameters(
        self,
        times: List[datetime]
    ) -> List[Tuple[datetime, float, float, float, float, float, float, float, float]]:
        """
        Compute detailed orbital parameters for each datetime in times list.
        Returns list of tuples: (time, lon, lat, alt, velocity, azimuth, arc, true_anomaly, inclination).
        """
        pass

    @abstractmethod
    def propagate(
        self,
        start: datetime,
        duration_hours: float,
        step_minutes: float
    ) -> List[Tuple[datetime, float, float, float, float, float, float, float, float]]:
        """
        Generate propagated orbital parameters from start over duration with given step.
        """
        pass
