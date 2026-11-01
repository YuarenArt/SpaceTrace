"""Regression checks for release and CI helper scripts."""

from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import pytest

from scripts.test_qgis_gui import redact
from test.conftest import ROOT


def run_script(script, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *(str(arg) for arg in args)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )


@pytest.mark.unit
def test_plugin_zip_validator_rejects_modified_source(tmp_path):
    built = run_script("build_plugin.py", "--output-dir", tmp_path)
    assert built.returncode == 0, built.stderr
    archive = next(tmp_path.glob("SpaceTrace-*.zip"))
    assert run_script("check_plugin_zip.py", archive).returncode == 0

    replacement = tmp_path / "replacement.zip"
    with ZipFile(archive) as original, ZipFile(replacement, "w") as modified:
        for name in original.namelist():
            data = original.read(name)
            if name == "SpaceTrace/__init__.py":
                data += b"\n# changed\n"
            modified.writestr(name, data)
    archive.unlink()
    replacement.rename(archive)
    result = run_script("check_plugin_zip.py", archive)
    assert result.returncode != 0
    assert "differs from checkout" in result.stderr


@pytest.mark.unit
def test_live_report_redacts_credentials(monkeypatch):
    monkeypatch.setenv("SPACETRACE_LOGIN", "user@example.invalid")
    monkeypatch.setenv("SPACETRACE_PASSWORD", "sample-password")
    result = redact("user@example.invalid: sample-password")
    assert result == "<redacted>: <redacted>"


@pytest.mark.unit
def test_plugin_zip_builder_refuses_to_overwrite(tmp_path):
    assert run_script("build_plugin.py", "--output-dir", tmp_path).returncode == 0
    archive = next(Path(tmp_path).glob("SpaceTrace-*.zip"))
    original = archive.read_bytes()
    assert run_script("build_plugin.py", "--output-dir", tmp_path).returncode != 0
    assert archive.read_bytes() == original
