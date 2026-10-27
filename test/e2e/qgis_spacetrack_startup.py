"""QGIS --code scenario for SpaceTrack search, selection, export and custom query."""
import gc
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

from qgis.PyQt.QtCore import QPoint, Qt, QTimer
from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtWidgets import QApplication, QDialogButtonBox, QMessageBox
from qgis.core import QgsProject


def click(widget):
    pos = QPoint(16, widget.height() // 2) if widget.inherits("QCheckBox") else widget.rect().center()
    QTest.mouseClick(widget, Qt.LeftButton, pos=pos)
    QApplication.processEvents()


def run():
    output_dir = Path(os.environ["SPACETRACE_E2E_DIR"])
    mode = os.environ["SPACETRACE_E2E_MODE"]
    sys.path.insert(0, os.environ["SPACETRACE_REPO_ROOT"])
    report = {"ok": False, "scenarios": []}
    login = password = ""
    messages = []
    try:
        if mode == "live":
            from test.live_credentials import load_credentials
            login, password = load_credentials()
        else:
            login, password = "test@example.invalid", "fake-password"

        import qgis.utils

        if "SpaceTrace" not in qgis.utils.plugins:
            assert qgis.utils.loadPlugin("SpaceTrace")
            assert qgis.utils.startPlugin("SpaceTrace")
        plugin = qgis.utils.plugins["SpaceTrace"]

        if mode == "mock-api":
            from SpaceTrace.src.data_retriver import spacetrack_retriver
            from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog

            line1, line2 = (output_dir / "iss.txt").read_text(encoding="ascii").splitlines()[:2]
            record = {"TLE_LINE1": line1, "TLE_LINE2": line2, "INCLINATION": 51.6386}

            def with_norad(line, sat_id):
                prefix = line[:2] + f"{sat_id:05d}" + line[7:-1]
                checksum = sum(int(char) if char.isdigit() else char == "-"
                               for char in prefix) % 10
                return prefix + str(checksum)

            class FakeClient:
                fail_next_search = False
                fail_id = None

                def __init__(self, *args):
                    pass

                def search_by_norad_id(self, text, limit):
                    if FakeClient.fail_next_search:
                        FakeClient.fail_next_search = False
                        raise TimeoutError("simulated network timeout")
                    if text == "25544-25545":
                        return [
                            {"NORAD_CAT_ID": 25544, "SATNAME": "ISS"},
                            {"NORAD_CAT_ID": 25545, "SATNAME": "OTHER"},
                        ]
                    return [{"NORAD_CAT_ID": 25544, "SATNAME": "ISS"}]

                def search_by_custom_query(self, conditions, limit):
                    assert conditions == [
                        ("NORAD_CAT_ID", "=", "25544"),
                        ("CURRENT", "=", "Y"),
                    ]
                    return [{"NORAD_CAT_ID": 25544, "SATNAME": "ISS"}]

                def get_omm(self, sat_id, start):
                    assert str(sat_id) in {"25544", "25545"}
                    if str(sat_id) == str(FakeClient.fail_id):
                        raise OSError("simulated element download failure")
                    return [{
                        **record,
                        "TLE_LINE1": with_norad(line1, int(sat_id)),
                        "TLE_LINE2": with_norad(line2, int(sat_id)),
                    }]

            spacetrack_retriver.SpacetrackClientWrapper = FakeClient
            spacetrack_dialog.SpacetrackClientWrapper = FakeClient
            spacetrack_dialog.QFileDialog.getSaveFileName = (
                lambda *args, **kwargs: (str(output_dir / "search_omm.json"), "")
            )

        # Avoid a modal warning blocking unattended QGIS when the live API fails.
        QMessageBox.warning = lambda *args: messages.append("warning") or QMessageBox.Ok
        QMessageBox.information = lambda *args: messages.append("information") or QMessageBox.Ok
        QMessageBox.critical = lambda *args: messages.append("critical") or QMessageBox.Ok

        plugin.actions[0].trigger()
        dialog = plugin.dlg
        assert dialog.isVisible()
        dialog.lineEditLogin.setText(login)
        dialog.lineEditPassword.setText(password)

        callback_errors = []

        def search_by_id():
            modal = QApplication.activeModalWidget()
            try:
                assert modal is not None, "SpaceTrack search dialog did not open"
                click(modal.ui.radio_norad)
                modal.ui.line_edit_search.setText("25544")
                click(modal.ui.push_button_search)
                assert modal.ui.table_result.rowCount() == 1, (
                    "No ISS search result", messages, dialog.textEditLog.toPlainText()
                )
                modal.ui.table_result.selectRow(0)
                if mode == "mock-api":
                    modal.ui.combo_save_format.setCurrentText("OMM")
                    click(modal.ui.push_button_save)
                    assert (output_dir / "search_omm.json").exists()
                click(modal.ui.button_box.button(QDialogButtonBox.Ok))
            except Exception:
                callback_errors.append(traceback.format_exc())
                if modal is not None:
                    modal.reject()

        QTimer.singleShot(0, search_by_id)
        click(dialog.pushButtonSearchSatellites)
        assert not callback_errors, callback_errors
        assert dialog.lineEditSatID.text() == "25544", (dialog.lineEditSatID.text(), messages)
        report["scenarios"].append({"id": "E2E-03", "selected": "25544"})

        dialog.comboBoxDataFormatSpaceTrack.setCurrentText("OMM")
        dialog.dateTimeEdit.setDateTime(datetime.now())
        dialog.spinBoxDuration.setValue(0.5)
        dialog.spinBoxStepMinutes.setValue(10)
        dialog.lineEditOutputPath.setText(str(output_dir / "api_track.gpkg"))
        click(dialog.checkBoxSaveData)
        dialog.lineEditSaveDataPath.setText(str(output_dir))
        click(dialog.pushButtonExecute)
        layers = list(QgsProject.instance().mapLayers().values())
        counts = sorted(layer.featureCount() for layer in layers)
        assert len(layers) == 2 and 4 in counts, (counts, dialog.textEditLog.toPlainText(), messages)
        assert (output_dir / "25544_omm.json").exists()
        report["scenarios"].append({"id": "E2E-04", "layers": counts})
        del layers

        if mode == "mock-api":
            dialog.tabWidget.setCurrentWidget(dialog.tabMain)

            def custom_search():
                modal = QApplication.activeModalWidget()
                try:
                    assert modal is not None

                    def fill_custom():
                        custom = QApplication.activeModalWidget()
                        try:
                            assert custom is not None and custom is not modal
                            click(custom.ui.button_add)
                            custom.ui.table.cellWidget(0, 1).setCurrentText("NORAD_CAT_ID")
                            custom.ui.table.cellWidget(0, 3).setText("25544")
                            click(custom.ui.button_add)
                            custom.ui.table.cellWidget(1, 1).setCurrentText("CURRENT")
                            custom.ui.table.cellWidget(1, 3).setText("Y")
                            click(custom.ui.button_search)
                        except Exception:
                            callback_errors.append(traceback.format_exc())
                            if custom is not None:
                                custom.reject()

                    QTimer.singleShot(0, fill_custom)
                    click(modal.ui.push_button_custom)
                    assert modal.ui.table_result.rowCount() == 1
                    modal.ui.table_result.selectRow(0)
                    click(modal.ui.button_box.button(QDialogButtonBox.Ok))
                except Exception:
                    callback_errors.append(traceback.format_exc())
                    if modal is not None:
                        modal.reject()

            QTimer.singleShot(0, custom_search)
            click(dialog.pushButtonSearchSatellites)
            assert not callback_errors, callback_errors
            assert dialog.lineEditSatID.text() == "25544"
            report["scenarios"].append({"id": "E2E-05", "custom_query": True})

            def retry_and_multi_select():
                modal = QApplication.activeModalWidget()
                try:
                    assert modal is not None
                    click(modal.ui.radio_norad)
                    modal.ui.line_edit_search.setText("25544-25545")
                    FakeClient.fail_next_search = True
                    click(modal.ui.push_button_search)
                    assert modal.ui.table_result.rowCount() == 0
                    click(modal.ui.push_button_search)
                    assert modal.ui.table_result.rowCount() == 2
                    modal.ui.table_result.selectAll()
                    click(modal.ui.button_box.button(QDialogButtonBox.Ok))
                except Exception:
                    callback_errors.append(traceback.format_exc())
                    if modal is not None:
                        modal.reject()

            QTimer.singleShot(0, retry_and_multi_select)
            click(dialog.pushButtonSearchSatellites)
            assert not callback_errors, callback_errors
            assert dialog.lineEditSatID.text() == "25544-25545"
            report["scenarios"].append({"id": "E2E-08", "retry_and_multi_select": True})

            QgsProject.instance().clear()
            dialog.tabWidget.setCurrentWidget(dialog.tabMain)
            click(dialog.checkBoxSaveData)
            dialog.lineEditOutputPath.setText(f"{output_dir}|gpkg")
            click(dialog.pushButtonExecute)
            counts = sorted(layer.featureCount() for layer in QgsProject.instance().mapLayers().values())
            assert len(counts) == 4 and counts.count(4) == 2 and all(
                count > 0 for count in counts
            ), (counts, "\n".join(dialog.textEditLog.toPlainText().splitlines()[-18:]))
            report["scenarios"].append({"id": "E2E-09", "layers": counts})

            QgsProject.instance().clear()
            dialog.tabWidget.setCurrentWidget(dialog.tabMain)
            dialog.lineEditOutputPath.clear()
            FakeClient.fail_id = 25545
            click(dialog.pushButtonExecute)
            FakeClient.fail_id = None
            counts = sorted(layer.featureCount() for layer in QgsProject.instance().mapLayers().values())
            assert len(counts) == 2 and 4 in counts, (
                counts, "\n".join(dialog.textEditLog.toPlainText().splitlines()[-18:])
            )
            assert "1/2 satellites processed" in dialog.textEditLog.toPlainText()
            report["scenarios"].append({"id": "E2E-15", "partial_api_batch": True})

            spacetrack_dialog.QFileDialog.getSaveFileName = lambda *a, **k: ("", "")

            def cancel_save():
                modal = QApplication.activeModalWidget()
                try:
                    assert modal is not None
                    click(modal.ui.radio_norad)
                    modal.ui.line_edit_search.setText("25544")
                    click(modal.ui.push_button_search)
                    modal.ui.table_result.selectRow(0)
                    click(modal.ui.push_button_save)
                    click(modal.ui.button_box.button(QDialogButtonBox.Cancel))
                except Exception:
                    callback_errors.append(traceback.format_exc())
                    if modal is not None:
                        modal.reject()

            dialog.tabWidget.setCurrentWidget(dialog.tabMain)
            QTimer.singleShot(0, cancel_save)
            click(dialog.pushButtonSearchSatellites)
            assert not callback_errors, callback_errors
            assert dialog.lineEditSatID.text() == "25544-25545"
            report["scenarios"].append({"id": "E2E-12", "cancel_keeps_selection": True})

            QgsProject.instance().clear()
            assert not QgsProject.instance().mapLayers()
            dialog.tabWidget.setCurrentWidget(dialog.tabMain)
            dialog.raise_()
            dialog.activateWindow()
            QApplication.processEvents()
            click(dialog.checkBoxSaveData)
            assert dialog.checkBoxSaveData.isChecked()
            dialog.lineEditSaveDataPath.setText(str(output_dir / "missing" / "bad.json"))
            click(dialog.radioLocalFile)
            assert dialog.radioLocalFile.isChecked()
            dialog.lineEditDataPath.setText(str(output_dir / "iss.txt"))
            dialog.lineEditOutputPath.clear()
            click(dialog.pushButtonExecute)
            assert "Processing file:" in dialog.textEditLog.toPlainText()
            counts = sorted(layer.featureCount() for layer in QgsProject.instance().mapLayers().values())
            assert len(counts) == 2 and 4 in counts, (
                counts, dialog.get_inputs()["data_file_paths"],
                "\n".join(dialog.textEditLog.toPlainText().splitlines()[-18:])
            )
            report["scenarios"].append({"id": "E2E-13", "local_after_api": True})

        click(dialog.pushButtonClose)
        report["ok"] = True
    except Exception:
        error = traceback.format_exc()
        if password:
            error = error.replace(password, "<password>")
        if login:
            error = error.replace(login, "<login>")
        report["error"] = error
    finally:
        QgsProject.instance().clear()
        gc.collect()
        (output_dir / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        QTimer.singleShot(0, QApplication.quit)


QTimer.singleShot(0, run)
