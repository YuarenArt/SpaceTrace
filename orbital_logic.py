"""
Orbital Logic Module
---------------------

This module contains functions for retrieving satellite TLE data and creating
orbital track layers. The functions are used to generate either persistent shapefile
layers on disk or temporary in-memory layers in QGIS.

Functions:
- get_spacetrack_tle: Retrieve TLE data for a satellite.
- create_orbital_track_shapefile_for_day: Generate a point shapefile for the orbital track.
- convert_points_shp_to_line: Convert a point shapefile to a polyline shapefile.
- create_persistent_orbital_track: Create persistent shapefiles (points and lines) on disk.
- create_in_memory_orbital_layers: Create temporary in-memory layers for the orbital track.
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


def get_spacetrack_tle(sat_id, start_date, end_date, username, password, latest=False):
    """
    Retrieve TLE (Two-Line Element) data for a given satellite.

    :param sat_id: Satellite NORAD ID.
    :param start_date: Start date for TLE retrieval.
    :param end_date: End date for TLE retrieval.
    :param latest: If True, retrieve the latest available TLE.
    :param username: SpaceTrack account login (email).
    :param password: SpaceTrack account password.
    :return: A tuple (tle_1, tle_2, orb_incl).
    """
    st = SpaceTrackClient(identity=username, password=password)
    if not latest:
        daterange = op.inclusive_range(start_date, end_date)
        data = st.tle(norad_cat_id=sat_id, orderby='epoch desc', limit=1, format='tle', epoch=daterange)
    else:
        data = st.tle_latest(norad_cat_id=sat_id, orderby='epoch desc', limit=1, format='tle')
    if not data:
        raise Exception('Failed to retrieve TLE for satellite with ID {}'.format(sat_id))
    tle_1 = data[0:69]
    tle_2 = data[70:139]
    orb_incl = data[78:86]
    return tle_1, tle_2, orb_incl


def create_orbital_track_shapefile_for_day(sat_id, track_day, step_minutes, output_shapefile, username, password):
    """
    Create a point shapefile representing the orbital track for a given day.

    :param sat_id: Satellite NORAD ID.
    :param track_day: Date for which the orbital track is computed.
    :param step_minutes: Time step (in minutes) for computing satellite positions.
    :param output_shapefile: Output filename for the point shapefile.
    :param username: SpaceTrack account login.
    :param password: SpaceTrack account password.
    """
    if track_day > date.today():
        print('Using the latest TLE data as of UTC {}'.format(datetime.utcnow()))
        tle_1, tle_2, orb_incl = get_spacetrack_tle(sat_id, None, None, latest=True, username=username, password=password)
    else:
        tle_1, tle_2, orb_incl = get_spacetrack_tle(sat_id, track_day, track_day + timedelta(days=1), latest=False, username=username, password=password)
    if not tle_1 or not tle_2:
        raise Exception('Unable to retrieve TLE for satellite with ID {}'.format(sat_id))
    orb = Orbital("N", line1=tle_1, line2=tle_2)
    track_shape = shapefile.Writer(output_shapefile, shapefile.POINT)
    # Define shapefile fields
    track_shape.field('Point_ID', 'N', 10)
    track_shape.field('Point_Num', 'N', 10)
    track_shape.field('Orbit_Num', 'N', 10)
    track_shape.field('Date_Time', 'C', 19)
    track_shape.field('Latitude', 'F', 10, 6)
    track_shape.field('Longitude', 'F', 11, 6)
    track_shape.field('Altitude', 'F', 20, 3)
    track_shape.field('Velocity', 'F', 10, 5)
    track_shape.field('Sun_Zenith', 'F', 7, 2)
    track_shape.field('Orbit_Incl', 'F', 9, 4)
    i = 0
    minutes = 0
    while minutes < 1440:
        utc_hour = int(minutes // 60)
        utc_minutes = int((minutes - (utc_hour * 60)) // 1)
        utc_seconds = int(round((minutes - (utc_hour * 60) - utc_minutes) * 60))
        utc_string = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            track_day.year, track_day.month, track_day.day, utc_hour, utc_minutes, utc_seconds)
        utc_time = datetime(track_day.year, track_day.month, track_day.day, utc_hour, utc_minutes, utc_seconds)
        # Calculate satellite position and parameters
        lon, lat, alt = orb.get_lonlatalt(utc_time)
        orb_num = orb.get_orbit_number(utc_time, tbus_style=False)
        sun_zenith = astronomy.sun_zenith_angle(utc_time, lon, lat)
        pos, vel = orb.get_position(utc_time, normalize=False)
        vel_ = np.sqrt(vel[0] ** 2 + vel[1] ** 2 + vel[2] ** 2)
        # Write point and its attributes to the shapefile
        track_shape.point(lon, lat)
        track_shape.record(i, i + 1, orb_num, utc_string, lat, lon, alt, vel_, sun_zenith, orb_incl)
        i += 1
        minutes += step_minutes
    # Write projection file (WGS84)
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
        print('Shapefile saved successfully')
    except Exception as e:
        raise Exception('Failed to save shapefile: {}'.format(e))


def convert_points_shp_to_line(input_shp, output_shp):
    """
    Convert a point shapefile to a polyline shapefile.

    This function reads the input point shapefile and creates a polyline shapefile
    by connecting the points in order. It splits the line into segments when a jump
    in longitude greater than 180° is detected.

    :param input_shp: Input point shapefile filename.
    :param output_shp: Output polyline shapefile filename.
    """
    reader = shapefile.Reader(input_shp)
    shapes = reader.shapes()
    if not shapes:
        raise Exception("Input shapefile contains no objects.")
    points = []
    for shp in shapes:
        if shp.points and len(shp.points) > 0:
            points.append(shp.points[0])
        else:
            raise Exception("Found a record without coordinates in the input shapefile.")
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
    print("Conversion complete. Polyline shapefile created: {}".format(output_shp))


def create_persistent_orbital_track(sat_id, track_day, step_minutes, output_shapefile, username, password):
    """
    Create persistent orbital track shapefiles on disk.

    This high-level function generates a point shapefile for the orbital track and then
    converts it into a polyline shapefile.

    :param sat_id: Satellite NORAD ID.
    :param track_day: Date for which the orbital track is computed.
    :param step_minutes: Time step (in minutes) for calculating satellite positions.
    :param output_shapefile: Output filename for the point shapefile.
    :param username: SpaceTrack account login.
    :param password: SpaceTrack account password.
    """
    create_orbital_track_shapefile_for_day(sat_id, track_day, step_minutes, output_shapefile, username, password)
    line_output_path = output_shapefile.replace('.shp', '_line.shp')
    convert_points_shp_to_line(output_shapefile, line_output_path)


def create_in_memory_orbital_layers(sat_id, track_day, step_minutes, username, password):
    """
    Create temporary in-memory layers representing the orbital track.

    This function computes satellite positions to generate both point and polyline
    layers in memory, which can be added to the QGIS project.

    :param sat_id: Satellite NORAD ID.
    :param track_day: Date for which the orbital track is computed.
    :param step_minutes: Time step (in minutes) for calculating positions.
    :param username: SpaceTrack account login.
    :param password: SpaceTrack account password.
    :return: A tuple (point_layer, line_layer) containing the in-memory layers.
    """
    if track_day > date.today():
        tle_1, tle_2, orb_incl = get_spacetrack_tle(sat_id, None, None, latest=True, username=username, password=password)
    else:
        tle_1, tle_2, orb_incl = get_spacetrack_tle(sat_id, track_day, track_day + timedelta(days=1), latest=False, username=username, password=password)
    if not tle_1 or not tle_2:
        raise Exception("Failed to retrieve TLE for satellite with ID {}".format(sat_id))
    orb = Orbital("N", line1=tle_1, line2=tle_2)
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
        velocity = np.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)
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
        except:
            feat.setAttribute("Orbit_Incl", 0.0)
        feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
        features.append(feat)
        i += 1
        minutes += step_minutes

    print("Total points created: {}".format(len(features)))
    if features:
        provider.addFeatures(features)
        point_layer.updateExtents()
    else:
        print("Warning: No points were added to the point layer.")

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
