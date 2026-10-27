"""Shared deterministic fixtures for the QGIS bundled Python runtime."""
import importlib.util
import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest


ROOT = Path(__file__).resolve().parents[1]
# The checkout can be named "Space Trace". Register its actual plugin package
# under the name QGIS uses instead of importing modules as top-level "src".
if "SpaceTrace" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "SpaceTrace", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
    )
    package = importlib.util.module_from_spec(spec)
    sys.modules["SpaceTrace"] = package
    spec.loader.exec_module(package)

TLE_LINE1 = "1 25544U 98067A   25087.72483446  .00032194  00000-0  56484-3 0  9999"
TLE_LINE2 = "2 25544  51.6386 345.5386 0004029  59.5799 332.6073 15.50242233502686"
START = datetime(2025, 3, 28, 18, 0)


@pytest.fixture(scope="session")
def qgis_app():
    from qgis.core import QgsApplication, QgsProject

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QgsApplication.instance()
    owned = app is None
    if owned:
        app = QgsApplication([], True)
        app.initQgis()
    yield app
    QgsProject.instance().clear()
    # The process owns its application. Calling exitQgis while Python still
    # holds SIP layer wrappers can crash Qt on Windows.


@pytest.fixture(autouse=True)
def clean_project(request):
    if "qgis_app" in request.fixturenames:
        from qgis.core import QgsProject

        QgsProject.instance().clear()
        yield
        QgsProject.instance().clear()
    else:
        yield


@pytest.fixture
def tle_file(tmp_path):
    path = tmp_path / "iss.txt"
    path.write_text(f"{TLE_LINE1}\n{TLE_LINE2}\n", encoding="ascii")
    return path


@pytest.fixture
def iface(qgis_app):
    from qgis.PyQt.QtWidgets import QWidget

    result = Mock()
    result.mainWindow.return_value = QWidget()
    result.messageBar.return_value = Mock()
    yield result
    result.mainWindow.return_value.close()


@pytest.fixture
def plugin(iface, tmp_path):
    from SpaceTrace.src.Space_trace.Space_trace import SpaceTracePlugin

    result = SpaceTracePlugin(iface, log_path=str(tmp_path / "plugin.log"))
    yield result
    if result.dlg is not None:
        result.dlg.close()
    result.unload()
