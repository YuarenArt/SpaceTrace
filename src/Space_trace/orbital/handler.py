"""
orbital_logic_handler.py

This module contains the OrbitalLogicHandler class which implements the core logic
for orbital track computation and layer creation from TLE or OMM data.
"""

import os
import math
from datetime import datetime, timedelta
import shapefile
import numpy as np
from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
                       QgsFields, QgsField)
from PyQt5.QtCore import QVariant, QDateTime
from pyorbital.orbital import Orbital

from .saver import ShpSaver, GpkgSaver, GeoJsonSaver, MemoryLayerSaver


class OrbitalLogicHandler:
    """
    Implements the core logic for orbital track computation and layer creation.

    Provides methods to create persistent shapefiles and temporary in-memory QGIS layers
    from TLE or OMM data.
    """

    def __init__(self):
        self.memory_saver = MemoryLayerSaver()

    def get_line_segments(self, points):
        """
        Generate line segments from a list of points based on the split type.

        :param points: List of (lon, lat) tuples.
        :return: List of segments, where each segment is a list of (lon, lat) tuples.
        """
        if not points:
            raise ValueError("Points list is empty.")

        segments = []
        current_segment = [points[0]]
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            delta_lon = p2[0] - p1[0]
            if abs(delta_lon) <= 180:
                current_segment.append(p2)
            else:
                if delta_lon < -180:
                    t = (180 - p1[0]) / (p2[0] + 360 - p1[0])
                    lat_interp = p1[1] + t * (p2[1] - p1[1])
                    current_segment.append((180, lat_interp))
                    segments.append(current_segment)
                    current_segment = [(-180, lat_interp), p2]
                elif delta_lon > 180:
                    t = (-180 - p1[0]) / (p2[0] - 360 - p1[0])
                    lat_interp = p1[1] + t * (p2[1] - p1[1])
                    current_segment.append((-180, lat_interp))
                    segments.append(current_segment)
                    current_segment = [(180, lat_interp), p2]
        if current_segment:
            segments.append(current_segment)
        return segments

    def generate_line_geometries(self, points):
        """
        Generate line geometries based on a list of points and split them as needed.

        :param points: List of (lon, lat) tuples.
        :return: List of QgsGeometry line geometries.
        """
        segments = self.get_line_segments(points)
        return [QgsGeometry.fromPolylineXY([QgsPointXY(lon, lat) for lon, lat in seg])
                for seg in segments]

    def compute_orbital_parameters(self, orb, times, inc):
        """
        Compute orbital parameters for given times.

        :param orb: Orbital object initialized with TLE data.
        :param times: Array of numpy.datetime64 times.
        :param inc: Orbital inclination (degrees).
        :return: List of tuples (datetime, lon, lat, alt, velocity, azimuth, elevation, true_anomaly, inc).
        """
        positions, velocities = orb.get_position(times, normalize=False)
        lons, lats, alts = orb.get_lonlatalt(times)
        velocity_norms = np.linalg.norm(velocities, axis=0)

        lats_rad = np.radians(lats)
        lons_rad = np.radians(lons)
        vx, vy, vz = velocities

        east = -np.sin(lons_rad) * vx + np.cos(lons_rad) * vy
        north = (-np.sin(lats_rad) * np.cos(lons_rad) * vx -
                np.sin(lats_rad) * np.sin(lons_rad) * vy +
                np.cos(lats_rad) * vz)
        up = (np.cos(lats_rad) * np.cos(lons_rad) * vx +
            np.cos(lats_rad) * np.sin(lons_rad) * vy +
            np.sin(lats_rad) * vz)

        azimuth = (np.degrees(np.arctan2(east, north)) + 360) % 360
        horizontal_speed = np.sqrt(east ** 2 + north ** 2)
        elevation = np.degrees(np.arctan2(up, horizontal_speed))

        e = orb.tle.excentricity  
        M0 = orb.tle.mean_anomaly
        n = orb.tle.mean_motion
        t0 = orb.tle.epoch
        M = M0 + n * ((times - t0) / np.timedelta64(1, 's'))
        E = solve_kepler_newton(M, e)

        true_anomaly = 2 * np.arctan2(np.sqrt(1 + e) * np.sin(E / 2),
                                  np.sqrt(1 - e) * np.cos(E / 2))
        true_anomaly = (np.degrees(true_anomaly) + 360) % 360

        points = [(times[i].astype('datetime64[ms]').astype(datetime), lons[i], lats[i], alts[i],
                velocity_norms[i], azimuth[i], elevation[i], true_anomaly[i], inc)
                for i in range(len(times))]

        return points

    def generate_points(self, data, data_format, start_datetime, duration_hours, step_minutes):
        """
        Generate a list of points with orbital parameters based on the data format.

        :param data: TLE tuple (tle_1, tle_2, orb_incl) or a list of OMM records.
        :param data_format: 'TLE' or 'OMM'.
        :param start_datetime: Start date and time for track computation.
        :param duration_hours: Duration of the track in hours.
        :param step_minutes: Time step in minutes.
        :return: List of tuples (datetime, lon, lat, alt, velocity, azimuth, elevation, true_anomaly).
        :raises ValueError: If data format is invalid or data is malformed.
        """
        end_time = start_datetime + timedelta(hours=duration_hours)
        step = timedelta(minutes=step_minutes)
        num_steps = int((end_time - start_datetime) / step)
        start_time_np = np.datetime64(start_datetime)
        step_np = np.timedelta64(int(step_minutes * 60 * 1e6), 'us')
        times = start_time_np + np.arange(num_steps) * step_np

        if data_format == 'TLE':
            if not isinstance(data, tuple) or len(data) != 3:
                raise ValueError("TLE data must be a tuple of (tle_1, tle_2, orb_incl).")
            tle_1, tle_2, inc = data
        elif data_format == 'OMM':
            if not isinstance(data, list) or not data:
                raise ValueError("OMM data must be a non-empty list of records.")
            record = data[0]
            tle_1 = record.get("TLE_LINE1")
            tle_2 = record.get("TLE_LINE2")
            inc = record.get("INCLINATION")
            if not tle_1 or not tle_2:
                raise ValueError("OMM record missing TLE data.")
        else:
            raise ValueError("Data format must be 'TLE' or 'OMM'.")
        
        orb = Orbital("N", line1=tle_1, line2=tle_2)
        points = self.compute_orbital_parameters(orb, times, inc)
        return points
    

    def _adjust_output_path(self, output_path, file_format):
        """
        Adjust the output file path based on the file format.

        :param output_path: Original output path.
        :param file_format: 'shp', 'gpkg', or 'geojson'.
        :return: Adjusted output file path.
        """
        base, ext = os.path.splitext(output_path)
        if file_format == 'shp':
            return f"{base}_line.shp"
        elif file_format == 'gpkg':
            return f"{base}_line.gpkg"
        elif file_format == 'geojson':
            return f"{base}_line.geojson"

    # ---------------- Unified High-Level Methods ----------------

    def create_persistent_orbital_track(self, data, data_format, start_datetime, duration_hours, step_minutes, output_path, file_format, create_line_layer):
        """
        Create persistent orbital track shapefiles on disk.

        :param data: TLE or OMM data.
        :param data_format: 'TLE' or 'OMM'.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :param output_path: Output path for the points file.
        :param file_format: 'shp', 'gpkg', or 'geojson'.
        :return: Tuple (points_file, line_file).
        """
        points = self.generate_points(data, data_format, start_datetime, duration_hours, step_minutes)

        if file_format == 'shp':
            saver = ShpSaver()
        elif file_format == 'gpkg':
            saver = GpkgSaver()
        elif file_format == 'geojson':
            saver = GeoJsonSaver()
        else:
            raise ValueError("Unsupported file format")

        saver.save_points(points, output_path)
        
        line_file = None
        if create_line_layer:
            geometries = self.generate_line_geometries([(pt[1], pt[2]) for pt in points])
            line_output_path = self._adjust_output_path(output_path, file_format)
            saver.save_lines(geometries, line_output_path)
            line_file = line_output_path

        return output_path, line_file

    def create_in_memory_layers(self, data, data_format, start_datetime, duration_hours, step_minutes, create_line_layer):
        """
        Create temporary in-memory QGIS layers.

        :param data: TLE or OMM data.
        :param data_format: 'TLE' or 'OMM'.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :return: Tuple (point_layer, line_layer).
        """
        points = self.generate_points(data, data_format, start_datetime, duration_hours, step_minutes)
        point_layer = self.memory_saver.save_points(points, f"Orbital Track {data_format}")
        line_layer = None
        if create_line_layer:
            geometries = self.generate_line_geometries([(pt[1], pt[2]) for pt in points])
            line_layer = self.memory_saver.save_lines(geometries, f"Orbital Track {data_format} Line")
        return point_layer, line_layer

def solve_kepler_newton(M, e, tol=1e-6, max_iter=100):
    M = np.asarray(M)
    E = M.copy() 

    for _ in range(max_iter):
        delta_E = (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
        E -= delta_E
        if np.all(np.abs(delta_E) < tol):
            break

    return E