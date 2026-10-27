import pytest
from qgis.core import QgsCoordinateReferenceSystem, QgsProviderRegistry

@pytest.mark.integration
def test_qgis_runtime_has_vector_provider(qgis_app):
    assert "ogr" in QgsProviderRegistry.instance().providerList()
    assert QgsCoordinateReferenceSystem("EPSG:4326").isValid()
