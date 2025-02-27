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


class OrbitalLogicHandler:
    """
    Implements the core logic for orbital track computation and layer creation.

    Provides methods to create persistent shapefiles and temporary in-memory QGIS layers
    from TLE or OMM data.
    """

    def __init__(self):
        pass

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

    def create_point_shapefile(self, points, output_shapefile):
        """
        Create a point shapefile from a list of points.
        
        :param points: List of tuples (datetime, lon, lat, alt).
        :param output_shapefile: Output shapefile path.
        """
        writer = shapefile.Writer(output_shapefile, shapefile.POINT)
        writer.field('Point_ID', 'N', 10)
        writer.field('Date_Time', 'C', 19)
        writer.field('Latitude', 'F', 10, 6)
        writer.field('Longitude', 'F', 11, 6)
        writer.field('Altitude', 'F', 20, 3)

        for i, (current_time, lon, lat, alt) in enumerate(points):
            utc_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
            writer.point(lon, lat)
            writer.record(i, utc_string, lat, lon, alt)

        prj_filename = output_shapefile.replace('.shp', '.prj')
        with open(prj_filename, "w") as prj:
            wgs84_wkt = (
                'GEOGCS["WGS 84",DATUM["WGS_1984",'
                'SPHEROID["WGS 84",6378137,298.257223563]],'
                'PRIMEM["Greenwich",0],'
                'UNIT["degree",0.0174532925199433]]'
            )
            prj.write(wgs84_wkt)

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

        segments = []
        current_segment = [QgsPointXY(points[0][1], points[0][2])]
        for i in range(1, len(points)):
            prev_lon = current_segment[-1].x()
            curr_lon = points[i][1]
            if abs(curr_lon - prev_lon) > 180:
                segments.append(current_segment)
                current_segment = [QgsPointXY(points[i][1], points[i][2])]
            else:
                current_segment.append(QgsPointXY(points[i][1], points[i][2]))
        if current_segment:
            segments.append(current_segment)

        line_features = []
        for i, segment in enumerate(segments):
            line_feat = QgsFeature()
            line_geom = QgsGeometry.fromPolylineXY(segment)
            line_feat.setGeometry(line_geom)
            line_feat.setAttributes([i + 1])
            line_features.append(line_feat)

        if line_features:
            provider.addFeatures(line_features)
            line_layer.updateExtents()
        return line_layer

    def convert_points_shp_to_line(self, input_shp, output_shp):
        """
        Convert a point shapefile to a polyline shapefile.
        
        :param input_shp: Input point shapefile path.
        :param output_shp: Output polyline shapefile path.
        :raises ValueError: If input shapefile is empty.
        """
        reader = shapefile.Reader(input_shp)
        shapes = reader.shapes()
        if not shapes:
            raise ValueError("Input shapefile contains no objects.")

        points = [shp.points[0] for shp in shapes if shp.points]
        segments = []
        current_segment = [points[0]]
        for i in range(1, len(points)):
            prev_lon = current_segment[-1][0]
            curr_lon = points[i][0]
            if abs(curr_lon - prev_lon) > 180:
                segments.append(current_segment)
                current_segment = [points[i]]
            else:
                current_segment.append(points[i])
        if current_segment:
            segments.append(current_segment)

        writer = shapefile.Writer(output_shp, shapeType=shapefile.POLYLINE)
        writer.field("ID", "N", size=10)
        writer.line(segments)
        writer.record(1)
        writer.close()

        prj_filename = os.path.splitext(output_shp)[0] + ".prj"
        with open(prj_filename, "w") as prj_file:
            wgs84_wkt = (
                'GEOGCS["WGS 84",DATUM["WGS_1984",'
                'SPHEROID["WGS 84",6378137,298.257223563]],'
                'PRIMEM["Greenwich",0],'
                'UNIT["degree",0.0174532925199433]]'
            )
            prj_file.write(wgs84_wkt)

    # ---------------- Unified High-Level Methods ----------------

    def create_persistent_orbital_track(self, data, data_format, sat_id, track_day, step_minutes, output_shapefile):
        """
        Create persistent orbital track shapefiles on disk.
        
        :param data: TLE or OMM data.
        :param data_format: 'TLE' or 'OMM'.
        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :param output_shapefile: Output point shapefile path.
        :return: Tuple (point_shapefile, line_shapefile).
        """
        points = self.generate_points(data, data_format, track_day, step_minutes)
        self.create_point_shapefile(points, output_shapefile)
        line_output_path = output_shapefile.replace('.shp', '_line.shp')
        self.convert_points_shp_to_line(output_shapefile, line_output_path)
        return output_shapefile, line_output_path

    def create_in_memory_layers(self, data, data_format, sat_id, track_day, step_minutes):
        """
        Create temporary in-memory QGIS layers.
        
        :param data: TLE or OMM data.
        :param data_format: 'TLE' or 'OMM'.
        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :return: Tuple (point_layer, line_layer).
        """
        points = self.generate_points(data, data_format, track_day, step_minutes)
        point_layer = self.create_in_memory_point_layer(points, f"Orbital Track {data_format}")
        line_layer = self.create_line_layer_from_points(points, f"Orbital Track {data_format} Line")
        return point_layer, line_layer