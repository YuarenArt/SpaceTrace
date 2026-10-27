"""Convert mean anomaly to true anomaly for elliptical Earth orbits."""

import numpy as np


def mean_to_true_anomaly(mean_anomaly, eccentricity):
    """Return true anomaly in radians for mean anomaly in radians."""
    if not 0 <= eccentricity < 1:
        raise ValueError("Eccentricity must be in the range [0, 1).")

    mean_anomaly = np.mod(np.asarray(mean_anomaly, dtype=float), 2 * np.pi)
    eccentric_anomaly = mean_anomaly.copy()

    for _ in range(30):
        correction = (
            eccentric_anomaly - eccentricity * np.sin(eccentric_anomaly) - mean_anomaly
        ) / (1 - eccentricity * np.cos(eccentric_anomaly))
        eccentric_anomaly -= correction
        if np.all(np.abs(correction) < 1e-12):
            break

    return 2 * np.arctan2(
        np.sqrt(1 + eccentricity) * np.sin(eccentric_anomaly / 2),
        np.sqrt(1 - eccentricity) * np.cos(eccentric_anomaly / 2),
    )
