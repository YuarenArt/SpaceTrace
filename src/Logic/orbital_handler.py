"""
orbital_logic_handler.py

This module contains the OrbitalLogicHandler class which implements the core logic
for orbital track computation and layer creation from TLE or OMM data.
"""

import os
from datetime import datetime, timedelta
import shapefile
import numpy as np
from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
                       QgsFields, QgsField)
from PyQt5.QtCore import QVariant, QDateTime
from pyorbital.orbital import Orbital

from .file_saver import ShpSaver, GpkgSaver, GeoJsonSaver


class OrbitalLogicHandler:
    """
    Implements the core logic for orbital track computation and layer creation.

    Provides methods to create persistent shapefiles and temporary in-memory QGIS layers
    from TLE or OMM data.
    """

    def __init__(self):
        pass

    def get_line_segments(self, points):
        """
        Generate line segments from a list of points based on the split type.

        :param points: List of (lon, lat) tuples.
        :return: List of segments, each segment is a list of (lon, lat) tuples.
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
        Generates line geometries based on a list of points and the type of split.

        :param points: List of (lon, lat) tuples.
        """
        segments = self.get_line_segments(points)
        return [QgsGeometry.fromPolylineXY([QgsPointXY(lon, lat) for lon, lat in seg]) for seg in segments]

    def generate_points(self, data, data_format, track_day, step_minutes):
        """
        Generate a list of points (time, lon, lat, alt) based on data format.
        
        :param data: TLE tuple (tle_1, tle_2, orb_incl) or OMM record list.
        :param data_format: 'TLE' or 'OMM'.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :return: List of tuples (datetime, lon, lat, alt).
        :raises ValueError: If data format is invalid or data is malformed.
        """
        points = []
        current_time = datetime(track_day.year, track_day.month, track_day.day)
        end_time = current_time + timedelta(days=1)
        
        if data_format == 'TLE':
            if not isinstance(data, tuple) or len(data) != 3:
                raise ValueError("TLE data must be a tuple of (tle_1, tle_2, orb_incl).")
            tle_1, tle_2, _ = data
            orb = Orbital("N", line1=tle_1, line2=tle_2)
            
            while current_time < end_time:
                lon, lat, alt = orb.get_lonlatalt(current_time)
                points.append((current_time, lon, lat, alt))
                current_time += timedelta(minutes=step_minutes)
                
        elif data_format == 'OMM':
            if not isinstance(data, list) or not data:
                raise ValueError("OMM data must be a non-empty list of records.")
            record = data[0]
            tle_line1 = record.get("TLE_LINE1")
            tle_line2 = record.get("TLE_LINE2")
            if not tle_line1 or not tle_line2:
                raise ValueError("OMM record missing TLE data.")
            orb = Orbital("N", line1=tle_line1, line2=tle_line2)

            while current_time < end_time:
                lon, lat, alt = orb.get_lonlatalt(current_time)
                points.append((current_time, lon, lat, alt))
                current_time += timedelta(minutes=step_minutes)
                
        else:
            raise ValueError("Data format must be 'TLE' or 'OMM'.")
        return points

    def create_in_memory_point_layer(self, points, layer_name):
        """
        Create an in-memory point layer from a list of points.
        
        :param points: List of tuples (datetime, lon, lat, alt).
        :param layer_name: Name of the layer.
        :return: QgsVectorLayer with points.
        """
        point_layer = QgsVectorLayer("Point?crs=EPSG:4326", layer_name, "memory")
        provider = point_layer.dataProvider()
        fields = QgsFields()
        fields.append(QgsField("Point_ID", QVariant.Int))
        fields.append(QgsField("Date_Time", QVariant.DateTime))
        fields.append(QgsField("Latitude", QVariant.Double))
        fields.append(QgsField("Longitude", QVariant.Double))
        fields.append(QgsField("Altitude", QVariant.Double))
        provider.addAttributes(fields)
        point_layer.updateFields()

        features = []
        for i, (current_time, lon, lat, alt) in enumerate(points):
            qdt = QDateTime(current_time.year, current_time.month, current_time.day,
                            current_time.hour, current_time.minute, current_time.second)
            feat = QgsFeature()
            feat.setFields(fields)
            feat.setAttribute("Point_ID", i)
            feat.setAttribute("Date_Time", qdt)
            feat.setAttribute("Latitude", lat)
            feat.setAttribute("Longitude", lon)
            feat.setAttribute("Altitude", alt)
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
            features.append(feat)

        if features:
            provider.addFeatures(features)
            point_layer.updateExtents()
        return point_layer

    def create_line_layer_from_points(self, points, layer_name):
        """
        Create an in-memory line layer from a list of points.
        
        :param points: List of tuples (datetime, lon, lat, alt).
        :param layer_name: Name of the layer.
        :return: QgsVectorLayer with lines.
        """
        line_layer = QgsVectorLayer("LineString?crs=EPSG:4326", layer_name, "memory")
        provider = line_layer.dataProvider()
        provider.addAttributes([QgsField("ID", QVariant.Int)])
        line_layer.updateFields()

        point_coords = [(lon, lat) for _, lon, lat, _ in points]
        geometries = self.generate_line_geometries(point_coords)

        line_features = []
        for i, geom in enumerate(geometries):
            feat = QgsFeature()
            feat.setGeometry(geom)
            feat.setAttributes([i + 1])
            line_features.append(feat)

        if line_features:
            provider.addFeatures(line_features)
            line_layer.updateExtents()
        return line_layer
    
    def _adjust_output_path(self, output_path, file_format):
        base, ext = os.path.splitext(output_path)
        if file_format == 'shp':
            return f"{base}_line.shp"
        elif file_format == 'geopackage':
            return f"{base}_line.gpkg"
        elif file_format == 'geojson':
            return f"{base}_line.geojson"

    # ---------------- Unified High-Level Methods ----------------

    def create_persistent_orbital_track(self, data, data_format, track_day, step_minutes, output_path, file_format='shp'):
        """
        Create persistent orbital track shapefiles on disk.
        
        :param data: TLE or OMM data.
        :param data_format: 'TLE' or 'OMM'.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :param output_shapefile: Output point shapefile path.
        :return: Tuple (point_shapefile, line_shapefile).
        """
        points = self.generate_points(data, data_format, track_day, step_minutes)
        geometries = self.generate_line_geometries([(lon, lat) for _, lon, lat, _ in points])
        
        if file_format == 'shp':
            saver = ShpSaver()
        elif file_format == 'geopackage':
            saver = GpkgSaver()
        elif file_format == 'geojson':
            saver = GeoJsonSaver()
        else:
            raise ValueError("Unsupported file format")
        
        saver.save_points(points, output_path)
        line_output_path = self._adjust_output_path(output_path, file_format)
        saver.save_lines(geometries, line_output_path)
    
        return output_path, line_output_path

    def create_in_memory_layers(self, data, data_format, track_day, step_minutes):
        """
        Create temporary in-memory QGIS layers.
        
        :param data: TLE or OMM data.
        :param data_format: 'TLE' or 'OMM'.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :return: Tuple (point_layer, line_layer).
        """
        points = self.generate_points(data, data_format, track_day, step_minutes)
        point_layer = self.create_in_memory_point_layer(points, f"Orbital Track {data_format}")
        line_layer = self.create_line_layer_from_points(points, f"Orbital Track {data_format} Line")
        return point_layer, line_layer