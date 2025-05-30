from qgis.core import (
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsFields,
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
)
from PyQt5.QtCore import QVariant, QDateTime, Qt
from typing import Optional, Callable
from abc import ABC, abstractmethod

class FileSaver(ABC):
    """
    Abstract base class for saving point and line geometries to QGIS layers or files.
    Supports ESRI Shapefile, GeoPackage, GeoJSON, and in-memory formats.
    """
    point_fields = [
        ("Point_ID", QVariant.Int),
        ("Date_Time", None),
        ("Latitude", QVariant.Double),
        ("Longitude", QVariant.Double),
        ("Altitude", QVariant.Double),
        ("Velocity", QVariant.Double),
        ("Azimuth", QVariant.Double),
        ("TrajectoryArc", QVariant.Double),
        ("TrueAnomaly", QVariant.Double),
        ("Inclination", QVariant.Double),
    ]

    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        """
        Initialize with a logging callback and set CRS.

        :param log_callback: Optional function to handle logging.
        """
        self.log_callback = log_callback
        self.project_crs = QgsProject.instance().crs()
        self.source_crs = QgsCoordinateReferenceSystem("EPSG:4326")

        if self.log_callback:
            self.log_callback(f"Initialized FileSaver with project CRS: {self.project_crs.authid()} "
                             f"({self.project_crs.description()})", "DEBUG")
            if not self.project_crs.isValid():
                self.log_callback("Project CRS is invalid; falling back to EPSG:4326", "WARNING")
                self.project_crs = self.source_crs
            else:
                self.log_callback(f"Source CRS: {self.source_crs.authid()} ({self.source_crs.description()})", "DEBUG")

    def _log(self, message: str, level: str = "INFO"):
        """
        Log a message using the provided callback.

        :param message: Message to log.
        :param level: Log level ("INFO", "DEBUG", "WARNING", "ERROR").
        """
        if self.log_callback:
            self.log_callback(message, level)

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name (e.g., 'ESRI Shapefile', 'GPKG')."""
        pass

    @property
    @abstractmethod
    def date_field_type(self):
        """Return the QVariant type for the Date_Time field."""
        pass

    @abstractmethod
    def prepare_date(self, dt):
        """Prepare datetime object for storage in the layer."""
        pass

    @abstractmethod
    def is_memory(self) -> bool:
        """Return True if the saver is for in-memory layers."""
        pass

    def _transform_geometry(self, geometry: QgsGeometry) -> QgsGeometry:
        """
        Transform geometry from source CRS (EPSG:4326) to project CRS if needed.

        :param geometry: Geometry to transform.
        :return: Transformed geometry.
        """
        if self.source_crs != self.project_crs:
            self._log(f"Transforming geometry from {self.source_crs.authid()} to {self.project_crs.authid()}", "DEBUG")
            transform = QgsCoordinateTransform(self.source_crs, self.project_crs, QgsProject.instance())
            geometry.transform(transform)
        return geometry

    def save_points(self, points, output_path_or_layername: Optional[str] = None) -> Optional[QgsVectorLayer]:
        """
        Save point data to a layer or file with detailed logging.

        :param points: List of point data tuples (datetime, lon, lat, alt, vel, az, arc, ta, inc).
        :param output_path_or_layername: Output file path or layer name for in-memory layers.
        :return: QgsVectorLayer for in-memory layers, None for file-based formats.
        """
        self._log(f"Starting save_points for format: {self.format_name}", "DEBUG")

        if not self.is_memory() and output_path_or_layername is None:
            self._log(f"Output path is required for {self.format_name} format but was None", "ERROR")
            raise ValueError(f"Output path is required for {self.format_name} format")

        layer_name = output_path_or_layername if output_path_or_layername else "Points"
        self._log(f"Creating point layer with name: {layer_name}, CRS: {self.project_crs.authid()}", "DEBUG")

        # Create a vector layer for points with the project's CRS
        layer = QgsVectorLayer(f"Point?crs={self.project_crs.authid()}", layer_name, "memory")
        prov = layer.dataProvider()

        # Define and add fields
        fields = QgsFields()
        for name, vtype in self.point_fields:
            t = vtype if name != "Date_Time" else self.date_field_type
            fields.append(QgsField(name, t))
        prov.addAttributes(fields)
        layer.updateFields()
        self._log(f"Fields added to point layer: {[field.name() for field in fields]}", "DEBUG")

        # Create point features
        feats = []
        for i, pt in enumerate(points):
            dt, lon, lat, alt, vel, az, arc, ta, inc = pt
            feat = QgsFeature()
            feat.setFields(fields)
            feat.setAttribute("Point_ID", i)
            feat.setAttribute("Date_Time", self.prepare_date(dt))
            feat.setAttribute("Latitude", lat)  # Store original WGS84 coordinates
            feat.setAttribute("Longitude", lon)
            feat.setAttribute("Altitude", alt)
            feat.setAttribute("Velocity", vel)
            feat.setAttribute("Azimuth", az)
            feat.setAttribute("TrajectoryArc", arc)
            feat.setAttribute("TrueAnomaly", ta)
            feat.setAttribute("Inclination", inc)

            # Create and transform geometry
            geometry = QgsGeometry.fromPointXY(QgsPointXY(lon, lat))
            geometry = self._transform_geometry(geometry)
            feat.setGeometry(geometry)
            feats.append(feat)
        self._log(f"Created {len(feats)} point features", "DEBUG")

        # Add features and save if necessary
        if feats:
            prov.addFeatures(feats)
            self._log(f"Added {len(feats)} features to point layer", "DEBUG")
            if not self.is_memory():
                self._log(f"Saving points to file: {output_path_or_layername}, CRS: {self.project_crs.authid()}", "DEBUG")
                write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(
                    layer, output_path_or_layername, "UTF-8", self.project_crs, self.format_name
                )
                if write_result != QgsVectorFileWriter.NoError:
                    self._log(f"Failed to save points to {output_path_or_layername}: {error_message}", "ERROR")
                    raise RuntimeError(f"Failed to save {self.format_name}: {error_message}")
                self._log(f"Successfully saved points to {output_path_or_layername}", "INFO")
            else:
                layer.updateExtents()
                self._log("Updated extents for in-memory point layer", "DEBUG")
        else:
            self._log("No point features were created", "WARNING")

        return layer if self.is_memory() else None

    def save_lines(self, geometries, output_path_or_layername: Optional[str] = None) -> Optional[QgsVectorLayer]:
        """
        Save line geometries to a layer or file with detailed logging.

        :param geometries: List of QgsGeometry objects representing line segments.
        :param output_path_or_layername: Output file path or layer name for in-memory layers.
        :return: QgsVectorLayer for in-memory layers, None for file-based formats.
        """
        self._log(f"Starting save_lines for format: {self.format_name}", "DEBUG")

        if not self.is_memory() and output_path_or_layername is None:
            self._log(f"Output path is required for {self.format_name} format but was None", "ERROR")
            raise ValueError(f"Output path is required for {self.format_name} format")

        layer_name = output_path_or_layername if output_path_or_layername else "Lines"
        self._log(f"Creating line layer with name: {layer_name}, CRS: {self.project_crs.authid()}", "DEBUG")

        # Create a vector layer for lines with the project's CRS
        layer = QgsVectorLayer(f"LineString?crs={self.project_crs.authid()}", layer_name, "memory")
        prov = layer.dataProvider()

        # Define and add fields
        fields = QgsFields()
        fields.append(QgsField("ID", QVariant.Int))
        prov.addAttributes(fields)
        layer.updateFields()
        self._log(f"Fields added to line layer: {[field.name() for field in fields]}", "DEBUG")

        # Verify 'ID' field exists
        id_index = layer.fields().indexFromName("ID")
        if id_index == -1:
            self._log("Field 'ID' was not added to the line layer", "ERROR")
        else:
            self._log(f"Field 'ID' found at index {id_index}", "DEBUG")

        # Create line features
        feats = []
        for i, geom in enumerate(geometries, start=1):
            feat = QgsFeature()
            feat.setFields(fields)
            if id_index != -1:
                feat.setAttribute("ID", i)
                self._log(f"Set attribute 'ID' = {i} for feature {i}", "DEBUG")
            else:
                self._log(f"Skipping attribute 'ID' for feature {i} as field is missing", "WARNING")

            # Transform geometry from WGS84 to project CRS
            transformed_geom = self._transform_geometry(geom)
            feat.setGeometry(transformed_geom)
            feats.append(feat)
        self._log(f"Created {len(feats)} line features", "DEBUG")

        # Add features and save if necessary
        if feats:
            prov.addFeatures(feats)
            self._log(f"Added {len(feats)} features to line layer", "DEBUG")
            if not self.is_memory():
                self._log(f"Saving lines to file: {output_path_or_layername}, CRS: {self.project_crs.authid()}", "DEBUG")
                write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(
                    layer, output_path_or_layername, "UTF-8", self.project_crs, self.format_name
                )
                if write_result != QgsVectorFileWriter.NoError:
                    self._log(f"Failed to save lines to {output_path_or_layername}: {error_message}", "ERROR")
                    raise RuntimeError(f"Failed to save {self.format_name}: {error_message}")
                self._log(f"Successfully saved lines to {output_path_or_layername}", "INFO")
            else:
                layer.updateExtents()
                self._log("Updated extents for in-memory line layer", "DEBUG")
        else:
            self._log("No line features were created", "WARNING")

        return layer if self.is_memory() else None


class ShpSaver(FileSaver):
    """Saver for ESRI Shapefile format."""
    format_name = "ESRI Shapefile"
    date_field_type = QVariant.String

    def prepare_date(self, dt):
        """Convert datetime to ISO string for shapefiles."""
        return QDateTime(dt.year, dt.month, dt.day,
                         dt.hour, dt.minute, dt.second).toString(Qt.ISODate)

    def is_memory(self) -> bool:
        return False


class GpkgSaver(FileSaver):
    """Saver for GeoPackage format."""
    format_name = "GPKG"
    date_field_type = QVariant.DateTime

    def prepare_date(self, dt):
        """Convert datetime to QDateTime for GeoPackage."""
        return QDateTime(dt.year, dt.month, dt.day,
                         dt.hour, dt.minute, dt.second)

    def is_memory(self) -> bool:
        return False


class GeoJsonSaver(FileSaver):
    """Saver for GeoJSON format."""
    format_name = "GeoJSON"
    date_field_type = QVariant.DateTime

    def prepare_date(self, dt):
        """Convert datetime to QDateTime for GeoJSON."""
        return QDateTime(dt.year, dt.month, dt.day,
                         dt.hour, dt.minute, dt.second)

    def is_memory(self) -> bool:
        return False


class MemorySaver(FileSaver):
    """Saver for in-memory QGIS layers."""
    format_name = "memory"
    date_field_type = QVariant.DateTime

    def prepare_date(self, dt):
        """Convert datetime to QDateTime for in-memory layers."""
        return QDateTime(dt.year, dt.month, dt.day,
                         dt.hour, dt.minute, dt.second)

    def is_memory(self) -> bool:
        return True


class SaverFactory(ABC):
    """Abstract factory for creating FileSaver instances."""
    @abstractmethod
    def get_saver(self) -> FileSaver:
        pass


class ShpFactory(SaverFactory):
    def get_saver(self) -> FileSaver:
        return ShpSaver()


class GpkgFactory(SaverFactory):
    def get_saver(self) -> FileSaver:
        return GpkgSaver()


class GeoJsonFactory(SaverFactory):
    def get_saver(self) -> FileSaver:
        return GeoJsonSaver()


class MemoryFactory(SaverFactory):
    def get_saver(self) -> FileSaver:
        return MemorySaver()


class FactoryProvider:
    """Provides appropriate SaverFactory based on format name."""
    @staticmethod
    def get_factory(format_name: str) -> SaverFactory:
        fmt = format_name.lower()
        if fmt == 'shp':
            return ShpFactory()
        elif fmt == 'gpkg':
            return GpkgFactory()
        elif fmt == 'geojson':
            return GeoJsonFactory()
        elif fmt == 'memory':
            return MemoryFactory()
        else:
            raise ValueError(f"Unsupported format: {format_name}")