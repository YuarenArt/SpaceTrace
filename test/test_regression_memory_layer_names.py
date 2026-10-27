"""Memory savers should honor a caller's requested layer name."""
import pytest

from SpaceTrace.src.Space_trace.orbital.saver import FactoryProvider


@pytest.mark.integration
@pytest.mark.parametrize("method", ["save_points", "save_lines"])
@pytest.mark.parametrize("norad_id", [None, 0, 25544])
def test_requested_layer_name_is_used_with_or_without_norad(qgis_app, method, norad_id):
    saver = FactoryProvider.get_factory("memory").get_saver()
    layer = getattr(saver, method)([], "My requested name", norad_id=norad_id)
    assert layer.isValid()
    assert layer.name() == "My requested name"


@pytest.mark.integration
@pytest.mark.parametrize("method,expected", [("save_points", "Points"), ("save_lines", "Lines")])
def test_default_layer_name_is_retained(qgis_app, method, expected):
    saver = FactoryProvider.get_factory("memory").get_saver()
    layer = getattr(saver, method)([])
    assert layer.name() == expected
