"""
orbital_logic_handler.py

This module contains the OrbitalLogicHandler class which implements the core logic
for orbital track computation and layer creation from TLE or OMM data.
"""

import os
from qgis.core import (QgsGeometry, QgsPointXY, QgsCoordinateReferenceSystem)
from .saver import FactoryProvider
from ...orbital_data_processor.skyfield import SkyfieldOrbitalDataProcessor


class OrbitalLogicHandler:
    """
    Implements the core logic for orbital track computation and layer creation.

    Provides methods to create persistent shapefiles and temporary in-memory QGIS layers
    from TLE or OMM data.
    """

    def __init__(self, log_callback=None):
        self.log_callback=log_callback

    def _log(self, message: str, level: str = "INFO"):
        """
        Log a message using the provided callback if available.

        :param message: Message to log.
        :param level: Log level ("INFO", "DEBUG", "WARNING", "ERROR").
        """
        if self.log_callback:
            self.log_callback(message, level)

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
            lon1, lat1 = p1
            lon2, lat2 = p2

            delta_lon = lon2 - lon1
            delta_lat = lat2 - lat1

            cross_antimeridian = abs(delta_lon) > 180
            cross_pole = abs(lat1) > 80 and abs(lat2) > 80 and (lat1 * lat2 < 0)

            if cross_antimeridian:
                if delta_lon < -180:
                    t = (180 - lon1) / (lon2 + 360 - lon1)
                    lat_interp = lat1 + t * delta_lat
                    current_segment.append((180, lat_interp))
                    segments.append(current_segment)
                    current_segment = [(-180, lat_interp), p2]
                elif delta_lon > 180:
                    t = (-180 - lon1) / (lon2 - 360 - lon1)
                    lat_interp = lat1 + t * delta_lat
                    current_segment.append((-180, lat_interp))
                    segments.append(current_segment)
                    current_segment = [(180, lat_interp), p2]
            elif cross_pole:
                # Interpolate crossing at the pole (lat = ±90), longitude undefined, but we use ±180
                t = (90 - abs(lat1)) / (abs(lat2 - lat1))
                pole_lat = 90.0 if lat2 > lat1 else -90.0
                pole_lon = 180.0  # Or any constant, as longitude at pole is degenerate
                interpolated_point = (pole_lon, pole_lat)
                current_segment.append(interpolated_point)
                segments.append(current_segment)
                current_segment = [interpolated_point, p2]
            else:
                current_segment.append(p2)

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
    

    def _adjust_output_path(self, output_path, file_format, norad_id=None):
        base, ext = os.path.splitext(output_path)
        suffix = f"_line_{norad_id}" if norad_id else "_line"
        if file_format == 'shp':
            return f"{base}{suffix}.shp"
        elif file_format == 'gpkg':
            return f"{base}{suffix}.gpkg"
        elif file_format == 'geojson':
            return f"{base}{suffix}.geojson"

    def create_track_from_points(self, points, output_path, file_format, create_line, norad_id=None):
        """
        Save point and optional line shapefiles from propagated points.
        """
        if not points:
            raise ValueError("No points provided to create track.")
        
        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                except OSError as e:
                    self._log(f"Failed to create output directory: {str(e)}", "ERROR")
                    raise RuntimeError(f"Failed to create output directory: {str(e)}")


        input_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        factory = FactoryProvider.get_factory(file_format)
        saver = factory.get_saver(log_callback=self.log_callback, input_crs=input_crs)
        
        try:
            saver.save_points(points, output_path, norad_id=norad_id)
            line_file = None
            if create_line:
                geometries = self.generate_line_geometries([(pt[1], pt[2]) for pt in points])
                line_output_path = self._adjust_output_path(output_path, file_format, norad_id)
                saver.save_lines(geometries, line_output_path, norad_id)
                line_file = line_output_path
            return output_path, line_file
        except Exception as e:
            self._log(f"Error creating track: {str(e)}", "ERROR")
            raise RuntimeError(f"Failed to create track: {str(e)}")

    def create_memory_layers_from_points(self, points, data_format, create_line,  norad_id=None):
        """
        Create in-memory QGIS layers from propagated points.
        """
        if not points:
            raise ValueError("No points provided to create track.")

        input_crs = QgsCoordinateReferenceSystem("EPSG:4326")

        factory = FactoryProvider.get_factory("memory")
        saver = factory.get_saver(log_callback=self.log_callback, input_crs=input_crs)
        point_layer = saver.save_points(points, norad_id=norad_id)
        line_layer = None
        if create_line:
            geometries = self.generate_line_geometries([(pt[1], pt[2]) for pt in points])
            line_layer = saver.save_lines(geometries, norad_id=norad_id)
        return point_layer, line_layer

    def create_persistent_orbital_track(self, data, data_format, start_datetime, duration_hours, step_minutes, output_path, file_format, create_line, norad_id):
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
        return self.create_track_from_points(points, output_path, file_format, create_line, norad_id)

    def create_in_memory_layers(self, data, data_format, start_datetime, duration_hours, step_minutes, create_line, norad_id):
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
        return self.create_memory_layers_from_points(points, data_format, create_line, norad_id)
    
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
                self._log(f"[_get_processor] {error_msg}", "ERROR")
                raise ValueError(error_msg)
            
            tle1, tle2, inc = data[0], data[1], data[2]

            self._log(f"[_get_processor] TLE_LINE1 is {'not empty' if tle1 else 'EMPTY'}", 
                      "WARNING" if not tle1 else "DEBUG")
            self._log(f"[_get_processor] TLE_LINE2 is {'not empty' if tle2 else 'EMPTY'}", 
                      "WARNING" if not tle2 else "DEBUG")

            return SkyfieldOrbitalDataProcessor("N", tle1, tle2, self.log_callback)
        
        elif data_format == "OMM":
            record = data[0]
            tle_1 = record.get("TLE_LINE1")
            tle_2 = record.get("TLE_LINE2")
            inc = record.get("INCLINATION")
            return SkyfieldOrbitalDataProcessor("N", tle_1, tle_2, self.log_callback)
        else:
            raise ValueError(f"Unsupported data format: {data_format}")