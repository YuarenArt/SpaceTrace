"""Second QGIS process: reopen the project written by qgis_startup.py."""

import json
import os
import traceback
from pathlib import Path

from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsProject


def run():
    output_dir = Path(os.environ["SPACETRACE_E2E_DIR"])
    report = {"ok": False, "scenarios": []}
    try:
        project_file = output_dir / "saved_project.qgz"
        assert project_file.exists()
        assert QgsProject.instance().read(str(project_file))
        layers = list(QgsProject.instance().mapLayers().values())
        counts = sorted(layer.featureCount() for layer in layers)
        assert len(layers) == 2 and 7 in counts, counts
        assert all(layer.isValid() for layer in layers)
        report["scenarios"].append({"id": "E2E-14", "reopened_layers": counts})
        report["ok"] = True
    except Exception:
        report["error"] = traceback.format_exc()
    finally:
        QgsProject.instance().clear()
        (output_dir / "reopen_result.json").write_text(json.dumps(report), encoding="utf-8")
        QTimer.singleShot(0, QApplication.quit)


QTimer.singleShot(0, run)
