from abc import ABC, abstractmethod
import shapefile

from qgis.core import (
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
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
            writer = shapefile.Writer(output_path, shapefile.POINT)
            writer.field('Point_ID', 'N', 10)
            writer.field('Date_Time', 'C', 19) 
            writer.field('Latitude', 'F', 10, 6)
            writer.field('Longitude', 'F', 11, 6)
            writer.field('Altitude', 'F', 20, 3)
            writer.field('Velocity', 'F', 15, 3)
            writer.field('Azimuth', 'F', 10, 3)
            writer.field('Elevation', 'F', 10, 3)
            writer.field('TrueAnomaly', 'F', 11, 3)
            writer.field('Inclination', 'F', 11, 3)

            for i, point in enumerate(points):
                current_time, lon, lat, alt, velocity, azimuth, elevation, true_anomaly, inc = point
                utc_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
                writer.point(lon, lat)
                writer.record(
                    i, utc_string, lat, lon, alt, velocity, azimuth, elevation, true_anomaly, inc
                )
            self._write_prj(output_path)

    def save_lines(self, geometries, output_path):
        writer = shapefile.Writer(output_path, shapefile.POLYLINE)
        writer.field("ID", "N", size=10)
        for i, geom in enumerate(geometries):
            points = [(pt.x(), pt.y()) for pt in geom.get()]
            writer.line([points])
            writer.record(i + 1)
        writer.close()
        self._write_prj(output_path)

    def _write_prj(self, output_path):
        prj_filename = output_path.replace('.shp', '.prj')
        with open(prj_filename, "w") as prj_file:
            wgs84_wkt = (
                'GEOGCS["WGS 84",DATUM["WGS_1984",'
                'SPHEROID["WGS 84",6378137,298.257223563]],'
                'PRIMEM["Greenwich",0],'
                'UNIT["degree",0.0174532925199433]]'
            )
            prj_file.write(wgs84_wkt)

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
        options = QgsVectorFileWriter.SaveVectorOptions()
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