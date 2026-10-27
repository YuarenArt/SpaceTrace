import pytest
from qgis.PyQt.QtCore import QTranslator
from test.conftest import ROOT

@pytest.mark.unit
def test_available_translation_files_load(qgis_app):
    files = list((ROOT / "i18n").glob("SpaceTracePlugin_*.qm"))
    assert files
    for path in files:
        assert QTranslator().load(str(path)), path
