from unittest.mock import Mock
import pytest
from SpaceTrace.src.Space_trace.orbital.facade import OrbitalTrackFacade
from SpaceTrace.src.config.orbital import OrbitalConfig
from test.conftest import START, TLE_LINE1, TLE_LINE2

@pytest.mark.unit
def test_facade_passes_config_and_data_to_handler(tmp_path):
    data = (TLE_LINE1, TLE_LINE2, 51.6386)
    retriever = Mock()
    retriever.retrieve_data.return_value = data
    facade = OrbitalTrackFacade(retriever)
    facade.logic_handler = Mock()
    facade.logic_handler.create_persistent_orbital_track.return_value = ("points.gpkg", None)
    config = OrbitalConfig(sat_id=25544, start_datetime=START, duration_hours=1,
                           step_minutes=10, output_path=str(tmp_path / "points.gpkg"), file_format="gpkg")
    assert facade.process_persistent_track(config) == ("points.gpkg", None)
    retriever.retrieve_data.assert_called_once_with(config)
    facade.logic_handler.create_persistent_orbital_track.assert_called_once_with(
        data, "TLE", START, 1, 10, config.output_path, "gpkg", True, 25544)

@pytest.mark.unit
def test_memory_track_does_not_write_plugin_directory():
    retriever = Mock()
    retriever.retrieve_data.return_value = (TLE_LINE1, TLE_LINE2, 51.6386)
    facade = OrbitalTrackFacade(retriever)
    facade.logic_handler = Mock()
    facade.logic_handler.create_in_memory_layers.return_value = ("points", None)
    config = OrbitalConfig(start_datetime=START, save_data=False)
    assert facade.process_in_memory_track(config) == ("points", None)
    assert config.save_data_path == ""


@pytest.mark.unit
def test_api_response_for_wrong_norad_id_is_rejected_before_saving(tmp_path):
    retriever = Mock()
    retriever.retrieve_data.return_value = (TLE_LINE1, TLE_LINE2, 51.6386)
    facade = OrbitalTrackFacade(retriever)
    facade.logic_handler = Mock()
    config = OrbitalConfig(
        sat_id=40000, start_datetime=START, data_format="TLE",
        save_data=True, save_data_path=str(tmp_path / "wrong.tle"),
    )
    with pytest.raises(ValueError, match="requested ID 40000"):
        facade.process_in_memory_track(config)
    facade.logic_handler.create_in_memory_layers.assert_not_called()
    assert list(tmp_path.iterdir()) == []
