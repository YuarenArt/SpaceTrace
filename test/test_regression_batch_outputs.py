"""Regression tests for output names in multi-file processing."""
import os
from datetime import datetime

import pytest
from qgis.core import QgsVectorLayer

from SpaceTrace.src.Space_trace.orbital.facade import OrbitalTrackFacade
from SpaceTrace.src.data_retriver.data_retriver import LocalFileRetriever


@pytest.mark.integration
def test_duplicate_stems_do_not_collide_with_other_input_names(plugin, tle_file, tmp_path):
    source_dirs = [tmp_path / name for name in ("a", "b", "c")]
    paths = []
    for folder, name in zip(source_dirs, ("foo.txt", "foo.txt", "foo_1.txt")):
        folder.mkdir()
        path = folder / name
        path.write_bytes(tle_file.read_bytes())
        paths.append(str(path))

    output_dir = tmp_path / "output"
    output_dir.mkdir()
    inputs = {
        "data_file_paths": paths, "output_path": str(output_dir), "save_data_path": "",
        "save_data": False, "start_datetime": datetime(2025, 3, 28, 18),
        "duration_hours": 0.1, "step_minutes": 60, "add_layer": False,
        "data_format": "TLE", "create_line_layer": False,
    }
    configs = [plugin._create_config_for_local_file(inputs, i, "gpkg") for i in range(3)]
    names = [os.path.normcase(config.output_path) for config in configs]
    assert len(set(names)) == 3
    assert os.path.basename(configs[2].output_path) == "foo_1_points.gpkg"

    facade = OrbitalTrackFacade(LocalFileRetriever())
    for config in configs:
        point_file, line_file = facade.process_persistent_track(config)
        assert line_file is None
        layer = QgsVectorLayer(point_file, "points", "ogr")
        assert layer.isValid() and layer.featureCount() == 1
        del layer


@pytest.mark.unit
def test_generated_suffixes_avoid_all_original_stems(plugin):
    paths = ["a/foo.txt", "b/foo.txt", "c/foo_1.txt", "d/foo_1_2.txt"]
    names = plugin._local_output_base_names(paths)
    assert len({os.path.normcase(name) for name in names}) == len(paths)
    assert names[2:] == ["foo_1", "foo_1_2"]
