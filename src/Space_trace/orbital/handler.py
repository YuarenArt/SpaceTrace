"""
orbital_logic_handler.py

This module contains the OrbitalLogicHandler class which implements the core logic
for orbital track computation and layer creation from TLE or OMM data.
"""

import os
from poliastro.twobody.angles import M_to_nu

from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
                       QgsFields, QgsField)
from PyQt5.QtCore import QVariant, QDateTime

from .saver import FactoryProvider
from ...orbital_data_processor.pyorbtital_processor import PyOrbitalDataProcessor


class OrbitalLogicHandler:
    """
    Implements the core logic for orbital track computation and layer creation.

    Provides methods to create persistent shapefiles and temporary in-memory QGIS layers
    from TLE or OMM data.
    """

    def __init__(self, log_callback=None):
        self.log_callback=log_callback

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

    def create_track_from_points(self, points, output_path, file_format, create_line):
        """
        Save point and optional line shapefiles from propagated points.
        """

        if not points:
            raise ValueError("No points provided to create track.")

        factory = FactoryProvider.get_factory(file_format)
        saver = factory.get_saver()
        saver.save_points(points, output_path)
        line_file = None
        if create_line:
            geometries = self.generate_line_geometries([(pt[1], pt[2]) for pt in points])
            line_output_path = self._adjust_output_path(output_path, file_format)
            saver.save_lines(geometries, line_output_path)
            line_file = line_output_path
        return output_path, line_file

    def create_memory_layers_from_points(self, points, data_format, create_line):
        """
        Create in-memory QGIS layers from propagated points.
        """

        if not points:
            raise ValueError("No points provided to create track.")

        factory = FactoryProvider.get_factory("memory")
        saver = factory.get_saver()
        point_layer = saver.save_points(points)
        line_layer = None
        if create_line:
            geometries = self.generate_line_geometries([(pt[1], pt[2]) for pt in points])
            line_layer = saver.save_lines(geometries, f"Orbital Track {data_format} Line")
        return point_layer, line_layer

    def create_persistent_orbital_track(self, data, data_format, start_datetime, duration_hours, step_minutes, output_path, file_format, create_line):
        """
        Create persistent orbital track files from data.

        :param data: TLE or OMM data.
        :param data_format: Data format ('TLE' or 'OMM').
        :param start_datetime: Start datetime for propagation.
        :param duration_hours: Duration in hours.
        :param step_minutes: Time step in minutes.
        :param output_path: Path for saving output files.
        :param file_format: Output file format ('shp', 'gpkg', 'geojson').
        :param create_line: Boolean to indicate if line layer should be created.
        :return: Tuple (points_file, line_file).
        """
        processor = self._get_processor(data, data_format)
        points = processor.propagate(start_datetime, duration_hours, step_minutes)
        return self.create_track_from_points(points, output_path, file_format, create_line)

    def create_in_memory_layers(self, data, data_format, start_datetime, duration_hours, step_minutes, create_line):
        """
        Create in-memory QGIS layers from data.

        :param data: TLE or OMM data.
        :param data_format: Data format ('TLE' or 'OMM').
        :param start_datetime: Start datetime for propagation.
        :param duration_hours: Duration in hours.
        :param step_minutes: Time step in minutes.
        :param create_line: Boolean to indicate if line layer should be created.
        :return: Tuple (point_layer, line_layer).
        """
        
        processor = self._get_processor(data, data_format)
        points = processor.propagate(start_datetime, duration_hours, step_minutes)
        return self.create_memory_layers_from_points(points, data_format, create_line)
    
    def _get_processor(self, data, data_format):
        """
        Create an OrbitalDataProcessor based on data format.

        :param data: TLE or OMM data.
        :param data_format: Data format ('TLE' or 'OMM').
        :return: OrbitalDataProcessorInterface instance.
        :raises ValueError: If data format is unsupported.
        """
        if data_format == "TLE":

            if not isinstance(data, (list, tuple)) or len(data) < 3:
                error_msg = f"Incorrect TLE data: expected at least 3 elements (got {type(data)} of length {len(data)})"
                if self.log_callback:
                    self.log_callback(f"[_get_processor] {error_msg}", "ERROR")
                raise ValueError(error_msg)
            
            
            tle1, tle2, inc = data[0], data[1], data[2]

            if self.log_callback:
                self.log_callback(f"[_get_processor] TLE_LINE1 is {'not empty' if tle1 else 'EMPTY'}", "WARNING" if not tle1 else "DEBUG")
                self.log_callback(f"[_get_processor] TLE_LINE2 is {'not empty' if tle2 else 'EMPTY'}", "WARNING" if not tle2 else "DEBUG")


            return PyOrbitalDataProcessor("N", tle1, tle2, inc, self.log_callback)
        
        elif data_format == "OMM":
            # Assuming OMM data contains necessary fields; adapt as needed
            record = data[0]
            tle_name = "N"
            tle_1 = record.get("TLE_LINE1")
            tle_2 = record.get("TLE_LINE2")
            inc = record.get("INCLINATION")
            return PyOrbitalDataProcessor("N", tle_1, tle_2, inc, self.log_callback)
        else:
            raise ValueError(f"Unsupported data format: {data_format}")