from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton, QLabel, QLineEdit,
    QPushButton, QComboBox, QTableWidget, QDialogButtonBox, QFileDialog, QDialog
)
from datetime import datetime, timezone
import json
import os

from ..spacetrack_client.spacetrack_client import SpacetrackClientWrapper
from .custom_query_dialog import CustomQueryDialog


class Ui_SpaceTrackDialog:
    """UI setup for the SpaceTrack dialog interface."""

    def setup_ui(self, dialog: QDialog) -> None:
        dialog.resize(900, 500)
        self._create_main_layout(dialog)
        self._create_search_type_group(dialog)
        self._create_search_inputs(dialog)
        self._create_limit_selector(dialog)
        self._create_results_table(dialog)
        self._create_save_controls(dialog)
        self._create_progress_bar(dialog)
        self._create_bottom_buttons(dialog)

    def retranslate_ui(self, dialog: QDialog) -> None:
        _translate = QtCore.QCoreApplication.translate
        dialog.setWindowTitle(_translate("SpaceTrackDialog", "SpaceTrack Search"))
        self.group_box.setTitle(_translate("SpaceTrackDialog", "Search Type"))
        self.radio_name.setText(_translate("SpaceTrackDialog", "By Name"))
        self.radio_active.setText(_translate("SpaceTrackDialog", "All Active"))
        self.radio_country.setText(_translate("SpaceTrackDialog", "By Country"))
        self.radio_norad.setText(_translate("SpaceTrackDialog", "By NORAD ID"))
        self.label_search.setText(_translate("SpaceTrackDialog", "Search Criteria:"))
        self.line_edit_search.setPlaceholderText(_translate(
            "SpaceTrackDialog",
            "Enter name, country code (e.g., US), NORAD ID (e.g., 25544), range (e.g., 25544-25550), or list (e.g., 25544,25545)"
        ))
        self.push_button_search.setText(_translate("SpaceTrackDialog", "Search"))
        self.label_limit.setText(_translate("SpaceTrackDialog", "Result Limit:"))
        self.push_button_custom.setText(_translate("SpaceTrackDialog", "Custom Query"))
        self.label_save_format.setText(_translate("SpaceTrackDialog", "Save Format:"))
        self.push_button_save.setText(_translate("SpaceTrackDialog", "Save Data"))

        headers = [
            "NORAD ID", "Name", "Country", "Launch Date",
            "Eccentricity", "Perigee (km)", "Apogee (km)", "Inclination (°)"
        ]
        self.table_result.setHorizontalHeaderLabels(headers)

    def _create_main_layout(self, dialog: QDialog) -> None:
        self.main_layout = QVBoxLayout(dialog)

    def _create_search_type_group(self, dialog: QDialog) -> None:
        self.group_box = QGroupBox(dialog)
        layout = QHBoxLayout(self.group_box)
        self.radio_name = QRadioButton(self.group_box)
        self.radio_active = QRadioButton(self.group_box)
        self.radio_country = QRadioButton(self.group_box)
        self.radio_norad = QRadioButton(self.group_box)
        for widget in (self.radio_name, self.radio_active, self.radio_country, self.radio_norad):
            layout.addWidget(widget)
        self.main_layout.addWidget(self.group_box)

    def _create_search_inputs(self, dialog: QDialog) -> None:
        self.label_search = QLabel(dialog)
        self.line_edit_search = QLineEdit(dialog)
        self.push_button_search = QPushButton(dialog)
        
        self.main_layout.addWidget(self.label_search)
        self.main_layout.addWidget(self.line_edit_search)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.push_button_search)
        button_layout.addStretch()
        self.main_layout.addLayout(button_layout)

    def _create_limit_selector(self, dialog: QDialog) -> None:
        self.label_limit = QLabel(dialog)
        self.combo_limit = QComboBox(dialog)
        self.combo_limit.addItems(["1", "5", "10", "25", "50", "100", "500", "1000"])
        self.combo_limit.setCurrentText("10")
        layout = QHBoxLayout()
        layout.addWidget(self.label_limit)
        layout.addWidget(self.combo_limit)
        layout.addStretch()
        self.main_layout.addLayout(layout)

    def _create_results_table(self, dialog: QDialog) -> None:
        headers = [
            "NORAD_CAT_ID", "SATNAME", "COUNTRY", "LAUNCH",
            "ECCENTRICITY", "PERIGEE", "APOGEE", "INCLINATION"
        ]
        self.table_result = QTableWidget(dialog)
        self.table_result.setColumnCount(len(headers))
        display_headers = [
            "NORAD ID", "Name", "Country", "Launch Date",
            "Eccentricity", "Perigee (km)", "Apogee (km)", "Inclination (°)"
        ]
        self.table_result.setHorizontalHeaderLabels(display_headers)
        self.table_result.setSelectionMode(QTableWidget.MultiSelection)
        self.table_result.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_result.horizontalHeader().setStretchLastSection(True)
        self.table_result.setSortingEnabled(True)
        self.main_layout.addWidget(self.table_result)

    def _create_save_controls(self, dialog: QDialog) -> None:
        self.label_save_format = QLabel(dialog)
        self.combo_save_format = QComboBox(dialog)
        self.combo_save_format.addItems(["OMM", "TLE"])
        self.push_button_save = QPushButton(dialog)
        layout = QHBoxLayout()
        layout.addWidget(self.label_save_format)
        layout.addWidget(self.combo_save_format)
        layout.addWidget(self.push_button_save)
        layout.addStretch()
        self.main_layout.addLayout(layout)

    def _create_progress_bar(self, dialog: QDialog) -> None:
        self.progress_bar = QtWidgets.QProgressBar(dialog)
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

    def _create_bottom_buttons(self, dialog: QDialog) -> None:
        self.push_button_custom = QPushButton(dialog)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dialog)
        self.main_layout.addWidget(self.push_button_custom, 0, QtCore.Qt.AlignRight)
        self.main_layout.addWidget(self.button_box)


class SpaceTrackDialog(QtWidgets.QDialog):
    """Dialog to search, display, and save satellite data from SpaceTrack API."""

    def __init__(
        self, parent=None, login: str = None,
        password: str = None, log_callback=None, translator=None
    ):
        super().__init__(parent)
        self.translator = translator
        self.log_callback = log_callback
        self.client = SpacetrackClientWrapper(login, password)
        self.selected_ids = []
        self.custom_conds = []

        self.ui = Ui_SpaceTrackDialog()
        self.ui.setup_ui(self)
        self.ui.retranslate_ui(self)
        self._connect_signals()
        self.ui.radio_name.setChecked(True)

    def _connect_signals(self) -> None:
        ui = self.ui
        ui.push_button_search.clicked.connect(self.perform_search)
        ui.push_button_custom.clicked.connect(self.open_custom_query)
        ui.button_box.accepted.connect(self.on_accept)
        ui.button_box.rejected.connect(self.reject)
        ui.table_result.itemSelectionChanged.connect(self.on_selection_changed)
        ui.push_button_save.clicked.connect(self.save_selected_data)

    def perform_search(self) -> None:
        """Search satellites based on selected criteria and display results."""
        self._log("Initiating search...")
        text = self.ui.line_edit_search.text().strip()
        limit = int(self.ui.combo_limit.currentText())
        self.ui.table_result.setRowCount(0)

        try:
            results = self._get_results(text, limit)
            self._display_results(results)
        except Exception as err:
            self._handle_error(f"Search error: {err}")

    def _get_results(self, text: str, limit: int):
        """Dispatch search by current radio selection."""
        ui = self.ui
        match True:
            case _ if ui.radio_name.isChecked():
                self._ensure_text(text, "Please enter a satellite name.")
                return self.client.search_by_name(text, limit)
            case _ if ui.radio_active.isChecked():
                return self.client.get_active_satellites(limit)
            case _ if ui.radio_country.isChecked():
                self._ensure_text(text, "Please enter a country code (e.g., US).")
                return self.client.search_by_country(text, limit)
            case _ if ui.radio_norad.isChecked():
                self._ensure_text(text, "Please enter a NORAD ID, range, or list.")
                return self.client.search_by_norad_id(text, limit)
            case _:
                return []

    def open_custom_query(self) -> None:
        dialog = CustomQueryDialog(self)
        dialog.set_saved_conditions(self.custom_conds)
        if dialog.exec_() == QDialog.Accepted:
            self.custom_conds = dialog.get_saved_conditions()
            self.perform_custom_search(self.custom_conds)

    def perform_custom_search(self, conditions: list) -> None:
        """Run custom conditions query and display results."""
        self._log("Initiating custom query...")
        limit = int(self.ui.combo_limit.currentText())
        self.ui.table_result.setRowCount(0)

        try:
            results = self.client.search_by_custom_query(conditions, limit)
            self._display_results(results)
        except Exception as err:
            self._handle_error(f"Custom query error: {err}")

    def _display_results(self, results: list) -> None:
        """Populate table with search results."""
        if not results:
            self.ui.table_result.setRowCount(1)
            self.ui.table_result.setItem(0, 0, QtWidgets.QTableWidgetItem("No results"))
            self._log("No results found.")
            return
        self._log(f"Found {len(results)} items.")
        for record in results:
            if isinstance(record, dict):
                self._add_row(record)

    def _add_row(self, record: dict) -> None:
        """Insert a single satellite record into the table."""
        row = self.ui.table_result.rowCount()
        self.ui.table_result.insertRow(row)
        for col, key in enumerate([
            "NORAD_CAT_ID", "SATNAME", "COUNTRY", "LAUNCH",
            "ECCENTRICITY", "PERIGEE", "APOGEE", "INCLINATION"
        ]):
            text = self._format_cell(key, record)
            item = QtWidgets.QTableWidgetItem(text)
            if key == "NORAD_CAT_ID" and text.isdigit():
                item.setData(QtCore.Qt.UserRole, int(text))
            self.ui.table_result.setItem(row, col, item)

    def _format_cell(self, key: str, rec: dict) -> str:
        """Format cell value based on its key."""
        val = rec.get(key)
        try:
            if key == "ECCENTRICITY":
                if val is None and rec.get("PERIGEE") and rec.get("APOGEE"):
                    rp, ra = float(rec["PERIGEE"]), float(rec["APOGEE"])
                    return f"{(ra - rp)/(ra + rp):.6f}"
                return f"{float(val):.6f}" if val is not None else ""
            if key in ("PERIGEE", "APOGEE"):
                return f"{float(val):.0f}" if val is not None else ""
            if key == "INCLINATION":
                return f"{float(val):.3f}" if val is not None else ""
            return str(val) if val is not None else ""
        except Exception as e:
            self._log(f"Format error: {e}")
            return ""

    def on_selection_changed(self) -> None:
        """Update list of selected NORAD IDs."""
        rows = {idx.row() for idx in self.ui.table_result.selectedIndexes()}
        self.selected_ids = []
        for r in rows:
            item = self.ui.table_result.item(r, 0)
            if item and item.text().isdigit():
                self.selected_ids.append(item.text())
        self._log(f"Selected IDs: {', '.join(self.selected_ids) or 'None'}")

    def on_accept(self) -> None:
        """Accept dialog only if at least one ID is selected."""
        if self.selected_ids:
            self._log(f"Accepting with IDs: {', '.join(self.selected_ids)}")
            self.accept()
        else:
            self._warn("Select at least one satellite.")

    def save_selected_data(self) -> None:
        """Save data for selected satellites in chosen format."""
        if not self.selected_ids:
            self._warn("No satellite selected to save.")
            return

        fmt = self.ui.combo_save_format.currentText()
        self._log(f"Saving {fmt} for IDs {', '.join(self.selected_ids)}.")

        paths = self._determine_paths(fmt, self.selected_ids)
        if not paths:
            return

        self._execute_save(fmt, paths)

    def _ensure_text(self, text: str, warning: str) -> None:
        if not text:
            self._warn(warning)
            raise ValueError(warning)

    def _determine_paths(self, fmt: str, ids: list) -> list:
        """Get file paths based on count (single or multiple)."""
        ext = 'json' if fmt == 'OMM' else 'txt'
        if len(ids) == 1:
            default = f"satellite_{ids[0]}.{ext}"
            path, _ = QFileDialog.getSaveFileName(self, "Save Satellite Data", default, f"{fmt} (*.{ext});;All Files (*)")
            if path:
                return [(ids[0], path)]
            self._log("Save cancelled.")
            return []

        dir_path = QFileDialog.getExistingDirectory(self, "Select directory to save data", "", QFileDialog.ShowDirsOnly)
        if not dir_path:
            self._log("Save cancelled.")
            return []
        return [(nid, os.path.join(dir_path, f"satellite_{nid}.{ext}")) for nid in ids]

    def _execute_save(self, fmt: str, paths: list) -> None:
        """Perform actual saving and update progress."""
        bar = self.ui.progress_bar
        bar.setVisible(True)
        bar.setRange(0, len(paths))
        start = datetime.now(timezone.utc)
        failures = []

        for i, (nid, p) in enumerate(paths, 1):
            self._log(f"Writing {fmt} for ID {nid} to {p}")
            try:
                if fmt == 'OMM':
                    data = self.client.get_omm(nid, start)
                    with open(p, 'w') as f:
                        json.dump(data, f, indent=4)
                else:
                    t1, t2, _ = self.client.get_tle(nid, start)
                    with open(p, 'w') as f:
                        f.write(f"{t1}\n{t2}\n")
                self._log(f"Saved {nid}.")
            except Exception as e:
                self._log(f"Error saving {nid}: {e}")
                failures.append(nid)
            bar.setValue(i)
            QtWidgets.QApplication.processEvents()

        bar.reset()
        bar.setVisible(False)

        if failures:
            self._handle_error(f"Failed to save IDs: {', '.join(failures)}.")
        else:
            QtWidgets.QMessageBox.information(self, "Success", "All data saved.")
            self._log("Save complete.")

    def _warn(self, message: str) -> None:
        QtWidgets.QMessageBox.warning(self, "Warning", message)
        self._log(message)

    def _handle_error(self, message: str) -> None:
        QtWidgets.QMessageBox.critical(self, "Error", message)
        self._log(message)

    def _log(self, message: str) -> None:
        if self.log_callback:
            self.log_callback(message)

    def get_selected_norad_ids(self) -> list:
        return self.selected_ids
