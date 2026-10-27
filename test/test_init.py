"""QGIS plugin packaging metadata."""
import configparser
import pytest
from test.conftest import ROOT

@pytest.mark.unit
def test_required_plugin_metadata():
    parser = configparser.ConfigParser()
    parser.optionxform = str
    assert parser.read(ROOT / "metadata.txt", encoding="utf-8")
    assert parser.has_section("general")
    for key in ("name", "description", "version", "qgisMinimumVersion", "email", "author"):
        assert parser.has_option("general", key)
        assert parser.get("general", key).strip()
