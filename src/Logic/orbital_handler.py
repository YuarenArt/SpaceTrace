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

from .file_saver import ShpSaver, GpkgSaver, GeoJsonSaver, MemoryLayerSaver


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

    def _compute_orbital_parameters(self, orb, current_time):
        """
        Compute orbital parameters for a given time.

        Calculates longitude, latitude, altitude, velocity, azimuth, elevation,
        and true anomaly for the provided orbital object at the specified time.

        :param orb: Instance of Orbital.
        :param current_time: Datetime object for computation.
        :return: Tuple (lon, lat, alt, velocity, azimuth, elevation, true_anomaly).
        :raises NotImplementedError: If the orbital object does not support get_position_velocity.
        """
        # Get geodetic coordinates: longitude, latitude, altitude.
        lon, lat, alt = orb.get_lonlatalt(current_time)

        # Get position and velocity vectors.
        try:
            position, velocity_vector = orb.get_position(current_time, normalize=False)
        except AttributeError:
            raise NotImplementedError("Orbital object does not support get_position_velocity. "
                                      "Numerical differentiation is not implemented.")

        # Compute velocity as the norm of the velocity vector.
        velocity = math.sqrt(sum(v ** 2 for v in velocity_vector))

        # Convert velocity from ECEF to local ENU coordinates for azimuth and elevation calculations.
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        vx, vy, vz = velocity_vector

        east = -math.sin(lon_rad) * vx + math.cos(lon_rad) * vy
        north = (-math.sin(lat_rad) * math.cos(lon_rad) * vx -
                 math.sin(lat_rad) * math.sin(lon_rad) * vy +
                 math.cos(lat_rad) * vz)
        up = (math.cos(lat_rad) * math.cos(lon_rad) * vx +
              math.cos(lat_rad) * math.sin(lon_rad) * vy +
              math.sin(lat_rad) * vz)

        azimuth = (math.degrees(math.atan2(east, north)) + 360) % 360
        horizontal_speed = math.sqrt(east ** 2 + north ** 2)
        elevation = math.degrees(math.atan2(up, horizontal_speed))

        # Compute true anomaly.
        try:
            true_anomaly = orb.get_true_anomaly(current_time)
        except AttributeError:
            # Compute using the eccentricity vector if get_true_anomaly is not available.
            mu = getattr(orb, 'mu', 398600.4418)  # Earth's gravitational parameter in km^3/s^2.
            r_norm = math.sqrt(sum(r ** 2 for r in position))
            r_dot_v = sum(r * v for r, v in zip(position, velocity_vector))
            h_vec = np.cross(position, velocity_vector)
            h_norm = np.linalg.norm(h_vec)
            v_squared = velocity ** 2
            e_vec = [((v_squared - mu / r_norm) * r_i - r_dot_v * v_i) / mu
                     for r_i, v_i in zip(position, velocity_vector)]
            e = math.sqrt(sum(comp ** 2 for comp in e_vec))
            dot_e_r = sum(ei * ri for ei, ri in zip(e_vec, position))
            if e > 1e-8 and r_norm > 1e-8:
                cos_nu = max(min(dot_e_r / (e * r_norm), 1.0), -1.0)
                true_anomaly = math.degrees(math.acos(cos_nu))
                if r_dot_v < 0:
                    true_anomaly = 360 - true_anomaly
            else:
                true_anomaly = 0.0

        return lon, lat, alt, velocity, azimuth, elevation, true_anomaly

    def generate_points(self, data, data_format, track_day, step_minutes):
        """
        Generate a list of points with orbital parameters based on the data format.

        :param data: TLE tuple (tle_1, tle_2, orb_incl) or a list of OMM records.
        :param data_format: 'TLE' or 'OMM'.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :return: List of tuples (datetime, lon, lat, alt, velocity, azimuth, elevation, true_anomaly).
        :raises ValueError: If data format is invalid or data is malformed.
        """
        points = []
        current_time = datetime(track_day.year, track_day.month, track_day.day)
        end_time = current_time + timedelta(days=1)

        if data_format == 'TLE':
            if not isinstance(data, tuple) or len(data) != 3:
                raise ValueError("TLE data must be a tuple of (tle_1, tle_2, orb_incl).")
            tle_1, tle_2, inc = data
            orb = Orbital("N", line1=tle_1, line2=tle_2)

            while current_time < end_time:
                lon, lat, alt, velocity, azimuth, elevation, true_anomaly = \
                    self._compute_orbital_parameters(orb, current_time)
                points.append((current_time, lon, lat, alt, velocity, azimuth, elevation, true_anomaly, inc))
                current_time += timedelta(minutes=step_minutes)

        elif data_format == 'OMM':
            if not isinstance(data, list) or not data:
                raise ValueError("OMM data must be a non-empty list of records.")
            record = data[0]
            tle_line1 = record.get("TLE_LINE1")
            tle_line2 = record.get("TLE_LINE2")
            inc = record.get("INCLINATION")
            if not tle_line1 or not tle_line2:
                raise ValueError("OMM record missing TLE data.")
            orb = Orbital("N", line1=tle_line1, line2=tle_line2)

            while current_time < end_time:
                lon, lat, alt, velocity, azimuth, elevation, true_anomaly = \
                    self._compute_orbital_parameters(orb, current_time)
                points.append((current_time, lon, lat, alt, velocity, azimuth, elevation, true_anomaly, inc))
                current_time += timedelta(minutes=step_minutes)

        else:
            raise ValueError("Data format must be 'TLE' or 'OMM'.")
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

    def create_persistent_orbital_track(self, data, data_format, track_day, step_minutes, output_path, file_format, create_line_layer):
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
        points = self.generate_points(data, data_format, track_day, step_minutes)

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

    def create_in_memory_layers(self, data, data_format, track_day, step_minutes, create_line_layer):
        """
        Create temporary in-memory QGIS layers.

        :param data: TLE or OMM data.
        :param data_format: 'TLE' or 'OMM'.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :return: Tuple (point_layer, line_layer).
        """
        points = self.generate_points(data, data_format, track_day, step_minutes)
        point_layer = self.memory_saver.save_points(points, f"Orbital Track {data_format}")
        line_layer = None
        if create_line_layer:
            geometries = self.generate_line_geometries([(pt[1], pt[2]) for pt in points])
            line_layer = self.memory_saver.save_lines(geometries, f"Orbital Track {data_format} Line")
        return point_layer, line_layer
