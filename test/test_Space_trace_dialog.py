import pytest

@pytest.mark.unit
@pytest.mark.parametrize("text,expected", [
    ("25544", [25544]), ("3, 1-2, 2", [1, 2, 3]), ("5-3", ValueError),
])
def test_norad_parser(plugin, text, expected):
    if expected is ValueError:
        with pytest.raises(ValueError):
            plugin._parse_norad_ids(text)
    else:
        assert plugin._parse_norad_ids(text) == expected


@pytest.mark.unit
@pytest.mark.parametrize("text", ["0", "-1", "1,,2", "1-1002", "3-2", "1-2-3"])
def test_norad_parser_rejects_invalid_or_oversized_batches(plugin, text):
    with pytest.raises(ValueError):
        plugin._parse_norad_ids(text)

@pytest.mark.unit
def test_plugin_action_lifecycle(plugin, iface):
    plugin.initGui()
    assert len(plugin.actions) == 1
    assert plugin.actions[0].isEnabled()
    plugin.unload()
    iface.removeToolBarIcon.assert_called_once_with(plugin.actions[0])
    iface.removePluginVectorMenu.assert_called_once()

@pytest.mark.unit
def test_output_validation(plugin, tmp_path):
    output = str(tmp_path / "track.gpkg")
    assert plugin._validate_output_path(output, 1) == (output, "gpkg")
    assert plugin._validate_output_path(f"{tmp_path}|geojson", 2) == (str(tmp_path), "geojson")
    with pytest.raises(Exception, match="Unsupported"):
        plugin._validate_output_path(str(tmp_path / "track.csv"), 1)


@pytest.mark.unit
def test_output_and_raw_data_paths_must_be_writable(plugin, tmp_path, monkeypatch):
    with pytest.raises(Exception, match="Choose a path"):
        plugin._validate_save_data_path("", True, 1)
    with pytest.raises(Exception, match="does not exist"):
        plugin._validate_save_data_path(str(tmp_path / "missing" / "raw.json"), True, 1)

    from SpaceTrace.src.Space_trace import Space_trace as module
    monkeypatch.setattr(module.os, "access", lambda path, mode: False)
    with pytest.raises(Exception, match="not writable"):
        plugin._validate_output_path(str(tmp_path / "track.gpkg"), 1)
    with pytest.raises(Exception, match="not writable"):
        plugin._validate_save_data_path(str(tmp_path / "raw.json"), True, 1)

@pytest.mark.unit
def test_validation_rejects_missing_file_and_credentials(plugin, tmp_path):
    base = dict(data_file_paths=[], sat_id_text="25544", login="", password="", output_path="",
                save_data=False, save_data_path="")
    with pytest.raises(Exception, match="login"):
        plugin._validate_inputs(base)
    base["data_file_paths"] = [str(tmp_path / "missing.txt")]
    with pytest.raises(Exception, match="not readable"):
        plugin._validate_inputs(base)

