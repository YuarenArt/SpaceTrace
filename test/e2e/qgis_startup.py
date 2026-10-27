"""Executed by QGIS --code, with paths provided by scripts/test-gui-e2e-windows.ps1."""
import gc
import json
import os
import traceback
from datetime import datetime
from pathlib import Path

from qgis.PyQt.QtCore import Qt, QTimer, QPoint
from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsProject, QgsVectorLayer


def click(widget):
    pos = QPoint(16, widget.height() // 2) if widget.inherits("QCheckBox") else widget.rect().center()
    QTest.mouseClick(widget, Qt.LeftButton, pos=pos)
    QApplication.processEvents()


def run():
    output_dir = Path(os.environ["SPACETRACE_E2E_DIR"])
    report_path = output_dir / "result.json"
    report = {"ok": False, "scenarios": []}
    try:
        import qgis.utils

        if "SpaceTrace" not in qgis.utils.plugins:
            assert qgis.utils.loadPlugin("SpaceTrace"), "Plugin did not load"
            assert qgis.utils.startPlugin("SpaceTrace"), "Plugin did not start"
        plugin = qgis.utils.plugins["SpaceTrace"]
        assert len(plugin.actions) == 1

        # Real QGIS toolbar action, real dialog, real Qt clicks, real processing.
        plugin.actions[0].trigger()
        dialog = plugin.dlg
        assert dialog.isVisible()
        click(dialog.radioLocalFile)
        dialog.lineEditDataPath.setText(str(output_dir / "iss.txt"))
        dialog.dateTimeEdit.setDateTime(datetime(2025, 3, 28, 18))
        click(dialog.quickButton_1_hour)
        dialog.spinBoxStepMinutes.setValue(10)
        dialog.lineEditOutputPath.setText(str(output_dir / "track.gpkg"))
        click(dialog.pushButtonExecute)
        layers = list(QgsProject.instance().mapLayers().values())
        counts = sorted(layer.featureCount() for layer in layers)
        assert len(layers) == 2 and 7 in counts, counts
        report["scenarios"].append({"id": "E2E-01", "layers": counts})
        del layers
        click(dialog.pushButtonClose)
        project_file = output_dir / "saved_project.qgz"
        QgsProject.instance().setFileName(str(project_file))
        assert QgsProject.instance().write()
        QgsProject.instance().clear()
        assert QgsProject.instance().read(str(project_file))
        restored = sorted(layer.featureCount() for layer in QgsProject.instance().mapLayers().values())
        assert restored == counts, restored
        report["scenarios"].append({"id": "E2E-07", "restored_layers": restored})
        QgsProject.instance().clear()

        plugin.actions[0].trigger()
        assert dialog.isVisible()
        dialog.tabWidget.setCurrentWidget(dialog.tabMain)
        QApplication.processEvents()
        dialog.activateWindow()
        QApplication.processEvents()
        dialog.lineEditOutputPath.clear()
        assert dialog.checkBoxCreateLineLayer.isChecked(), (dialog.checkBoxCreateLineLayer.isVisible(), dialog.checkBoxCreateLineLayer.isChecked())
        click(dialog.checkBoxCreateLineLayer)
        assert not dialog.checkBoxCreateLineLayer.isChecked(), ("Line checkbox did not toggle", dialog.checkBoxCreateLineLayer.isVisible(), dialog.checkBoxCreateLineLayer.isEnabled(), dialog.checkBoxCreateLineLayer.rect().getRect())
        click(dialog.pushButtonExecute)
        layers = list(QgsProject.instance().mapLayers().values())
        assert len(layers) == 1 and layers[0].featureCount() == 7, (len(layers), [layer.featureCount() for layer in layers], dialog.textEditLog.toPlainText())
        report["scenarios"].append({"id": "E2E-02", "layers": [7]})
        del layers
        click(dialog.pushButtonClose)
        QgsProject.instance().clear()

        line1, line2 = (output_dir / "iss.txt").read_text(encoding="ascii").splitlines()[:2]
        omm_file = output_dir / "iss.json"
        omm_file.write_text(json.dumps([{
            "TLE_LINE1": line1, "TLE_LINE2": line2, "INCLINATION": 51.6386
        }]), encoding="utf-8")
        plugin.actions[0].trigger()
        dialog.tabWidget.setCurrentWidget(dialog.tabMain)
        QApplication.processEvents()
        dialog.lineEditDataPath.setText(str(omm_file))
        dialog.comboBoxDataFormatLocal.setCurrentText("OMM")
        dialog.lineEditOutputPath.setText(str(output_dir / "omm_track.geojson"))
        click(dialog.checkBoxCreateLineLayer)
        click(dialog.checkBoxAddLayer)
        assert dialog.checkBoxCreateLineLayer.isChecked()
        assert not dialog.checkBoxAddLayer.isChecked()
        click(dialog.pushButtonExecute)
        points = QgsVectorLayer(str(output_dir / "omm_track.geojson"), "points", "ogr")
        assert points.isValid() and points.featureCount() == 7
        assert not QgsProject.instance().mapLayers()
        report["scenarios"].append({"id": "E2E-06", "exported_points": 7})
        del points
        click(dialog.pushButtonClose)

        plugin.actions[0].trigger()
        dialog.tabWidget.setCurrentWidget(dialog.tabMain)
        QApplication.processEvents()
        if not dialog.radioLocalFile.isChecked():
            click(dialog.radioLocalFile)
        dialog.lineEditDataPath.clear()
        dialog.lineEditOutputPath.clear()
        click(dialog.pushButtonExecute)
        assert "Select at least one local data file" in dialog.textEditLog.toPlainText()
        assert not QgsProject.instance().mapLayers()
        report["scenarios"].append({"id": "E2E-10", "empty_local_rejected": True})
        click(dialog.pushButtonClose)

        assert qgis.utils.unloadPlugin("SpaceTrace")
        assert qgis.utils.loadPlugin("SpaceTrace")
        assert qgis.utils.startPlugin("SpaceTrace")
        reloaded = qgis.utils.plugins["SpaceTrace"]
        assert len(reloaded.actions) == 1
        reloaded.actions[0].trigger()
        assert reloaded.dlg.isVisible()
        click(reloaded.dlg.pushButtonClose)
        report["scenarios"].append({"id": "E2E-11", "reload": True})
        report["ok"] = True
    except Exception:
        report["error"] = traceback.format_exc()
    finally:
        QgsProject.instance().clear()
        gc.collect()
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        QTimer.singleShot(0, QApplication.quit)


QTimer.singleShot(0, run)
