"""Real PyQGIS data pipeline; all files are written into pytest's temporary directory."""
import json
import math
from datetime import timedelta
import pytest
from qgis.core import QgsVectorLayer
from SpaceTrace.src.config.orbital import OrbitalConfig
from SpaceTrace.src.data_retriver.data_retriver import LocalFileRetriever
from SpaceTrace.src.Space_trace.orbital.facade import OrbitalTrackFacade
from test.conftest import START, TLE_LINE1, TLE_LINE2

@pytest.mark.integration
@pytest.mark.parametrize("data_format", ["TLE", "OMM"])
@pytest.mark.parametrize("fmt", ["gpkg", "geojson", "shp"])
@pytest.mark.parametrize("create_line", [False, True])
def test_local_tle_to_persistent_layers(qgis_app, tle_file, tmp_path, data_format, fmt, create_line):
    if data_format == "OMM":
        source = tmp_path / "iss.json"
        source.write_text(json.dumps([{"TLE_LINE1": TLE_LINE1, "TLE_LINE2": TLE_LINE2,
                                       "INCLINATION": 51.6386}]), encoding="utf-8")
    else:
        source = tle_file
    output = tmp_path / f"track.{fmt}"
    config = OrbitalConfig(sat_id=25544, start_datetime=START, duration_hours=1,
                           step_minutes=10, output_path=str(output), file_format=fmt,
                           create_line_layer=create_line, data_format=data_format,
                           data_file_path=str(source))
    point_file, line_file = OrbitalTrackFacade(LocalFileRetriever()).process_persistent_track(config)
    points = QgsVectorLayer(point_file, "points", "ogr")
    assert points.isValid()
    assert points.featureCount() == 7
    assert points.crs().authid() == "EPSG:4326"
    if create_line:
        lines = QgsVectorLayer(line_file, "lines", "ogr")
        assert lines.isValid() and lines.featureCount() >= 1
        del lines
    else:
        assert line_file is None
    del points

@pytest.mark.integration
@pytest.mark.parametrize("data_format", ["TLE", "OMM"])
@pytest.mark.parametrize("create_line", [False, True])
def test_local_data_to_memory_layers(qgis_app, tle_file, tmp_path, data_format, create_line):
    if data_format == "OMM":
        source = tmp_path / "iss.json"
        source.write_text(json.dumps([{"TLE_LINE1": TLE_LINE1, "TLE_LINE2": TLE_LINE2,
                                       "INCLINATION": 51.6386}]), encoding="utf-8")
    else:
        source = tle_file
    config = OrbitalConfig(sat_id=25544, start_datetime=START, duration_hours=1,
                           step_minutes=10, data_format=data_format,
                           create_line_layer=create_line, data_file_path=str(source))
    points, lines = OrbitalTrackFacade(LocalFileRetriever()).process_in_memory_track(config)
    assert points.isValid() and points.featureCount() == 7
    assert (lines is not None) == create_line
    if lines:
        assert lines.isValid() and lines.featureCount() >= 1
    assert not (tmp_path / "data").exists()
    del points, lines

@pytest.mark.integration
def test_save_retrieved_tle(qgis_app, tle_file, tmp_path):
    messages = []
    callback = lambda message, level="INFO": messages.append(message)
    config = OrbitalConfig(sat_id=25544, start_datetime=START, duration_hours=1,
                           step_minutes=10, data_file_path=str(tle_file),
                           save_data=True, save_data_path=str(tmp_path / "saved.txt"))
    OrbitalTrackFacade(LocalFileRetriever(callback), callback).process_in_memory_track(config)
    saved = tmp_path / "saved_tle.txt"
    assert saved.exists()
    assert TLE_LINE1 in saved.read_text()
    assert sum("TLE data saved" in message for message in messages) == 1

@pytest.mark.integration
def test_save_retrieved_omm(qgis_app, tmp_path):
    messages = []
    callback = lambda message, level="INFO": messages.append(message)
    source = tmp_path / "iss.json"
    data = [{"TLE_LINE1": TLE_LINE1, "TLE_LINE2": TLE_LINE2,
             "INCLINATION": 51.6386}]
    source.write_text(json.dumps(data), encoding="utf-8")
    config = OrbitalConfig(sat_id=25544, start_datetime=START, duration_hours=1,
                           step_minutes=10, data_format="OMM", data_file_path=str(source),
                           save_data=True, save_data_path=str(tmp_path / "saved.json"))
    OrbitalTrackFacade(LocalFileRetriever(callback), callback).process_in_memory_track(config)
    assert json.loads((tmp_path / "saved_omm.json").read_text()) == data
    assert sum("OMM data saved" in message for message in messages) == 1

@pytest.mark.integration
def test_project_crs_transforms_geometry_but_keeps_lonlat_attributes(qgis_app, tle_file):
    from qgis.core import QgsCoordinateReferenceSystem, QgsProject

    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
    config = OrbitalConfig(sat_id=25544, start_datetime=START, duration_hours=1,
                           step_minutes=10, data_file_path=str(tle_file),
                           create_line_layer=False)
    points, lines = OrbitalTrackFacade(LocalFileRetriever()).process_in_memory_track(config)
    assert lines is None
    assert points.crs().authid() == "EPSG:3857"
    feature = next(points.getFeatures())
    lon, lat = feature["Longitude"], feature["Latitude"]
    xy = feature.geometry().asPoint()
    assert abs(xy.x() - lon) > 1000
    assert abs(xy.y() - lat) > 1000
    del points, lines, feature


@pytest.mark.integration
@pytest.mark.parametrize("data_format,payload", [
    ("TLE", ""),
    ("TLE", "1 broken\n2 broken\n"),
    ("OMM", "{"),
    ("OMM", "[]"),
    ("OMM", "{}"),
    ("OMM", '[{"TLE_LINE1": "bad"}]'),
])
def test_invalid_local_data_is_rejected_before_writing(
    qgis_app, tmp_path, data_format, payload
):
    source = tmp_path / ("bad.txt" if data_format == "TLE" else "bad.json")
    source.write_text(payload, encoding="utf-8")
    output = tmp_path / "track.gpkg"
    config = OrbitalConfig(
        sat_id=25544, start_datetime=START, duration_hours=1, step_minutes=10,
        data_format=data_format, data_file_path=str(source),
        output_path=str(output), file_format="gpkg",
    )
    with pytest.raises(Exception):
        OrbitalTrackFacade(LocalFileRetriever()).process_persistent_track(config)
    assert not output.exists()


@pytest.mark.integration
def test_one_point_creates_no_invalid_line(qgis_app, tle_file, tmp_path):
    config = OrbitalConfig(
        sat_id=25544, start_datetime=START, duration_hours=0.1, step_minutes=60,
        data_format="TLE", data_file_path=str(tle_file), create_line_layer=True,
    )
    point_layer, line_layer = OrbitalTrackFacade(LocalFileRetriever()).process_in_memory_track(config)
    assert point_layer.featureCount() == 1
    assert line_layer is None
    del point_layer

    config.output_path = str(tmp_path / "one.gpkg")
    config.file_format = "gpkg"
    point_file, line_file = OrbitalTrackFacade(LocalFileRetriever()).process_persistent_track(config)
    assert QgsVectorLayer(point_file, "points", "ogr").featureCount() == 1
    assert line_file is None


@pytest.mark.integration
@pytest.mark.parametrize("fmt", ["gpkg", "geojson", "shp"])
def test_existing_output_is_not_overwritten(qgis_app, tle_file, tmp_path, fmt):
    output = tmp_path / f"track.{fmt}"
    config = OrbitalConfig(
        sat_id=25544, start_datetime=START, duration_hours=1, step_minutes=10,
        data_format="TLE", data_file_path=str(tle_file),
        output_path=str(output), file_format=fmt, create_line_layer=True,
    )
    facade = OrbitalTrackFacade(LocalFileRetriever())
    facade.process_persistent_track(config)
    original = output.read_bytes()
    with pytest.raises(FileExistsError, match="already exists"):
        facade.process_persistent_track(config)
    assert output.read_bytes() == original


@pytest.mark.integration
def test_oversized_track_is_rejected_before_propagation(qgis_app, tle_file):
    from SpaceTrace.src.orbital_data_processor.skyfield import SkyfieldOrbitalDataProcessor

    processor = SkyfieldOrbitalDataProcessor("ISS", TLE_LINE1, TLE_LINE2)
    with pytest.raises(ValueError, match="maximum"):
        processor.propagate(START, 168, 0.01)


@pytest.mark.integration
@pytest.mark.parametrize("duration,step,count", [
    (0.1, 60, 1),
    (0.1, 0.01, 601),
    (1, 10, 7),
    (168, 60, 169),
])
def test_track_time_boundaries(qgis_app, duration, step, count):
    from SpaceTrace.src.orbital_data_processor.skyfield import SkyfieldOrbitalDataProcessor

    processor = SkyfieldOrbitalDataProcessor("ISS", TLE_LINE1, TLE_LINE2)
    values = processor.propagate(START, duration, step)
    assert len(values) == count
    assert values[0][0] == START
    assert values[-1][0] <= START + timedelta(hours=duration)
    assert all(math.isfinite(number) for point in values for number in point[1:])


@pytest.mark.integration
def test_persistent_layer_respects_project_crs_and_attributes(qgis_app, tle_file, tmp_path):
    from qgis.core import QgsCoordinateReferenceSystem, QgsProject

    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
    config = OrbitalConfig(
        sat_id=25544, start_datetime=START, duration_hours=1, step_minutes=10,
        data_format="TLE", data_file_path=str(tle_file),
        output_path=str(tmp_path / "mercator.gpkg"), file_format="gpkg",
        create_line_layer=False,
    )
    point_file, _ = OrbitalTrackFacade(LocalFileRetriever()).process_persistent_track(config)
    points = QgsVectorLayer(point_file, "points", "ogr")
    assert points.isValid() and points.crs().authid() == "EPSG:3857"
    feature = next(points.getFeatures())
    assert feature.geometry().isGeosValid()
    assert math.isfinite(feature["Velocity"])
    assert abs(feature.geometry().asPoint().x() - feature["Longitude"]) > 1000
    del points, feature


@pytest.mark.integration
def test_reference_orbit_values_and_point_attributes(qgis_app, tle_file):
    config = OrbitalConfig(
        sat_id=25544, start_datetime=START, duration_hours=0.1, step_minutes=60,
        data_format="TLE", data_file_path=str(tle_file), create_line_layer=False,
    )
    points, _ = OrbitalTrackFacade(LocalFileRetriever()).process_in_memory_track(config)
    feature = next(points.getFeatures())
    assert feature["Longitude"] == pytest.approx(64.5652, abs=0.01)
    assert feature["Latitude"] == pytest.approx(5.6224, abs=0.01)
    assert feature["Altitude"] == pytest.approx(417.274, abs=0.1)
    assert feature["Velocity"] == pytest.approx(7.6619, abs=0.01)
    assert feature["Inclination"] == pytest.approx(51.6386, abs=0.01)
    assert feature.geometry().asPoint().x() == pytest.approx(feature["Longitude"])
    assert feature.geometry().asPoint().y() == pytest.approx(feature["Latitude"])
    del points, feature


@pytest.mark.integration
def test_invalid_project_crs_falls_back_to_wgs84(qgis_app, tle_file):
    from qgis.core import QgsCoordinateReferenceSystem, QgsProject

    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem())
    config = OrbitalConfig(
        sat_id=25544, start_datetime=START, duration_hours=0.1, step_minutes=60,
        data_format="TLE", data_file_path=str(tle_file), create_line_layer=False,
    )
    points, _ = OrbitalTrackFacade(LocalFileRetriever()).process_in_memory_track(config)
    assert points.crs().authid() == "EPSG:4326"
    del points


@pytest.mark.integration
def test_line_write_failure_reports_partial_output(qgis_app, tle_file, tmp_path, monkeypatch):
    from SpaceTrace.src.Space_trace.orbital.saver import FactoryProvider
    from qgis.core import QgsCoordinateReferenceSystem

    saver = FactoryProvider.get_factory("gpkg").get_saver(
        input_crs=QgsCoordinateReferenceSystem("EPSG:4326")
    )

    def fail_lines(*args, **kwargs):
        raise OSError("simulated line write failure")

    monkeypatch.setattr(type(saver), "save_lines", fail_lines)
    output = tmp_path / "partial.gpkg"
    config = OrbitalConfig(
        sat_id=25544, start_datetime=START, duration_hours=1, step_minutes=10,
        data_format="TLE", data_file_path=str(tle_file),
        output_path=str(output), file_format="gpkg", create_line_layer=True,
    )
    with pytest.raises(RuntimeError, match="Partial point file remains"):
        OrbitalTrackFacade(LocalFileRetriever()).process_persistent_track(config)
    assert output.exists()
    assert QgsVectorLayer(str(output), "partial points", "ogr").featureCount() == 7


@pytest.mark.integration
@pytest.mark.parametrize("fmt", ["gpkg", "geojson", "shp"])
def test_persistent_schema_values_and_geometry(qgis_app, tle_file, tmp_path, fmt):
    config = OrbitalConfig(
        sat_id=25544, start_datetime=START, duration_hours=1, step_minutes=10,
        data_format="TLE", data_file_path=str(tle_file),
        output_path=str(tmp_path / f"schema.{fmt}"), file_format=fmt,
        create_line_layer=False,
    )
    point_file, _ = OrbitalTrackFacade(LocalFileRetriever()).process_persistent_track(config)
    points = QgsVectorLayer(point_file, "points", "ogr")
    assert points.isValid() and points.featureCount() == 7
    names = set(points.fields().names())
    assert {"Point_ID", "Latitude", "Longitude", "Altitude", "Velocity"} <= names
    if fmt == "shp":
        assert {"Trajectory", "TrueAnomal", "Inclinatio"} <= names
    else:
        assert {"TrajectoryArc", "TrueAnomaly", "Inclination"} <= names
    feature = next(points.getFeatures())
    assert feature.geometry().isGeosValid()
    assert math.isfinite(feature["Altitude"])
    assert math.isfinite(feature["Velocity"])
    assert abs(feature["Latitude"]) <= 90
    assert abs(feature["Longitude"]) <= 180
    del points, feature


@pytest.mark.integration
def test_invalid_project_crs_falls_back_for_persistent_file(qgis_app, tle_file, tmp_path):
    from qgis.core import QgsCoordinateReferenceSystem, QgsProject

    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem())
    config = OrbitalConfig(
        sat_id=25544, start_datetime=START, duration_hours=1, step_minutes=10,
        data_format="TLE", data_file_path=str(tle_file),
        output_path=str(tmp_path / "fallback.gpkg"), file_format="gpkg",
        create_line_layer=False,
    )
    point_file, _ = OrbitalTrackFacade(LocalFileRetriever()).process_persistent_track(config)
    points = QgsVectorLayer(point_file, "points", "ogr")
    assert points.isValid() and points.crs().authid() == "EPSG:4326"
    del points
