"""Widget-level UI tests: real Qt clicks, mocked file dialogs and API only."""
from unittest.mock import Mock
from pathlib import Path
import pytest
from qgis.PyQt.QtCore import Qt, QTimer, QUrl
from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtWidgets import QApplication, QComboBox, QDialog, QDialogButtonBox
from SpaceTrace.src.Space_trace.Space_trace_dialog import SpaceTracePluginDialog
from SpaceTrace.src.spacetrack_dialog.custom_query_dialog import CustomQueryDialog
from SpaceTrace.src.spacetrack_dialog.custom_query_dialog import field_types
from test.conftest import START

def click(widget):
    QTest.mouseClick(widget, Qt.LeftButton)

@pytest.fixture
def main_dialog(qgis_app):
    dialog = SpaceTracePluginDialog()
    dialog.show()
    qgis_app.processEvents()
    yield dialog
    dialog.close()

@pytest.mark.ui
def test_main_source_and_duration_buttons(main_dialog):
    d = main_dialog
    assert d.radioSpaceTrack.isChecked()
    click(d.radioLocalFile)
    assert d.groupBoxLocalFile.isVisible()
    assert not d.groupBoxSpaceTrack.isVisible()
    click(d.quickButton_1_hour)
    assert d.spinBoxDuration.value() == 1
    click(d.quickButton_1_day)
    assert d.spinBoxDuration.value() == 24
    click(d.quickButton_1_week)
    assert d.spinBoxDuration.value() == 168
    click(d.radioSpaceTrack)
    assert d.groupBoxSpaceTrack.isVisible()
    assert not d.groupBoxLocalFile.isVisible()

@pytest.mark.ui
def test_help_tab_and_external_link(main_dialog, monkeypatch):
    import webbrowser
    opened = []
    monkeypatch.setattr(webbrowser, "open", opened.append)
    d = main_dialog
    index = d.tabWidget.indexOf(d.tabHelp)
    bar = d.tabWidget.tabBar()
    QTest.mouseClick(bar, Qt.LeftButton, pos=bar.tabRect(index).center())
    assert d.tabWidget.currentWidget() is d.tabHelp
    assert d.textBrowserHelp.toPlainText().strip()
    d.textBrowserHelp.anchorClicked.emit(QUrl("https://example.org/help"))
    assert opened == ["https://example.org/help"]

@pytest.mark.ui
def test_main_file_browse_and_input_switch(main_dialog, monkeypatch, tmp_path):
    from SpaceTrace.src.Space_trace import Space_trace_dialog as module
    d = main_dialog
    click(d.radioLocalFile)
    monkeypatch.setattr(module.QFileDialog, "getOpenFileNames",
                        lambda *a, **k: ([str(tmp_path / "a.txt"), str(tmp_path / "b.txt")], ""))
    click(d.pushButtonBrowseData)
    assert d.get_inputs()["data_file_paths"] == [str(tmp_path / "a.txt"), str(tmp_path / "b.txt")]
    click(d.radioSpaceTrack)
    assert d.get_inputs()["data_file_paths"] == []

@pytest.mark.ui
def test_main_output_browse_single_and_multiple(main_dialog, monkeypatch, tmp_path):
    from SpaceTrace.src.Space_trace import Space_trace_dialog as module
    d = main_dialog
    click(d.radioLocalFile)
    d.lineEditDataPath.setText("one.txt")
    monkeypatch.setattr(module.QFileDialog, "getSaveFileName",
                        lambda *a, **k: (str(tmp_path / "one.gpkg"), ""))
    click(d.pushButtonBrowseOutput)
    assert d.lineEditOutputPath.text().endswith("one.gpkg")
    d.lineEditDataPath.setText("one.txt;two.txt")
    monkeypatch.setattr(module.QFileDialog, "getExistingDirectory",
                        lambda *a, **k: str(tmp_path))
    monkeypatch.setattr(d, "_show_format_selection_dialog", lambda: "geojson")
    click(d.pushButtonBrowseOutput)
    assert d.lineEditOutputPath.text() == f"{tmp_path}|geojson"

@pytest.mark.ui
def test_output_format_modal_ok_and_cancel(main_dialog):
    def choose(button, fmt=None):
        modal = QApplication.activeModalWidget()
        assert modal is not None
        if fmt:
            modal.findChild(QComboBox).setCurrentText(fmt)
        click(modal.findChild(QDialogButtonBox).button(button))

    QTimer.singleShot(0, lambda: choose(QDialogButtonBox.Ok, "gpkg"))
    assert main_dialog._show_format_selection_dialog() == "gpkg"
    QTimer.singleShot(0, lambda: choose(QDialogButtonBox.Cancel))
    assert main_dialog._show_format_selection_dialog() == ""

@pytest.mark.ui
def test_main_save_browse_and_checks(main_dialog, monkeypatch, tmp_path):
    from SpaceTrace.src.Space_trace import Space_trace_dialog as module
    d = main_dialog
    assert not d.pushButtonBrowseSaveData.isEnabled()
    click(d.checkBoxSaveData)
    assert d.pushButtonBrowseSaveData.isEnabled()
    monkeypatch.setattr(module.QFileDialog, "getExistingDirectory",
                        lambda *a, **k: str(tmp_path))
    click(d.pushButtonBrowseSaveData)
    assert d.lineEditSaveDataPath.text() == str(tmp_path)
    click(d.checkBoxCreateLineLayer)
    click(d.checkBoxAddLayer)
    inputs = d.get_inputs()
    assert inputs["save_data"] and not inputs["create_line_layer"] and not inputs["add_layer"]
    click(d.checkBoxSaveData)
    assert not d.pushButtonBrowseSaveData.isEnabled()
    assert d.get_inputs()["save_data_path"] == ""

@pytest.mark.ui
def test_search_satellites_requires_credentials(main_dialog, monkeypatch):
    from SpaceTrace.src.Space_trace import Space_trace_dialog as module
    warning = Mock()
    monkeypatch.setattr(module.QtWidgets.QMessageBox, "warning", warning)
    click(main_dialog.pushButtonSearchSatellites)
    warning.assert_called_once()

@pytest.mark.ui
def test_search_satellites_returns_selected_ids(main_dialog, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module
    fake = Mock()
    fake.exec_.return_value = QDialog.Accepted
    fake.get_selected_norad_ids.return_value = ["3", "1", "2"]
    monkeypatch.setattr(module, "SpaceTrackDialog", lambda *a, **k: fake)
    d = main_dialog
    d.lineEditLogin.setText("test@example.org")
    d.lineEditPassword.setText("secret")
    click(d.pushButtonSearchSatellites)
    assert d.lineEditSatID.text() == "1-3"

@pytest.mark.ui
def test_plugin_execute_and_close_buttons(plugin, qgis_app, monkeypatch, tle_file):
    from qgis.core import QgsProject
    plugin.run()
    d = plugin.dlg
    click(d.radioLocalFile)
    d.lineEditDataPath.setText(str(tle_file))
    d.dateTimeEdit.setDateTime(START)
    click(d.quickButton_1_hour)
    d.spinBoxStepMinutes.setValue(10)
    click(d.checkBoxCreateLineLayer)
    click(d.pushButtonExecute)
    assert d.tabWidget.currentWidget() is d.tabLog
    layers = list(QgsProject.instance().mapLayers().values())
    assert len(layers) == 1
    assert layers[0].featureCount() == 7
    click(d.pushButtonClose)
    assert not d.isVisible()

@pytest.mark.ui
def test_execute_multiple_local_files_to_folder(plugin, qgis_app, tle_file, tmp_path):
    from qgis.core import QgsProject
    other = tmp_path / "other.txt"
    other.write_text(tle_file.read_text(), encoding="ascii")
    plugin.run()
    d = plugin.dlg
    click(d.radioLocalFile)
    d.lineEditDataPath.setText(f"{tle_file};{other}")
    d.dateTimeEdit.setDateTime(START)
    d.spinBoxDuration.setValue(1)
    d.spinBoxStepMinutes.setValue(10)
    d.lineEditOutputPath.setText(f"{tmp_path}|gpkg")
    click(d.pushButtonExecute)
    layers = list(QgsProject.instance().mapLayers().values())
    assert len(layers) == 4
    assert sorted(layer.featureCount() for layer in layers) == [2, 2, 7, 7]

@pytest.mark.ui
@pytest.mark.parametrize("data_format", ["TLE", "OMM"])
def test_execute_api_with_fake_client(plugin, qgis_app, monkeypatch, tmp_path, data_format):
    from qgis.core import QgsProject
    from SpaceTrace.src.data_retriver import spacetrack_retriver as module
    from test.conftest import TLE_LINE1, TLE_LINE2
    client = Mock()
    client.get_tle.return_value = (TLE_LINE1, TLE_LINE2, 51.6386)
    client.get_omm.return_value = [{"TLE_LINE1": TLE_LINE1, "TLE_LINE2": TLE_LINE2,
                                    "INCLINATION": 51.6386}]
    monkeypatch.setattr(module, "SpacetrackClientWrapper", lambda *a: client)
    plugin.run()
    d = plugin.dlg
    d.lineEditSatID.setText("25544")
    d.lineEditLogin.setText("test@example.org")
    d.lineEditPassword.setText("secret")
    d.comboBoxDataFormatSpaceTrack.setCurrentText(data_format)
    d.dateTimeEdit.setDateTime(START)
    d.spinBoxDuration.setValue(1)
    d.spinBoxStepMinutes.setValue(10)
    d.lineEditOutputPath.setText(str(tmp_path / "api.gpkg"))
    click(d.pushButtonExecute)
    if data_format == "TLE":
        client.get_tle.assert_called_once()
    else:
        client.get_omm.assert_called_once()
    assert sorted(layer.featureCount() for layer in QgsProject.instance().mapLayers().values()) == [2, 7]

@pytest.mark.ui
def test_execute_multiple_api_ids_with_partial_failure(plugin, qgis_app, monkeypatch, tmp_path):
    from qgis.core import QgsProject
    from SpaceTrace.src.data_retriver import spacetrack_retriver as module
    from test.conftest import TLE_LINE1, TLE_LINE2

    client = Mock()

    def get_omm(sat_id, _):
        if sat_id == 40000:
            raise RuntimeError("No orbital data")
        return [{"TLE_LINE1": TLE_LINE1, "TLE_LINE2": TLE_LINE2,
                 "INCLINATION": 51.6386}]

    client.get_omm.side_effect = get_omm
    monkeypatch.setattr(module, "SpacetrackClientWrapper", lambda *args: client)
    plugin.run()
    d = plugin.dlg
    d.lineEditSatID.setText("25544,40000")
    d.lineEditLogin.setText("test@example.org")
    d.lineEditPassword.setText("secret")
    d.comboBoxDataFormatSpaceTrack.setCurrentText("OMM")
    d.dateTimeEdit.setDateTime(START)
    d.spinBoxDuration.setValue(1)
    d.spinBoxStepMinutes.setValue(10)
    d.lineEditOutputPath.setText(f"{tmp_path}|gpkg")
    click(d.pushButtonExecute)
    assert len(QgsProject.instance().mapLayers()) == 2
    assert "1/2 satellites processed" in d.textEditLog.toPlainText()

@pytest.mark.ui
def test_execute_can_create_file_without_adding_layer(plugin, qgis_app, tle_file, tmp_path):
    from qgis.core import QgsProject
    plugin.run()
    d = plugin.dlg
    click(d.radioLocalFile)
    d.lineEditDataPath.setText(str(tle_file))
    d.dateTimeEdit.setDateTime(START)
    d.spinBoxDuration.setValue(1)
    d.spinBoxStepMinutes.setValue(10)
    d.lineEditOutputPath.setText(str(tmp_path / "export.gpkg"))
    click(d.checkBoxAddLayer)
    click(d.pushButtonExecute)
    assert (tmp_path / "export.gpkg").exists()
    assert not QgsProject.instance().mapLayers()

@pytest.mark.ui
def test_execute_invalid_output_reports_error(plugin, qgis_app, tle_file, tmp_path, iface):
    from qgis.core import QgsProject
    plugin.run()
    d = plugin.dlg
    click(d.radioLocalFile)
    d.lineEditDataPath.setText(str(tle_file))
    d.lineEditOutputPath.setText(str(tmp_path / "wrong.csv"))
    click(d.pushButtonExecute)
    assert not QgsProject.instance().mapLayers()
    assert "Unsupported format" in d.textEditLog.toPlainText()
    assert any(call.kwargs.get("level") == 3 for call in iface.messageBar.return_value.pushMessage.call_args_list)

@pytest.mark.ui
def test_execute_continues_after_one_invalid_file(plugin, qgis_app, tle_file, tmp_path):
    from qgis.core import QgsProject
    bad_file = tmp_path / "bad.txt"
    bad_file.write_text("invalid\ninvalid\n", encoding="ascii")
    plugin.run()
    d = plugin.dlg
    click(d.radioLocalFile)
    d.lineEditDataPath.setText(f"{tle_file};{bad_file}")
    d.dateTimeEdit.setDateTime(START)
    d.spinBoxDuration.setValue(1)
    d.spinBoxStepMinutes.setValue(10)
    d.lineEditOutputPath.setText(f"{tmp_path}|gpkg")
    click(d.pushButtonExecute)
    assert len(QgsProject.instance().mapLayers()) == 2
    assert "1/2 files processed" in d.textEditLog.toPlainText()

@pytest.fixture
def search_dialog(qgis_app, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module
    client = Mock()
    client.search_by_name.return_value = [{"NORAD_CAT_ID": 25544, "SATNAME": "ISS"}]
    client.get_active_satellites.return_value = [{"NORAD_CAT_ID": 25544}]
    client.search_by_country.return_value = [{"NORAD_CAT_ID": 25544}]
    client.search_by_norad_id.return_value = [{"NORAD_CAT_ID": 25544}]
    monkeypatch.setattr(module, "SpacetrackClientWrapper", lambda *a: client)
    dialog = module.SpaceTrackDialog(login="test@example.org", password="test")
    dialog.show()
    qgis_app.processEvents()
    yield dialog, client
    dialog.close()

@pytest.mark.ui
@pytest.mark.parametrize("radio,text,method", [
    ("radio_name", "ISS", "search_by_name"),
    ("radio_active", "", "get_active_satellites"),
    ("radio_country", "US", "search_by_country"),
    ("radio_norad", "25544", "search_by_norad_id"),
])
def test_search_modes_click_dispatch(search_dialog, radio, text, method):
    d, client = search_dialog
    click(getattr(d.ui, radio))
    d.ui.line_edit_search.setText(text)
    click(d.ui.push_button_search)
    getattr(client, method).assert_called_once()
    assert d.ui.table_result.rowCount() == 1

@pytest.mark.ui
def test_search_select_accept_save_and_cancel(search_dialog, monkeypatch, tmp_path):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module
    d, client = search_dialog
    d.ui.line_edit_search.setText("ISS")
    click(d.ui.push_button_search)
    d.ui.table_result.selectRow(0)
    d.ui.combo_save_format.setCurrentText("TLE")
    client.get_tle.return_value = ("line1", "line2", 51.6)
    monkeypatch.setattr(module.QFileDialog, "getSaveFileName",
                        lambda *a, **k: (str(tmp_path / "download.txt"), ""))
    monkeypatch.setattr(module.QMessageBox, "information", lambda *a: None)
    click(d.ui.push_button_save)
    assert (tmp_path / "download.txt").read_text().startswith("line1")
    ok = d.ui.button_box.button(QDialogButtonBox.Ok)
    click(ok)
    assert d.result() == QDialog.Accepted
    d.show()
    click(d.ui.button_box.button(QDialogButtonBox.Cancel))
    assert d.result() == QDialog.Rejected

@pytest.mark.ui
def test_search_custom_query_button(search_dialog, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module
    d, client = search_dialog
    fake = Mock()
    fake.exec_.return_value = QDialog.Accepted
    fake.get_saved_conditions.return_value = [("NORAD_CAT_ID", "=", "25544")]
    monkeypatch.setattr(module, "CustomQueryDialog", lambda *a: fake)
    client.search_by_custom_query.return_value = [{"NORAD_CAT_ID": 25544}]
    click(d.ui.push_button_custom)
    client.search_by_custom_query.assert_called_once()
    assert d.ui.table_result.rowCount() == 1

@pytest.mark.ui
def test_search_validation_and_empty_results(search_dialog, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module
    d, client = search_dialog
    warning = Mock()
    info = Mock()
    monkeypatch.setattr(module.QMessageBox, "warning", warning)
    monkeypatch.setattr(module.QMessageBox, "information", info)
    click(d.ui.push_button_search)
    warning.assert_called_once()
    client.search_by_name.assert_not_called()
    client.search_by_name.return_value = []
    d.ui.line_edit_search.setText("UNKNOWN")
    click(d.ui.push_button_search)
    info.assert_called_once()

@pytest.mark.ui
def test_typing_search_criteria_does_not_open_modal_warnings(search_dialog, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module
    d, _ = search_dialog
    warning = Mock()
    monkeypatch.setattr(module.QMessageBox, "warning", warning)
    click(d.ui.radio_country)
    QTest.keyClicks(d.ui.line_edit_search, "US")
    assert not d.ui.error_label.isVisible()
    click(d.ui.radio_norad)
    QTest.keyClicks(d.ui.line_edit_search, "25544,40000")
    assert not d.ui.error_label.isVisible()
    warning.assert_not_called()

@pytest.mark.ui
def test_search_accept_without_selection_warns(search_dialog, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module
    d, _ = search_dialog
    warning = Mock()
    monkeypatch.setattr(module.QMessageBox, "warning", warning)
    click(d.ui.button_box.button(QDialogButtonBox.Ok))
    warning.assert_called_once()
    assert d.isVisible()

@pytest.mark.ui
def test_search_save_multiple_satellites(search_dialog, monkeypatch, tmp_path):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module
    d, client = search_dialog
    client.search_by_name.return_value = [
        {"NORAD_CAT_ID": 25544}, {"NORAD_CAT_ID": 40000}
    ]
    d.ui.line_edit_search.setText("ISS")
    click(d.ui.push_button_search)
    d.ui.table_result.selectAll()
    client.get_tle.return_value = ("line1", "line2", 51.6)
    monkeypatch.setattr(module.QFileDialog, "getExistingDirectory", lambda *a, **k: str(tmp_path))
    monkeypatch.setattr(module.QMessageBox, "information", lambda *a: None)
    d.ui.combo_save_format.setCurrentText("TLE")
    click(d.ui.push_button_save)
    assert (tmp_path / "satellite_25544.txt").exists()
    assert (tmp_path / "satellite_40000.txt").exists()

@pytest.mark.ui
def test_custom_query_add_remove_search_cancel(qgis_app):
    d = CustomQueryDialog()
    d.show()
    qgis_app.processEvents()
    click(d.ui.button_add)
    assert d.ui.table.rowCount() == 1
    field = d.ui.table.cellWidget(0, 1)
    field.setCurrentText("NORAD_CAT_ID")
    d.ui.table.cellWidget(0, 3).setText("25544")
    click(d.ui.button_search)
    assert d.result() == QDialog.Accepted
    assert d.get_saved_conditions() == [("NORAD_CAT_ID", "=", "25544")]
    d.show()
    click(d.ui.button_remove)
    assert d.ui.table.rowCount() == 0
    click(d.ui.button_cancel)
    assert d.result() == QDialog.Rejected

@pytest.mark.ui
def test_custom_query_rejects_invalid_value(qgis_app, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import custom_query_dialog as module
    warning = Mock()
    monkeypatch.setattr(module.QMessageBox, "warning", warning)
    d = CustomQueryDialog()
    d.show()
    qgis_app.processEvents()
    click(d.ui.button_add)
    d.ui.table.cellWidget(0, 1).setCurrentText("NORAD_CAT_ID")
    d.ui.table.cellWidget(0, 3).setText("not-a-number")
    click(d.ui.button_search)
    warning.assert_called_once()
    assert d.result() != QDialog.Accepted
    d.close()

@pytest.mark.ui
def test_custom_query_null_operator_and_row_removal(qgis_app):
    d = CustomQueryDialog()
    d.show()
    qgis_app.processEvents()
    click(d.ui.button_add)
    click(d.ui.button_add)
    d.ui.table.selectRow(0)
    click(d.ui.button_remove)
    assert d.ui.table.rowCount() == 1
    # The remaining field widget moved from row 1 to row 0.
    d.ui.table.cellWidget(0, 1).setCurrentText("LAUNCH")
    operator = d.ui.table.cellWidget(0, 2)
    operator.setCurrentText("IS NULL")
    assert not d.ui.table.cellWidget(0, 3).isEnabled()
    assert d.get_conditions() == [("LAUNCH", "IS NULL", None)]
    click(d.ui.button_search)
    assert d.get_saved_conditions() == [("LAUNCH", "IS NULL", None)]


@pytest.mark.ui
def test_local_source_with_empty_path_never_uses_api(plugin, monkeypatch):
    from SpaceTrace.src.data_retriver import spacetrack_retriver

    api = Mock(side_effect=AssertionError("API must not be constructed"))
    monkeypatch.setattr(spacetrack_retriver, "SpaceTrackRetriever", api)
    plugin.run()
    d = plugin.dlg
    click(d.radioLocalFile)
    click(d.pushButtonExecute)
    assert "Select at least one local data file" in d.textEditLog.toPlainText()
    api.assert_not_called()


@pytest.mark.ui
def test_hidden_api_save_data_does_not_block_local_file(plugin, tle_file, tmp_path):
    from qgis.core import QgsProject

    plugin.run()
    d = plugin.dlg
    click(d.checkBoxSaveData)
    d.lineEditSaveDataPath.setText(str(tmp_path / "missing" / "secret.json"))
    click(d.radioLocalFile)
    d.lineEditDataPath.setText(str(tle_file))
    d.dateTimeEdit.setDateTime(START)
    d.spinBoxDuration.setValue(1)
    d.spinBoxStepMinutes.setValue(10)
    click(d.pushButtonExecute)
    assert d.get_inputs()["save_data"] is False
    assert len(QgsProject.instance().mapLayers()) == 2
    assert "1/1 files processed" in d.textEditLog.toPlainText()


@pytest.mark.ui
def test_empty_custom_query_cannot_call_api(search_dialog, qgis_app, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import custom_query_dialog as custom_module
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as search_module

    warning = Mock()
    monkeypatch.setattr(custom_module.QMessageBox, "warning", warning)
    monkeypatch.setattr(search_module.QMessageBox, "warning", warning)
    custom = CustomQueryDialog()
    custom.show()
    qgis_app.processEvents()
    click(custom.ui.button_search)
    assert custom.isVisible()
    warning.assert_called()
    custom.close()

    d, client = search_dialog
    d.perform_custom_search([])
    client.search_by_custom_query.assert_not_called()


@pytest.mark.ui
def test_repeat_search_clears_old_selection(search_dialog, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module

    d, client = search_dialog
    monkeypatch.setattr(module.QMessageBox, "information", Mock())
    warning = Mock()
    monkeypatch.setattr(module.QMessageBox, "warning", warning)
    d.ui.line_edit_search.setText("ISS")
    click(d.ui.push_button_search)
    d.ui.table_result.selectRow(0)
    assert d.get_selected_norad_ids() == ["25544"]
    client.search_by_name.return_value = []
    click(d.ui.push_button_search)
    assert d.get_selected_norad_ids() == []
    click(d.ui.button_box.button(QDialogButtonBox.Ok))
    warning.assert_called()
    assert d.isVisible()


@pytest.mark.ui
def test_partial_save_error_hides_progress_and_names_save_operation(
    search_dialog, monkeypatch, tmp_path
):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module

    d, client = search_dialog
    client.search_by_name.return_value = [
        {"NORAD_CAT_ID": 25544}, {"NORAD_CAT_ID": 40000}
    ]
    d.ui.line_edit_search.setText("ISS")
    click(d.ui.push_button_search)
    d.ui.table_result.selectAll()

    def get_tle(nid, _):
        if nid == "40000":
            raise RuntimeError("download failed")
        return "line1", "line2", 51.6

    client.get_tle.side_effect = get_tle
    monkeypatch.setattr(module.QFileDialog, "getExistingDirectory", lambda *a, **k: str(tmp_path))
    critical = Mock()
    monkeypatch.setattr(module.QMessageBox, "critical", critical)
    d.ui.combo_save_format.setCurrentText("TLE")
    click(d.ui.push_button_save)
    assert (tmp_path / "satellite_25544.txt").exists()
    assert not (tmp_path / "satellite_40000.txt").exists()
    assert not d.ui.progress_bar.isVisible()
    assert "while saving" in critical.call_args.args[2]


@pytest.mark.ui
def test_same_named_local_files_get_distinct_outputs(plugin, tle_file, tmp_path):
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    other = other_dir / tle_file.name
    other.write_text(tle_file.read_text(), encoding="ascii")
    plugin.run()
    d = plugin.dlg
    click(d.radioLocalFile)
    d.lineEditDataPath.setText(f"{tle_file};{other}")
    d.dateTimeEdit.setDateTime(START)
    d.spinBoxDuration.setValue(1)
    d.spinBoxStepMinutes.setValue(10)
    d.lineEditOutputPath.setText(f"{tmp_path}|gpkg")
    click(d.pushButtonExecute)
    assert (tmp_path / "iss_1_points.gpkg").exists()
    assert (tmp_path / "iss_2_points.gpkg").exists()
    assert "2/2 files processed" in d.textEditLog.toPlainText()


@pytest.mark.ui
def test_repeat_execute_refuses_to_overwrite_output(plugin, tle_file, tmp_path):
    plugin.run()
    d = plugin.dlg
    click(d.radioLocalFile)
    d.lineEditDataPath.setText(str(tle_file))
    d.dateTimeEdit.setDateTime(START)
    d.spinBoxDuration.setValue(1)
    d.spinBoxStepMinutes.setValue(10)
    output = tmp_path / "track.gpkg"
    d.lineEditOutputPath.setText(str(output))
    click(d.pushButtonExecute)
    original = output.read_bytes()
    click(d.pushButtonExecute)
    assert output.read_bytes() == original
    assert "Output already exists" in d.textEditLog.toPlainText()
    assert "0/1 files processed" in d.textEditLog.toPlainText()


@pytest.mark.ui
def test_api_error_redacts_credentials(plugin, monkeypatch):
    from SpaceTrace.src.data_retriver import spacetrack_retriver

    client = Mock()
    client.get_tle.side_effect = RuntimeError("login-user and password-value rejected")
    monkeypatch.setattr(spacetrack_retriver, "SpacetrackClientWrapper", lambda *a: client)
    plugin.run()
    d = plugin.dlg
    d.lineEditSatID.setText("25544")
    d.lineEditLogin.setText("login-user")
    d.lineEditPassword.setText("password-value")
    click(d.pushButtonExecute)
    log = d.textEditLog.toPlainText()
    assert "login-user" not in log
    assert "password-value" not in log
    assert "<redacted>" in log
    for handler in plugin.logger.handlers:
        handler.flush()
    file_log = Path(plugin.log_path).read_text(encoding="utf-8")
    assert "login-user" not in file_log
    assert "password-value" not in file_log


@pytest.mark.ui
@pytest.mark.parametrize("radio,text,method", [
    ("radio_name", "ISS", "search_by_name"),
    ("radio_active", "", "get_active_satellites"),
    ("radio_country", "US", "search_by_country"),
    ("radio_norad", "25544", "search_by_norad_id"),
])
@pytest.mark.parametrize("limit", ["1", "5", "10", "25", "50", "100", "500", "1000"])
def test_search_limit_reaches_client(search_dialog, radio, text, method, limit):
    d, client = search_dialog
    click(getattr(d.ui, radio))
    d.ui.line_edit_search.setText(text)
    d.ui.combo_limit.setCurrentText(limit)
    click(d.ui.push_button_search)
    assert getattr(client, method).call_args.args[-1] == int(limit)


@pytest.mark.ui
def test_search_error_clears_selected_id(search_dialog, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module

    d, client = search_dialog
    critical = Mock()
    monkeypatch.setattr(module.QMessageBox, "critical", critical)
    d.ui.line_edit_search.setText("ISS")
    click(d.ui.push_button_search)
    d.ui.table_result.selectRow(0)
    assert d.get_selected_norad_ids() == ["25544"]
    client.search_by_name.side_effect = TimeoutError("network timeout")
    click(d.ui.push_button_search)
    assert d.ui.table_result.rowCount() == 0
    assert d.get_selected_norad_ids() == []
    critical.assert_called_once()


@pytest.mark.ui
def test_search_sort_and_multi_selection_keep_norad_ids(search_dialog):
    d, client = search_dialog
    client.search_by_name.return_value = [
        {"NORAD_CAT_ID": 40000, "SATNAME": "B"},
        {"NORAD_CAT_ID": 25544, "SATNAME": "A"},
        {"NORAD_CAT_ID": 60000, "SATNAME": "C"},
    ]
    d.ui.line_edit_search.setText("SAT")
    click(d.ui.push_button_search)
    d.ui.table_result.sortItems(1, Qt.DescendingOrder)
    table = d.ui.table_result
    first = table.visualItemRect(table.item(0, 0)).center()
    last = table.visualItemRect(table.item(2, 0)).center()
    QTest.mouseClick(table.viewport(), Qt.LeftButton, pos=first)
    QTest.mouseClick(table.viewport(), Qt.LeftButton, Qt.ControlModifier, pos=last)
    assert set(d.get_selected_norad_ids()) == {
        table.item(0, 0).text(), table.item(2, 0).text()
    }


@pytest.mark.ui
def test_search_save_without_selection_or_cancel_never_downloads(
    search_dialog, monkeypatch
):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module

    d, client = search_dialog
    warning = Mock()
    monkeypatch.setattr(module.QMessageBox, "warning", warning)
    click(d.ui.push_button_save)
    warning.assert_called_once()
    d.ui.line_edit_search.setText("ISS")
    click(d.ui.push_button_search)
    d.ui.table_result.selectRow(0)
    monkeypatch.setattr(module.QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))
    click(d.ui.push_button_save)
    client.get_tle.assert_not_called()
    client.get_omm.assert_not_called()


@pytest.mark.ui
@pytest.mark.parametrize("field,value,operators", [
    ("NORAD_CAT_ID", "25544", ["=", "!=", "<", ">"]),
    ("INCLINATION", "90.5", ["=", "!=", "<", ">"]),
    ("LAUNCH", "2025-03-28", ["=", "!=", "<", ">", "IS NULL", "IS NOT NULL"]),
    ("SATNAME", "ISS", ["=", "!=", "LIKE"]),
    ("CURRENT", "Y", ["=", "!="]),
])
def test_custom_query_field_types_and_operators(qgis_app, field, value, operators):
    d = CustomQueryDialog()
    d.show()
    qgis_app.processEvents()
    click(d.ui.button_add)
    d.ui.table.cellWidget(0, 1).setCurrentText(field)
    combo = d.ui.table.cellWidget(0, 2)
    assert [combo.itemText(i) for i in range(combo.count())] == operators
    editor = d.ui.table.cellWidget(0, 3)
    editor.setText(value)
    assert d.get_conditions() == [(field, "=", value)]
    if field == "LAUNCH":
        combo.setCurrentText("IS NOT NULL")
        assert not editor.isEnabled()
        assert d.get_conditions() == [(field, "IS NOT NULL", None)]
    d.close()


@pytest.mark.ui
def test_custom_query_cancel_preserves_confirmed_conditions(qgis_app):
    d = CustomQueryDialog()
    d.set_saved_conditions([("NORAD_CAT_ID", "=", "25544")])
    d.show()
    qgis_app.processEvents()
    d.ui.table.cellWidget(0, 3).setText("40000")
    click(d.ui.button_cancel)
    assert d.get_saved_conditions() == [("NORAD_CAT_ID", "=", "25544")]


@pytest.mark.ui
def test_custom_query_remove_then_cancel_preserves_confirmed_conditions(qgis_app):
    d = CustomQueryDialog()
    original = [("NORAD_CAT_ID", "=", "25544"), ("CURRENT", "=", "Y")]
    d.set_saved_conditions(original)
    d.show()
    qgis_app.processEvents()
    d.ui.table.selectRow(0)
    click(d.ui.button_remove)
    assert d.ui.table.rowCount() == 1
    click(d.ui.button_cancel)
    assert d.get_saved_conditions() == original


@pytest.mark.ui
def test_main_browse_cancellations_preserve_existing_paths(main_dialog, monkeypatch):
    from SpaceTrace.src.Space_trace import Space_trace_dialog as module

    d = main_dialog
    click(d.radioLocalFile)
    d.lineEditDataPath.setText("original.txt")
    d.lineEditOutputPath.setText("original.gpkg")
    monkeypatch.setattr(module.QFileDialog, "getOpenFileNames", lambda *a, **k: ([], ""))
    monkeypatch.setattr(module.QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))
    click(d.pushButtonBrowseData)
    click(d.pushButtonBrowseOutput)
    assert d.lineEditDataPath.text() == "original.txt"
    assert d.lineEditOutputPath.text() == "original.gpkg"
    click(d.radioSpaceTrack)
    click(d.checkBoxSaveData)
    d.lineEditSaveDataPath.setText("original-save")
    monkeypatch.setattr(module.QFileDialog, "getExistingDirectory", lambda *a, **k: "")
    click(d.pushButtonBrowseSaveData)
    assert d.lineEditSaveDataPath.text() == "original-save"


@pytest.mark.ui
@pytest.mark.parametrize("fmt", ["shp", "gpkg", "geojson"])
def test_output_format_modal_all_formats(main_dialog, fmt):
    def choose():
        modal = QApplication.activeModalWidget()
        modal.findChild(QComboBox).setCurrentText(fmt)
        click(modal.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok))

    QTimer.singleShot(0, choose)
    assert main_dialog._show_format_selection_dialog() == fmt


@pytest.mark.ui
def test_main_calendar_value_is_converted_to_utc(main_dialog):
    from qgis.PyQt.QtCore import QDateTime

    local = QDateTime.fromString("2026-01-15T12:00:00", Qt.ISODate)
    main_dialog.dateTimeEdit.setDateTime(local)
    expected = main_dialog.dateTimeEdit.dateTime().toUTC().toPyDateTime().replace(tzinfo=None)
    assert main_dialog.get_inputs()["start_datetime"] == expected


@pytest.mark.ui
@pytest.mark.parametrize("wall_time,expected", [
    ("2025-03-09T01:30:00-05:00", "2025-03-09T06:30:00"),
    ("2025-03-09T03:30:00-04:00", "2025-03-09T07:30:00"),
])
def test_calendar_timezone_conversion_across_dst(main_dialog, wall_time, expected):
    from datetime import datetime
    from qgis.PyQt.QtCore import QDateTime

    qdatetime = QDateTime.fromString(wall_time, Qt.ISODate)
    assert qdatetime.isValid()
    assert main_dialog._to_utc_naive(qdatetime) == datetime.fromisoformat(expected)


@pytest.mark.ui
def test_all_failed_api_batch_has_no_success_message(plugin, monkeypatch):
    from qgis.core import QgsProject
    from SpaceTrace.src.data_retriver import spacetrack_retriver

    client = Mock()
    client.get_tle.side_effect = RuntimeError("no elements")
    monkeypatch.setattr(spacetrack_retriver, "SpacetrackClientWrapper", lambda *a: client)
    plugin.run()
    d = plugin.dlg
    d.lineEditSatID.setText("25544,40000")
    d.lineEditLogin.setText("user@example.invalid")
    d.lineEditPassword.setText("secret")
    click(d.pushButtonExecute)
    assert not QgsProject.instance().mapLayers()
    assert "0/2 satellites processed" in d.textEditLog.toPlainText()
    assert "All 2 satellites processed successfully" not in d.textEditLog.toPlainText()


@pytest.mark.ui
def test_memory_without_add_layer_leaves_project_empty(plugin, tle_file):
    from qgis.core import QgsProject

    plugin.run()
    d = plugin.dlg
    click(d.radioLocalFile)
    d.lineEditDataPath.setText(str(tle_file))
    d.spinBoxDuration.setValue(0.1)
    d.spinBoxStepMinutes.setValue(60)
    click(d.checkBoxAddLayer)
    click(d.pushButtonExecute)
    assert not QgsProject.instance().mapLayers()
    assert "1/1 files processed" in d.textEditLog.toPlainText()


@pytest.mark.ui
@pytest.mark.parametrize("radio,text", [
    ("radio_name", ""), ("radio_name", "A"),
    ("radio_country", "U"), ("radio_country", "USA"),
    ("radio_country", "U1"), ("radio_norad", "1,,2"),
    ("radio_norad", "A"), ("radio_norad", ""),
])
def test_invalid_search_criteria_do_not_call_api(search_dialog, monkeypatch, radio, text):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module

    d, client = search_dialog
    warning = Mock()
    monkeypatch.setattr(module.QMessageBox, "warning", warning)
    click(getattr(d.ui, radio))
    d.ui.line_edit_search.setText(text)
    click(d.ui.push_button_search)
    assert warning.called
    assert not client.search_by_name.called
    assert not client.search_by_country.called
    assert not client.search_by_norad_id.called


@pytest.mark.ui
def test_switching_search_mode_clears_text_and_inline_error(search_dialog):
    d, _ = search_dialog
    click(d.ui.radio_country)
    d.ui.line_edit_search.setText("U")
    assert d.ui.error_label.isVisible()
    click(d.ui.radio_norad)
    assert d.ui.line_edit_search.text() == ""
    assert not d.ui.error_label.isVisible()
    assert "NORAD ID" in d.ui.line_edit_search.placeholderText()


@pytest.mark.ui
def test_satcat_partial_records_and_result_limit(search_dialog):
    d, client = search_dialog
    client.search_by_name.return_value = [
        {"NORAD_CAT_ID": 25544, "SATNAME": "ISS", "INCLINATION": "bad"},
        {"NORAD_CAT_ID": 40000, "SATNAME": "OTHER"},
        {"SATNAME": "missing id"},
        "unexpected",
    ]
    d.ui.combo_limit.setCurrentText("1")
    d.ui.line_edit_search.setText("ISS")
    click(d.ui.push_button_search)
    assert d.ui.table_result.rowCount() == 1
    assert d.ui.table_result.item(0, 0).text() == "25544"
    assert d.ui.table_result.item(0, 7).text() == ""
    d.ui.table_result.selectRow(0)
    assert d.get_selected_norad_ids() == ["25544"]


@pytest.mark.ui
@pytest.mark.parametrize("field,kind", list(field_types.items()))
def test_every_custom_filter_field_can_be_selected(qgis_app, field, kind):
    values = {
        "int": "25544", "decimal": "90.5", "date": "2025-03-28",
        "string": "ISS", "enum": "Y",
    }
    d = CustomQueryDialog()
    d.show()
    qgis_app.processEvents()
    click(d.ui.button_add)
    d.ui.table.cellWidget(0, 1).setCurrentText(field)
    d.ui.table.cellWidget(0, 3).setText(values[kind])
    assert d.get_conditions() == [(field, "=", values[kind])]
    d.close()


@pytest.mark.ui
@pytest.mark.parametrize("value", ["2025-02-30", "2025-13-01", "wrong"])
def test_custom_query_rejects_bad_dates(qgis_app, monkeypatch, value):
    from SpaceTrace.src.spacetrack_dialog import custom_query_dialog as module

    warning = Mock()
    monkeypatch.setattr(module.QMessageBox, "warning", warning)
    d = CustomQueryDialog()
    d.show()
    qgis_app.processEvents()
    click(d.ui.button_add)
    d.ui.table.cellWidget(0, 1).setCurrentText("LAUNCH")
    d.ui.table.cellWidget(0, 3).setText(value)
    click(d.ui.button_search)
    warning.assert_called_once()
    assert d.isVisible()
    d.close()


@pytest.mark.ui
def test_custom_query_multiple_rows_and_middle_removal(qgis_app):
    d = CustomQueryDialog()
    d.show()
    qgis_app.processEvents()
    for field, value in [
        ("NORAD_CAT_ID", "25544"), ("CURRENT", "Y"), ("SATNAME", "ISS")
    ]:
        click(d.ui.button_add)
        row = d.ui.table.rowCount() - 1
        d.ui.table.cellWidget(row, 1).setCurrentText(field)
        d.ui.table.cellWidget(row, 3).setText(value)
    d.ui.table.selectRow(1)
    click(d.ui.button_remove)
    assert d.get_conditions() == [
        ("NORAD_CAT_ID", "=", "25544"), ("SATNAME", "=", "ISS")
    ]
    click(d.ui.button_search)
    assert d.get_saved_conditions() == [
        ("NORAD_CAT_ID", "=", "25544"), ("SATNAME", "=", "ISS")
    ]


@pytest.mark.ui
def test_save_multiple_omm_files_have_expected_json(search_dialog, monkeypatch, tmp_path):
    import json
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module

    d, client = search_dialog
    client.search_by_name.return_value = [
        {"NORAD_CAT_ID": 25544}, {"NORAD_CAT_ID": 40000}
    ]
    client.get_omm.side_effect = lambda nid, _: [{"NORAD_CAT_ID": int(nid)}]
    monkeypatch.setattr(module.QFileDialog, "getExistingDirectory", lambda *a, **k: str(tmp_path))
    monkeypatch.setattr(module.QMessageBox, "information", Mock())
    d.ui.line_edit_search.setText("ISS")
    click(d.ui.push_button_search)
    d.ui.table_result.selectAll()
    d.ui.combo_save_format.setCurrentText("OMM")
    click(d.ui.push_button_save)
    for nid in (25544, 40000):
        data = json.loads((tmp_path / f"satellite_{nid}.json").read_text())
        assert data == [{"NORAD_CAT_ID": nid}]
    assert not d.ui.progress_bar.isVisible()


@pytest.mark.ui
@pytest.mark.parametrize("error", [
    TimeoutError("timeout"), RuntimeError("HTTP 429"), RuntimeError("HTTP 503"),
    ValueError("invalid JSON"),
])
def test_search_api_errors_leave_dialog_reusable(search_dialog, monkeypatch, error):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module

    d, client = search_dialog
    critical = Mock()
    monkeypatch.setattr(module.QMessageBox, "critical", critical)
    client.search_by_name.side_effect = error
    d.ui.line_edit_search.setText("ISS")
    click(d.ui.push_button_search)
    assert d.ui.table_result.rowCount() == 0
    critical.assert_called_once()
    client.search_by_name.side_effect = None
    click(d.ui.push_button_search)
    assert d.ui.table_result.rowCount() == 1


@pytest.mark.ui
@pytest.mark.parametrize("bad_indexes,expected_successes", [
    ({0}, 2), ({2}, 2), ({0, 1, 2}, 0),
])
def test_three_file_batch_summary(plugin, tle_file, tmp_path, bad_indexes, expected_successes):
    from qgis.core import QgsProject

    paths = []
    for index in range(3):
        path = tmp_path / f"file_{index}.txt"
        path.write_text(
            "bad\nbad\n" if index in bad_indexes else tle_file.read_text(encoding="ascii"),
            encoding="ascii",
        )
        paths.append(path)
    plugin.run()
    d = plugin.dlg
    click(d.radioLocalFile)
    d.lineEditDataPath.setText(";".join(map(str, paths)))
    d.dateTimeEdit.setDateTime(START)
    d.spinBoxDuration.setValue(1)
    d.spinBoxStepMinutes.setValue(10)
    d.lineEditOutputPath.setText(f"{tmp_path}|gpkg")
    click(d.pushButtonExecute)
    assert f"{expected_successes}/3 files processed" in d.textEditLog.toPlainText()
    assert len(QgsProject.instance().mapLayers()) == expected_successes * 2


@pytest.mark.ui
def test_api_batch_saves_omm_with_json_extension(plugin, monkeypatch, tmp_path):
    import json
    from SpaceTrace.src.data_retriver import spacetrack_retriver
    from test.conftest import TLE_LINE1, TLE_LINE2

    client = Mock()
    def with_norad(line, sat_id):
        prefix = line[:2] + f"{sat_id:05d}" + line[7:-1]
        checksum = sum(int(char) if char.isdigit() else char == "-"
                       for char in prefix) % 10
        return prefix + str(checksum)

    def get_omm(sat_id, _):
        return [{
            "TLE_LINE1": with_norad(TLE_LINE1, sat_id),
            "TLE_LINE2": with_norad(TLE_LINE2, sat_id),
            "INCLINATION": 51.6386,
        }]

    client.get_omm.side_effect = get_omm
    monkeypatch.setattr(spacetrack_retriver, "SpacetrackClientWrapper", lambda *a: client)
    plugin.run()
    d = plugin.dlg
    d.lineEditSatID.setText("25544,25545")
    d.lineEditLogin.setText("user@example.invalid")
    d.lineEditPassword.setText("secret")
    d.comboBoxDataFormatSpaceTrack.setCurrentText("OMM")
    d.dateTimeEdit.setDateTime(START)
    d.spinBoxDuration.setValue(0.1)
    d.spinBoxStepMinutes.setValue(60)
    click(d.checkBoxSaveData)
    d.lineEditSaveDataPath.setText(str(tmp_path))
    click(d.pushButtonExecute)
    assert "2/2 satellites processed" in d.textEditLog.toPlainText()
    for nid in (25544, 25545):
        path = tmp_path / f"{nid}_omm.json"
        assert json.loads(path.read_text()) == get_omm(nid, None)


@pytest.mark.ui
def test_authentication_error_is_distinct_from_validation(search_dialog, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module

    class AuthenticationError(Exception):
        pass

    d, client = search_dialog
    critical = Mock()
    monkeypatch.setattr(module.QMessageBox, "critical", critical)
    client.search_by_name.side_effect = AuthenticationError()
    d.ui.line_edit_search.setText("ISS")
    click(d.ui.push_button_search)
    assert "authentication failed" in critical.call_args.args[2].lower()
    assert d.ui.table_result.rowCount() == 0


@pytest.mark.ui
def test_execute_requires_save_data_path_before_api_request(plugin, monkeypatch):
    from SpaceTrace.src.data_retriver import spacetrack_retriver

    client_factory = Mock()
    monkeypatch.setattr(spacetrack_retriver, "SpacetrackClientWrapper", client_factory)
    plugin.run()
    d = plugin.dlg
    d.lineEditSatID.setText("25544")
    d.lineEditLogin.setText("user@example.invalid")
    d.lineEditPassword.setText("secret")
    click(d.checkBoxSaveData)
    click(d.pushButtonExecute)
    assert "Choose a path to save" in d.textEditLog.toPlainText()
    client_factory.assert_not_called()


@pytest.mark.ui
def test_country_search_normalizes_lowercase_input(search_dialog):
    d, client = search_dialog
    click(d.ui.radio_country)
    d.ui.line_edit_search.setText("us")
    click(d.ui.push_button_search)
    client.search_by_country.assert_called_once_with("US", 10)


@pytest.mark.ui
def test_custom_query_empty_or_error_result_is_not_selectable(search_dialog, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module

    d, client = search_dialog
    client.search_by_custom_query.return_value = []
    d.perform_custom_search([("NORAD_CAT_ID", "=", "99999")])
    assert d.ui.table_result.rowCount() == 0
    assert d.get_selected_norad_ids() == []
    critical = Mock()
    monkeypatch.setattr(module.QMessageBox, "critical", critical)
    client.search_by_custom_query.side_effect = RuntimeError("HTTP 503")
    d.perform_custom_search([("NORAD_CAT_ID", "=", "25544")])
    assert d.ui.table_result.rowCount() == 0
    critical.assert_called_once()


@pytest.mark.ui
def test_all_failed_omm_save_reports_error_and_resets_progress(
    search_dialog, monkeypatch, tmp_path
):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module

    d, client = search_dialog
    d.ui.line_edit_search.setText("ISS")
    click(d.ui.push_button_search)
    d.ui.table_result.selectRow(0)
    d.ui.combo_save_format.setCurrentText("OMM")
    client.get_omm.side_effect = OSError("write failed")
    monkeypatch.setattr(module.QFileDialog, "getSaveFileName",
                        lambda *a, **k: (str(tmp_path / "bad.json"), ""))
    critical = Mock()
    monkeypatch.setattr(module.QMessageBox, "critical", critical)
    click(d.ui.push_button_save)
    assert not (tmp_path / "bad.json").exists()
    assert not d.ui.progress_bar.isVisible()
    assert "while saving" in critical.call_args.args[2]


@pytest.mark.ui
def test_spacetrack_error_log_redacts_login_and_password(search_dialog, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import spacetrack_dialog as module

    d, client = search_dialog
    logs = []
    d.log_callback = logs.append
    client.search_by_name.side_effect = RuntimeError("test@example.org and test rejected")
    monkeypatch.setattr(module.QMessageBox, "critical", Mock())
    d.ui.line_edit_search.setText("ISS")
    click(d.ui.push_button_search)
    assert logs
    assert all("test@example.org" not in message for message in logs)
    assert all("test rejected" not in message for message in logs)
    assert any("<redacted>" in message for message in logs)


@pytest.mark.ui
def test_custom_query_rejects_nonfinite_decimal(qgis_app, monkeypatch):
    from SpaceTrace.src.spacetrack_dialog import custom_query_dialog as module

    warning = Mock()
    monkeypatch.setattr(module.QMessageBox, "warning", warning)
    d = CustomQueryDialog()
    d.show()
    qgis_app.processEvents()
    click(d.ui.button_add)
    d.ui.table.cellWidget(0, 1).setCurrentText("INCLINATION")
    d.ui.table.cellWidget(0, 3).setText("nan")
    click(d.ui.button_search)
    assert d.isVisible()
    warning.assert_called_once()
    d.close()
