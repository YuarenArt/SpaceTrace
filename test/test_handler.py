import pytest
from SpaceTrace.src.Space_trace.orbital.handler import OrbitalLogicHandler

@pytest.mark.unit
@pytest.mark.parametrize("points,expected", [
    ([(10, 0), (20, 1)], [[(10, 0), (20, 1)]]),
    ([(179, 0), (-179, 2)], [[(179, 0), (180, 1)], [(-180, 1), (-179, 2)]]),
    ([(-179, 0), (179, 2)], [[(-179, 0), (-180, 1)], [(180, 1), (179, 2)]]),
])
def test_line_segments(points, expected):
    assert OrbitalLogicHandler().get_line_segments(points) == expected

@pytest.mark.unit
def test_empty_points_rejected():
    with pytest.raises(ValueError, match="empty"):
        OrbitalLogicHandler().get_line_segments([])

@pytest.mark.unit
def test_processor_format_validation():
    handler = OrbitalLogicHandler()
    with pytest.raises(ValueError, match="Incorrect TLE"):
        handler._get_processor(("one",), "TLE")
    with pytest.raises(ValueError, match="Unsupported"):
        handler._get_processor({}, "CSV")


@pytest.mark.unit
def test_one_point_has_no_line_geometry(qgis_app):
    assert OrbitalLogicHandler().generate_line_geometries([(10, 20)]) == []


@pytest.mark.unit
def test_antimeridian_geometry_segments_are_short(qgis_app):
    geometries = OrbitalLogicHandler().generate_line_geometries(
        [(179, 10), (-179, 11), (-178, 12)]
    )
    assert len(geometries) == 2
    for geometry in geometries:
        assert not geometry.isEmpty()
        xs = [point.x() for point in geometry.asPolyline()]
        assert max(xs) - min(xs) <= 180


@pytest.mark.unit
def test_polar_segment_does_not_create_empty_geometry(qgis_app):
    geometries = OrbitalLogicHandler().generate_line_geometries([(40, -85), (42, 85)])
    assert geometries and all(not geometry.isEmpty() for geometry in geometries)

