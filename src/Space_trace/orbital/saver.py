from abc import ABC, abstractmethod

from qgis.core import (
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsFields,
    QgsField
)

from PyQt5.QtCore import QVariant, QDateTime

class FileSaver(ABC):
    @abstractmethod
    def save_points(self, points, output_path):
        pass

    @abstractmethod
    def save_lines(self, geometries, output_path):
        pass

class ShpSaver(FileSaver):
    def save_points(self, points, output_path):
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "points", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("Point_ID", QVariant.Int),
            QgsField("Date_Time", QVariant.DateTime), 
            QgsField("Latitude", QVariant.Double),
            QgsField("Longitude", QVariant.Double),
            QgsField("Altitude", QVariant.Double),
            QgsField("Velocity", QVariant.Double),
            QgsField("Azimuth", QVariant.Double),
            QgsField("Elevation", QVariant.Double),
            QgsField("TrueAnomaly", QVariant.Double),
            QgsField("Inclination", QVariant.Double),
        ])
        layer.updateFields()

        features = []
        for i, point in enumerate(points):
            current_time, lon, lat, alt, velocity, azimuth, elevation, true_anomaly, inc = point
            qdt = QDateTime(
                current_time.year, current_time.month, current_time.day,
                current_time.hour, current_time.minute, current_time.second
            )
            feat = QgsFeature()
            feat.setAttributes([
                i, qdt, lat, lon, alt, velocity, azimuth, elevation, true_anomaly, inc
            ])
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
            features.append(feat)

        provider.addFeatures(features)
        QgsVectorFileWriter.writeAsVectorFormat(layer, output_path, "UTF-8", layer.crs(), "ESRI Shapefile")

    def save_lines(self, geometries, output_path):
        layer = QgsVectorLayer("LineString?crs=EPSG:4326", "lines", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([QgsField("ID", QVariant.Int)])
        layer.updateFields()

        features = []
        for i, geom in enumerate(geometries):
            feat = QgsFeature()
            feat.setAttributes([i + 1])
            feat.setGeometry(geom)
            features.append(feat)

        provider.addFeatures(features)
        QgsVectorFileWriter.writeAsVectorFormat(layer, output_path, "UTF-8", layer.crs(), "ESRI Shapefile")
class GpkgSaver(FileSaver):

    def save_points(self, points, output_path):
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "temp_points", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("Point_ID", QVariant.Int),
            QgsField("Date_Time", QVariant.DateTime), 
            QgsField("Latitude", QVariant.Double),
            QgsField("Longitude", QVariant.Double),
            QgsField("Altitude", QVariant.Double),
            QgsField("Velocity", QVariant.Double),
            QgsField("Azimuth", QVariant.Double),
            QgsField("Elevation", QVariant.Double),
            QgsField("TrueAnomaly", QVariant.Double),
            QgsField("Inclination", QVariant.Double),
        ])
        layer.updateFields()
        features = []
        for i, point in enumerate(points):
            current_time, lon, lat, alt, velocity, azimuth, elevation, true_anomaly, inc = point
            qdt = QDateTime(
                current_time.year, current_time.month, current_time.day,
                current_time.hour, current_time.minute, current_time.second
            )
            feat = QgsFeature()
            feat.setAttributes([
                i, qdt, lat, lon, alt, velocity, azimuth, elevation, true_anomaly, inc
            ])
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
            features.append(feat)
        provider.addFeatures(features)
        QgsVectorFileWriter.writeAsVectorFormat(layer, output_path, "UTF-8", layer.crs(), "GPKG")

    def save_lines(self, geometries, output_path):
        layer = QgsVectorLayer("LineString?crs=EPSG:4326", "temp_lines", "memory")
        provider = layer.dataProvider()
        layer.updateFields()
        features = []
        for i, geom in enumerate(geometries):
            feat = QgsFeature()
            feat.setAttributes([i + 1])
            feat.setGeometry(geom)
            features.append(feat)
        provider.addFeatures(features)
        QgsVectorFileWriter.writeAsVectorFormat(layer, output_path, "UTF-8", layer.crs(), "GPKG")

class GeoJsonSaver(FileSaver):

    def save_points(self, points, output_path):
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "temp_points", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("Point_ID", QVariant.Int),
            QgsField("Date_Time", QVariant.DateTime),  
            QgsField("Latitude", QVariant.Double),
            QgsField("Longitude", QVariant.Double),
            QgsField("Altitude", QVariant.Double),
            QgsField("Velocity", QVariant.Double),
            QgsField("Azimuth", QVariant.Double),
            QgsField("Elevation", QVariant.Double),
            QgsField("TrueAnomaly", QVariant.Double),
            QgsField("Inclination", QVariant.Double),
        ])
        layer.updateFields()
        features = []
        for i, point in enumerate(points):
            current_time, lon, lat, alt, velocity, azimuth, elevation, true_anomaly, inc = point
            qdt = QDateTime(
                current_time.year, current_time.month, current_time.day,
                current_time.hour, current_time.minute, current_time.second
            )
            feat = QgsFeature()
            feat.setAttributes([
                i, qdt, lat, lon, alt, velocity, azimuth, elevation, true_anomaly, inc
            ])
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
            features.append(feat)
        provider.addFeatures(features)
        QgsVectorFileWriter.writeAsVectorFormat(layer, output_path, "UTF-8", layer.crs(), "GeoJSON")    

    def save_lines(self, geometries, output_path):
        layer = QgsVectorLayer("LineString?crs=EPSG:4326", "temp_lines", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([QgsField("ID", QVariant.Int)])
        layer.updateFields()
        features = []
        for i, geom in enumerate(geometries):
            feat = QgsFeature()
            feat.setAttributes([i + 1])
            feat.setGeometry(geom)
            features.append(feat)
        provider.addFeatures(features)
        options = QgsVectorFileWriter.SaveVectorOptions()
        QgsVectorFileWriter.writeAsVectorFormat(layer, output_path, "UTF-8", layer.crs(), "GeoJSON")
        
class MemoryLayerSaver:
    """Class to create in-memory QGIS layers for points and lines."""

    def save_points(self, points, layer_name):
        """
        Create an in-memory point layer from a list of points.

        :param points: List of tuples (datetime, lon, lat, alt, velocity, azimuth, elevation, true_anomaly, inc).
        :param layer_name: Name of the layer.
        :return: QgsVectorLayer containing the points.
        """
        point_layer = QgsVectorLayer("Point?crs=EPSG:4326", layer_name, "memory")
        provider = point_layer.dataProvider()
        fields = QgsFields()
        fields.append(QgsField("Point_ID", QVariant.Int))
        fields.append(QgsField("Date_Time", QVariant.DateTime))
        fields.append(QgsField("Latitude", QVariant.Double))
        fields.append(QgsField("Longitude", QVariant.Double))
        fields.append(QgsField("Altitude", QVariant.Double))
        fields.append(QgsField("Velocity", QVariant.Double))
        fields.append(QgsField("Azimuth", QVariant.Double))
        fields.append(QgsField("Elevation", QVariant.Double))
        fields.append(QgsField("TrueAnomaly", QVariant.Double))
        fields.append(QgsField("Inclination", QVariant.Double))
        provider.addAttributes(fields)
        point_layer.updateFields()

        features = []
        for i, point in enumerate(points):
            current_time, lon, lat, alt, velocity, azimuth, elevation, true_anom, inc = point
            qdt = QDateTime(current_time.year, current_time.month, current_time.day,
                            current_time.hour, current_time.minute, current_time.second)
            feat = QgsFeature()
            feat.setFields(fields)
            feat.setAttribute("Point_ID", i)
            feat.setAttribute("Date_Time", qdt)
            feat.setAttribute("Latitude", lat)
            feat.setAttribute("Longitude", lon)
            feat.setAttribute("Altitude", alt)
            feat.setAttribute("Velocity", velocity)
            feat.setAttribute("Azimuth", azimuth)
            feat.setAttribute("Elevation", elevation)
            feat.setAttribute("TrueAnomaly", true_anom)
            feat.setAttribute("Inclination", inc)
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
            features.append(feat)

        if features:
            provider.addFeatures(features)
            point_layer.updateExtents()
        return point_layer

    def save_lines(self, geometries, layer_name):
        """
        Create an in-memory line layer from a list of geometries.

        :param points: List of tuples (datetime, lon, lat, ...), passed for compatibility.
        :param geometries: List of QgsGeometry objects representing line segments.
        :param layer_name: Name of the layer.
        :return: QgsVectorLayer containing the lines.
        """
        line_layer = QgsVectorLayer("LineString?crs=EPSG:4326", layer_name, "memory")
        provider = line_layer.dataProvider()
        provider.addAttributes([QgsField("ID", QVariant.Int)])
        line_layer.updateFields()

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