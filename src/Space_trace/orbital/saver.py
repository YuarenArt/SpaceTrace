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
    Works directly in the project CRS unless a different input CRS is specified.
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

    def __init__(
        self,
        log_callback: Optional[Callable[[str, str], None]] = None,
        input_crs: Optional[QgsCoordinateReferenceSystem] = None
    ):
        """
        Initialize with a logging callback and set both input CRS and project CRS.

        :param log_callback: Optional function to handle logging.
        :param input_crs: CRS of the input coordinates. If None, defaults to project CRS.
        """
        self.log_callback = log_callback
        self.project_crs = QgsProject.instance().crs()

        # If the user did not specify an input CRS, assume the input is already in project CRS.
        if input_crs and input_crs.isValid():
            self.input_crs = input_crs
        else:
            self.input_crs = self.project_crs

        if self.log_callback:
            self._log(
                f"Initialized FileSaver with project CRS: {self.project_crs.authid()} "
                f"({self.project_crs.description()}); input CRS: {self.input_crs.authid()}",
                "DEBUG"
            )

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
        """Return the format name (e.g., 'ESRI Shapefile', 'GPKG', 'GeoJSON', 'memory')."""
        pass

    @property
    @abstractmethod
    def date_field_type(self):
        """Return the QVariant type for the Date_Time field."""
        pass

    @abstractmethod
    def prepare_date(self, dt):
        """Prepare a Python datetime for storage in the layer."""
        pass

    @abstractmethod
    def is_memory(self) -> bool:
        """Return True if this saver writes to an in-memory layer."""
        pass

    def _transform_geometry(self, geometry: QgsGeometry) -> QgsGeometry:
        """
        Transform geometry from input CRS to project CRS if needed.

        :param geometry: Geometry to transform.
        :return: Transformed geometry.
        """
        if self.input_crs != self.project_crs:
            self._log(
                f"Transforming geometry from {self.input_crs.authid()} "
                f"to {self.project_crs.authid()}",
                "DEBUG"
            )
            transform = QgsCoordinateTransform(
                self.input_crs, self.project_crs, QgsProject.instance()
            )
            geometry.transform(transform)
        return geometry

    def save_points(
        self,
        points,
        output_path_or_layername: Optional[str] = None,
        norad_id: Optional[int] = None
    ) -> Optional[QgsVectorLayer]:
        """
        Save point data to a layer or file.

        :param points: List of point‐tuples: (datetime, lon, lat, alt, vel, az, arc, ta, inc).
                       Coordinates must be in the input CRS.
        :param output_path_or_layername: File path (for disk formats) or layer name (for memory).
        :return: QgsVectorLayer (for memory) or None (for disk).
        """
        self._log(f"Starting save_points for format: {self.format_name}", "DEBUG")

        if not self.is_memory() and not output_path_or_layername:
            self._log(
                f"Output path is required for {self.format_name} format but was None",
                "ERROR"
            )
            raise ValueError(f"Output path is required for {self.format_name} format")
        
        if self.is_memory():
            layer_name = output_path_or_layername or f"points_{norad_id}" if norad_id else "Points"
        else:
            layer_name = output_path_or_layername

        self._log(
            f"Creating point layer '{layer_name}' in CRS {self.project_crs.authid()}",
            "DEBUG"
        )

        # Create a vector layer for points with the project's CRS
        layer = QgsVectorLayer(
            f"Point?crs={self.project_crs.authid()}",
            layer_name,
            "memory"
        )
        prov = layer.dataProvider()

        # Define and add fields
        fields = QgsFields()
        for name, vtype in self.point_fields:
            t = vtype if name != "Date_Time" else self.date_field_type
            fields.append(QgsField(name, t))
        prov.addAttributes(fields)
        layer.updateFields()

        # Create and accumulate features
        feats = []
        for i, pt in enumerate(points):
            dt, lon, lat, alt, vel, az, arc, ta, inc = pt
            feat = QgsFeature()
            feat.setFields(fields)
            feat.setAttribute("Point_ID", i)
            feat.setAttribute("Date_Time", self.prepare_date(dt))
            # Store original input coordinates as attributes, even if input CRS != EPSG:4326
            feat.setAttribute("Latitude", lat)
            feat.setAttribute("Longitude", lon)
            feat.setAttribute("Altitude", alt)
            feat.setAttribute("Velocity", vel)
            feat.setAttribute("Azimuth", az)
            feat.setAttribute("TrajectoryArc", arc)
            feat.setAttribute("TrueAnomaly", ta)
            feat.setAttribute("Inclination", inc)

            # Build geometry in input CRS, then transform if needed
            geometry = QgsGeometry.fromPointXY(QgsPointXY(lon, lat))
            geometry = self._transform_geometry(geometry)
            feat.setGeometry(geometry)
            feats.append(feat)

        self._log(f"Created {len(feats)} point features", "DEBUG")

        if feats:
            prov.addFeatures(feats)
            self._log(f"Added {len(feats)} features to point layer", "DEBUG")

            if not self.is_memory():
                self._log(
                    f"Saving points to file: {output_path_or_layername} "
                    f"in CRS {self.project_crs.authid()}",
                    "DEBUG"
                )
                write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(
                    layer,
                    output_path_or_layername,
                    "UTF-8",
                    self.project_crs,
                    self.format_name
                )
                if write_result != QgsVectorFileWriter.NoError:
                    self._log(
                        f"Failed to save points to {output_path_or_layername}: {error_message}",
                        "ERROR"
                    )
                    raise RuntimeError(
                        f"Failed to save {self.format_name}: {error_message}"
                    )
                self._log(f"Successfully saved points to {output_path_or_layername}", "INFO")
            else:
                layer.updateExtents()
                self._log("Updated extents for in-memory point layer", "DEBUG")
        else:
            self._log("No point features were created", "WARNING")

        return layer if self.is_memory() else None

    def save_lines(
        self,
        geometries,
        output_path_or_layername: Optional[str] = None,
        norad_id: Optional[int] = None
    ) -> Optional[QgsVectorLayer]:
        """
        Save line geometries to a layer or file.

        :param geometries: List of QgsGeometry objects (constructed in input CRS).
        :param output_path_or_layername: File path (for disk) or layer name (for memory).
        :return: QgsVectorLayer (for memory) or None (for disk).
        """
        self._log(f"Starting save_lines for format: {self.format_name}", "DEBUG")

        if not self.is_memory() and not output_path_or_layername:
            self._log(
                f"Output path is required for {self.format_name} format but was None",
                "ERROR"
            )
            raise ValueError(f"Output path is required for {self.format_name} format")

        if self.is_memory():
            layer_name = output_path_or_layername or f"line_{norad_id}" if norad_id else "Lines"
        else:
            layer_name = output_path_or_layername

        self._log(
            f"Creating line layer '{layer_name}' in CRS {self.project_crs.authid()}",
            "DEBUG"
        )

        # Create a vector layer for lines with the project's CRS
        layer = QgsVectorLayer(
            f"LineString?crs={self.project_crs.authid()}",
            layer_name,
            "memory"
        )
        prov = layer.dataProvider()

        # Define and add a single ID field
        fields = QgsFields()
        fields.append(QgsField("ID", QVariant.Int))
        prov.addAttributes(fields)
        layer.updateFields()
        self._log(f"Fields added to line layer: {[f.name() for f in fields]}", "DEBUG")

        id_index = layer.fields().indexFromName("ID")
        if id_index == -1:
            self._log("Field 'ID' was not added to the line layer", "ERROR")
        else:
            self._log(f"Field 'ID' found at index {id_index}", "DEBUG")

        # Create and accumulate features
        feats = []
        for i, geom in enumerate(geometries, start=1):
            feat = QgsFeature()
            feat.setFields(fields)
            if id_index != -1:
                feat.setAttribute("ID", i)
            else:
                self._log(
                    f"Skipping attribute 'ID' for feature {i} as field is missing",
                    "WARNING"
                )

            # Transform geometry from input CRS to project CRS if needed
            transformed_geom = self._transform_geometry(geom)
            feat.setGeometry(transformed_geom)
            feats.append(feat)

        self._log(f"Created {len(feats)} line features", "DEBUG")

        if feats:
            prov.addFeatures(feats)
            self._log(f"Added {len(feats)} features to line layer", "DEBUG")

            if not self.is_memory():
                self._log(
                    f"Saving lines to file: {output_path_or_layername} "
                    f"in CRS {self.project_crs.authid()}",
                    "DEBUG"
                )
                write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(
                    layer,
                    output_path_or_layername,
                    "UTF-8",
                    self.project_crs,
                    self.format_name
                )
                if write_result != QgsVectorFileWriter.NoError:
                    self._log(
                        f"Failed to save lines to {output_path_or_layername}: {error_message}",
                        "ERROR"
                    )
                    raise RuntimeError(
                        f"Failed to save {self.format_name}: {error_message}"
                    )
                self._log(f"Successfully saved lines to {output_path_or_layername}", "INFO")
            else:
                layer.updateExtents()
                self._log("Updated extents for in-memory line layer", "DEBUG")
        else:
            self._log("No line features were created", "WARNING")

        return layer if self.is_memory() else None


class ShpSaver(FileSaver):
    """Saver for ESRI Shapefile format (disk)."""
    format_name = "ESRI Shapefile"
    date_field_type = QVariant.String

    def prepare_date(self, dt):
        """Convert datetime to ISO string for shapefiles."""
        return QDateTime(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second
        ).toString(Qt.ISODate)

    def is_memory(self) -> bool:
        return False


class GpkgSaver(FileSaver):
    """Saver for GeoPackage format (disk)."""
    format_name = "GPKG"
    date_field_type = QVariant.DateTime

    def prepare_date(self, dt):
        """Convert datetime to QDateTime for GeoPackage."""
        return QDateTime(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second
        )

    def is_memory(self) -> bool:
        return False


class GeoJsonSaver(FileSaver):
    """Saver for GeoJSON format (disk)."""
    format_name = "GeoJSON"
    date_field_type = QVariant.DateTime

    def prepare_date(self, dt):
        """Convert datetime to QDateTime for GeoJSON."""
        return QDateTime(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second
        )

    def is_memory(self) -> bool:
        return False


class MemorySaver(FileSaver):
    """Saver for in-memory QGIS layers."""
    format_name = "memory"
    date_field_type = QVariant.DateTime

    def prepare_date(self, dt):
        """Convert datetime to QDateTime for in-memory layers."""
        return QDateTime(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second
        )

    def is_memory(self) -> bool:
        return True


class SaverFactory(ABC):
    """Abstract factory for creating FileSaver instances."""
    @abstractmethod
    def get_saver(
        self,
        log_callback: Optional[Callable[[str, str], None]] = None,
        input_crs: Optional[QgsCoordinateReferenceSystem] = None
    ) -> FileSaver:
        pass


class ShpFactory(SaverFactory):
    def get_saver(
        self,
        log_callback: Optional[Callable[[str, str], None]] = None,
        input_crs: Optional[QgsCoordinateReferenceSystem] = None
    ) -> FileSaver:
        return ShpSaver(log_callback=log_callback, input_crs=input_crs)


class GpkgFactory(SaverFactory):
    def get_saver(
        self,
        log_callback: Optional[Callable[[str, str], None]] = None,
        input_crs: Optional[QgsCoordinateReferenceSystem] = None
    ) -> FileSaver:
        return GpkgSaver(log_callback=log_callback, input_crs=input_crs)


class GeoJsonFactory(SaverFactory):
    def get_saver(
        self,
        log_callback: Optional[Callable[[str, str], None]] = None,
        input_crs: Optional[QgsCoordinateReferenceSystem] = None
    ) -> FileSaver:
        return GeoJsonSaver(log_callback=log_callback, input_crs=input_crs)


class MemoryFactory(SaverFactory):
    def get_saver(
        self,
        log_callback: Optional[Callable[[str, str], None]] = None,
        input_crs: Optional[QgsCoordinateReferenceSystem] = None
    ) -> FileSaver:
        return MemorySaver(log_callback=log_callback, input_crs=input_crs)


class FactoryProvider:
    """
    Provides the appropriate SaverFactory based on a format name.
    Usage: factory = FactoryProvider.get_factory('shp')
           saver   = factory.get_saver(log_callback=my_logger, input_crs=my_input_crs)
    """
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
