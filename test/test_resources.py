import pytest
from qgis.PyQt.QtGui import QIcon

@pytest.mark.unit
def test_plugin_icon_is_registered(qgis_app):
    import SpaceTrace.resources
    assert not QIcon(":/plugins/Space_trace/icon.png").isNull()

