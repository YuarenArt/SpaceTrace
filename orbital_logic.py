"""
This module contains the refactored classes for orbital track generation.

Classes:
- SpacetrackClientWrapper: A subclass that handles SpaceTrack API communication.
- OrbitalLogicHandler: A subclass that implements the main logic for computing
  satellite positions, creating shapefiles, and generating in-memory layers.
- OrbitalOrchestrator: Orchestrates the overall process by combining the
  client and logic handler.
"""

from datetime import datetime, date, timedelta
import os
import shapefile
import numpy as np
import spacetrack.operators as op
from spacetrack import SpaceTrackClient
from pyorbital.orbital import Orbital
from pyorbital import astronomy

# QGIS imports for creating in-memory layers
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsFields, QgsField
from PyQt5.QtCore import QVariant


class SpacetrackClientWrapper:
    """
    Wrapper for SpaceTrack API communication.

    This class encapsulates the logic to retrieve TLE (Two-Line Element) data
    for a given satellite using SpaceTrackClient.
    """
    def __init__(self, username, password):
        """
        Initialize the SpaceTrack client with user credentials.

        :param username: SpaceTrack account login (email).
        :param password: SpaceTrack account password.
        """
        self.username = username
        self.password = password
        self.client = SpaceTrackClient(identity=username, password=password)

    def get_tle(self, sat_id, track_day=None, latest=False):
        """
        Retrieve TLE data for the specified satellite.

        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for which TLE data is needed. If None or in the future,
                          the latest TLE data is used.
        :param latest: Boolean flag to force retrieval of the latest TLE.
        :return: Tuple (tle_1, tle_2, orb_incl) with TLE lines and orbital inclination.
        :raises Exception: If TLE data cannot be retrieved.
        """
        if latest or (track_day is None or track_day > date.today()):
            # Use the latest available TLE data
            data = self.client.tle_latest(norad_cat_id=sat_id, orderby='epoch desc', limit=1, format='tle')
        else:
            daterange = op.inclusive_range(track_day, track_day + timedelta(days=1))
            data = self.client.tle(norad_cat_id=sat_id, orderby='epoch desc', limit=1, format='tle', epoch=daterange)
        if not data:
            raise Exception(f'Failed to retrieve TLE for satellite with ID {sat_id}')
        tle_1 = data[0:69]
        tle_2 = data[70:139]
        orb_incl = data[78:86]
        return tle_1, tle_2, orb_incl


class OrbitalLogicHandler:
    """
    Implements the core logic for orbital track computation and layer creation.

    Provides methods to create point shapefiles, convert them into polyline shapefiles,
    and generate temporary in-memory QGIS layers.
    """
    def __init__(self):
        pass

    def create_point_shapefile_for_day(self, sat_id, track_day, step_minutes, output_shapefile, tle_data):
        """
        Create a point shapefile representing the orbital track for a given day.

        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for which the track is computed.
        :param step_minutes: Time step in minutes for computing positions.
        :param output_shapefile: Filename for the output point shapefile.
        :param tle_data: Tuple (tle_1, tle_2, orb_incl) for satellite.
        :raises Exception: If TLE data is missing or file saving fails.
        """
        tle_1, tle_2, orb_incl = tle_data
        if not tle_1 or not tle_2:
            raise Exception(f'Unable to retrieve valid TLE for satellite with ID {sat_id}')
        orb = Orbital("N", line1=tle_1, line2=tle_2)
        writer = shapefile.Writer(output_shapefile, shapefile.POINT)
        # Define fields for the shapefile
        writer.field('Point_ID', 'N', 10)
        writer.field('Point_Num', 'N', 10)
        writer.field('Orbit_Num', 'N', 10)
        writer.field('Date_Time', 'C', 19)
        writer.field('Latitude', 'F', 10, 6)
        writer.field('Longitude', 'F', 11, 6)
        writer.field('Altitude', 'F', 20, 3)
        writer.field('Velocity', 'F', 10, 5)
        writer.field('Sun_Zenith', 'F', 7, 2)
        writer.field('Orbit_Incl', 'F', 9, 4)

        i = 0
        minutes = 0
        while minutes < 1440:
            utc_hour = int(minutes // 60)
            utc_minutes = int((minutes - (utc_hour * 60)) // 1)
            utc_seconds = int(round((minutes - (utc_hour * 60) - utc_minutes) * 60))
            utc_string = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                track_day.year, track_day.month, track_day.day, utc_hour, utc_minutes, utc_seconds)
            utc_time = datetime(track_day.year, track_day.month, track_day.day, utc_hour, utc_minutes, utc_seconds)
            # Compute satellite position and parameters
            lon, lat, alt = orb.get_lonlatalt(utc_time)
            orbit_num = orb.get_orbit_number(utc_time, tbus_style=False)
            sun_zenith = astronomy.sun_zenith_angle(utc_time, lon, lat)
            pos, vel = orb.get_position(utc_time, normalize=False)
            velocity = np.sqrt(vel[0] ** 2 + vel[1] ** 2 + vel[2] ** 2)
            # Write point and record to shapefile
            writer.point(lon, lat)
            writer.record(i, i + 1, orbit_num, utc_string, lat, lon, alt, velocity, sun_zenith, orb_incl)
            i += 1
            minutes += step_minutes

        # Write projection file for WGS84
        try:
            prj_filename = output_shapefile.replace('.shp', '.prj')
            with open(prj_filename, "w") as prj:
                wgs84_wkt = (
                    'GEOGCS["WGS 84",DATUM["WGS_1984",'
                    'SPHEROID["WGS 84",6378137,298.257223563]],'
                    'PRIMEM["Greenwich",0],'
                    'UNIT["degree",0.0174532925199433]]'
                )
                prj.write(wgs84_wkt)
        except Exception as e:
            raise Exception(f'Failed to save shapefile: {e}')

    def convert_points_shp_to_line(self, input_shp, output_shp):
        """
        Convert a point shapefile to a polyline shapefile by connecting points.

        :param input_shp: Input point shapefile filename.
        :param output_shp: Output polyline shapefile filename.
        :raises Exception: If the input shapefile contains no objects or missing data.
        """
        reader = shapefile.Reader(input_shp)
        shapes = reader.shapes()
        if not shapes:
            raise Exception("Input shapefile contains no objects.")
        # Extract points from the shapefile
        points = []
        for shp in shapes:
            if shp.points and len(shp.points) > 0:
                points.append(shp.points[0])
            else:
                raise Exception("Found a record without coordinates in the input shapefile.")
        # Split points into segments if a jump in longitude > 180° is detected
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
        # Write projection file for WGS84
        prj_filename = os.path.splitext(output_shp)[0] + ".prj"
        with open(prj_filename, "w") as prj_file:
            wgs84_wkt = (
                'GEOGCS["WGS 84",DATUM["WGS_1984",'
                'SPHEROID["WGS 84",6378137,298.257223563]],'
                'PRIMEM["Greenwich",0],'
                'UNIT["degree",0.0174532925199433]]'
            )
            prj_file.write(wgs84_wkt)

    def create_persistent_orbital_track(self, sat_id, track_day, step_minutes, output_shapefile, tle_data):
        """
        High-level method to create persistent orbital track shapefiles on disk.

        It generates a point shapefile and converts it into a polyline shapefile.

        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for which the track is computed.
        :param step_minutes: Time step (minutes) for calculating positions.
        :param output_shapefile: Output filename for the point shapefile.
        :param tle_data: Tuple containing TLE information.
        """
        self.create_point_shapefile_for_day(sat_id, track_day, step_minutes, output_shapefile, tle_data)
        line_output_path = output_shapefile.replace('.shp', '_line.shp')
        self.convert_points_shp_to_line(output_shapefile, line_output_path)
        return output_shapefile, line_output_path

    def create_in_memory_layers(self, sat_id, track_day, step_minutes, tle_data):
        """
        Create temporary in-memory layers representing the orbital track.

        Computes satellite positions to generate both point and polyline layers.

        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for which the track is computed.
        :param step_minutes: Time step in minutes.
        :param tle_data: Tuple containing TLE information.
        :return: Tuple (point_layer, line_layer) of QGIS in-memory layers.
        :raises Exception: If TLE data is invalid.
        """
        tle_1, tle_2, orb_incl = tle_data
        if not tle_1 or not tle_2:
            raise Exception(f"Failed to retrieve valid TLE for satellite with ID {sat_id}")
        orb = Orbital("N", line1=tle_1, line2=tle_2)
        # Create the point layer
        point_layer = QgsVectorLayer("Point?crs=EPSG:4326", "Temporary Orbital Track", "memory")
        provider = point_layer.dataProvider()
        fields = QgsFields()
        fields.append(QgsField("Point_ID", QVariant.Int))
        fields.append(QgsField("Point_Num", QVariant.Int))
        fields.append(QgsField("Orbit_Num", QVariant.Int))
        fields.append(QgsField("Date_Time", QVariant.String))
        fields.append(QgsField("Latitude", QVariant.Double))
        fields.append(QgsField("Longitude", QVariant.Double))
        fields.append(QgsField("Altitude", QVariant.Double))
        fields.append(QgsField("Velocity", QVariant.Double))
        fields.append(QgsField("Sun_Zenith", QVariant.Double))
        fields.append(QgsField("Orbit_Incl", QVariant.Double))
        provider.addAttributes(fields)
        point_layer.updateFields()

        features = []
        i = 0
        minutes = 0
        while minutes < 1440:
            utc_hour = int(minutes // 60)
            utc_minutes = int((minutes - (utc_hour * 60)) // 1)
            utc_seconds = int(round((minutes - (utc_hour * 60) - utc_minutes) * 60))
            utc_time = datetime(track_day.year, track_day.month, track_day.day, utc_hour, utc_minutes, utc_seconds)
            utc_string = utc_time.strftime("%Y-%m-%d %H:%M:%S")
            lon, lat, alt = orb.get_lonlatalt(utc_time)
            orbit_num = orb.get_orbit_number(utc_time, tbus_style=False)
            sun_zenith = astronomy.sun_zenith_angle(utc_time, lon, lat)
            pos, vel = orb.get_position(utc_time, normalize=False)
            velocity = np.sqrt(vel[0] ** 2 + vel[1] ** 2 + vel[2] ** 2)
            feat = QgsFeature()
            feat.setFields(fields)
            feat.setAttribute("Point_ID", i)
            feat.setAttribute("Point_Num", i + 1)
            feat.setAttribute("Orbit_Num", orbit_num)
            feat.setAttribute("Date_Time", utc_string)
            feat.setAttribute("Latitude", lat)
            feat.setAttribute("Longitude", lon)
            feat.setAttribute("Altitude", alt)
            feat.setAttribute("Velocity", velocity)
            feat.setAttribute("Sun_Zenith", sun_zenith)
            try:
                feat.setAttribute("Orbit_Incl", float(orb_incl))
            except Exception:
                feat.setAttribute("Orbit_Incl", 0.0)
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
            features.append(feat)
            i += 1
            minutes += step_minutes

        if features:
            provider.addFeatures(features)
            point_layer.updateExtents()

        # Build polyline geometry from point features
        points = [[feat.geometry().asPoint().x(), feat.geometry().asPoint().y()] for feat in features]
        segments = []
        if points:
            current_segment = [points[0]]
            for pt in points[1:]:
                if abs(pt[0] - current_segment[-1][0]) > 180:
                    segments.append(current_segment)
                    current_segment = [pt]
                else:
                    current_segment.append(pt)
            if current_segment:
                segments.append(current_segment)
        # Create the line layer
        line_layer = QgsVectorLayer("LineString?crs=EPSG:4326", "Temporary Orbital Track_line", "memory")
        line_provider = line_layer.dataProvider()
        line_provider.addAttributes([QgsField("ID", QVariant.Int)])
        line_layer.updateFields()
        line_feat = QgsFeature()
        if len(segments) == 1:
            line_geom = QgsGeometry.fromPolylineXY([QgsPointXY(x, y) for x, y in segments[0]])
        else:
            parts = []
            for seg in segments:
                parts.append([QgsPointXY(x, y) for x, y in seg])
            line_geom = QgsGeometry.fromMultiPolylineXY(parts)
        line_feat.setGeometry(line_geom)
        line_feat.setAttributes([1])
        line_provider.addFeatures([line_feat])
        line_layer.updateExtents()

        return point_layer, line_layer


class OrbitalOrchestrator:
    """
    Orchestrates the overall process of retrieving TLE data and generating orbital track layers.

    It combines a SpaceTrack client (SpacetrackClientWrapper) and a logic handler
    (OrbitalLogicHandler) to produce either persistent shapefiles on disk or
    temporary in-memory QGIS layers.
    """
    def __init__(self, username, password):
        """
        Initialize the orchestrator with SpaceTrack credentials.

        :param username: SpaceTrack account login.
        :param password: SpaceTrack account password.
        """
        self.client = SpacetrackClientWrapper(username, password)
        self.logic_handler = OrbitalLogicHandler()

    def process_persistent_track(self, sat_id, track_day, step_minutes, output_shapefile):
        """
        Generate persistent orbital track shapefiles on disk.

        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :param output_shapefile: Output filename for the point shapefile.
        :return: Tuple (point_shapefile, line_shapefile) with file paths.
        """
        # Determine whether to use the latest TLE based on the track day.
        use_latest = track_day > date.today()
        tle_data = self.client.get_tle(sat_id, track_day, latest=use_latest)
        return self.logic_handler.create_persistent_orbital_track(
            sat_id, track_day, step_minutes, output_shapefile, tle_data
        )

    def process_in_memory_track(self, sat_id, track_day, step_minutes):
        """
        Generate temporary in-memory QGIS layers representing the orbital track.

        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :return: Tuple (point_layer, line_layer) of QGIS in-memory layers.
        """
        use_latest = track_day > date.today()
        tle_data = self.client.get_tle(sat_id, track_day, latest=use_latest)
        return self.logic_handler.create_in_memory_layers(sat_id, track_day, step_minutes, tle_data)