"""Shared calculations for orbital velocity components."""

import numpy as np


def velocity_angles(longitudes, latitudes, velocities):
    """Return azimuth and trajectory angle in degrees for velocity vectors."""
    lons_rad = np.radians(longitudes)
    lats_rad = np.radians(latitudes)
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
    return azimuth, trajectory_arc
