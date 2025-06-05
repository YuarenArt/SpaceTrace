from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton, QLabel, QLineEdit,
    QPushButton, QComboBox, QTableWidget, QDialogButtonBox, QFileDialog, QDialog,
    QMessageBox
)
from datetime import datetime, timezone
import json
import os
import logging

from ..spacetrack_client.spacetrack_client import SpacetrackClientWrapper
from .custom_query_dialog import CustomQueryDialog


class Ui_SpaceTrackDialog:
    """UI setup for the SpaceTrack dialog interface."""

    def setup_ui(self, dialog: QDialog) -> None:
        dialog.resize(900, 500)
        self._create_main_layout(dialog)
        self._create_search_type_group(dialog)
        self._create_search_inputs(dialog)
        self._create_error_label(dialog)
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
        
        self.line_edit_search.textChanged.connect(self._on_search_text_changed)
        
        self.main_layout.addWidget(self.label_search)
        self.main_layout.addWidget(self.line_edit_search)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.push_button_search)
        button_layout.addStretch()
        self.main_layout.addLayout(button_layout)

    def _create_error_label(self, dialog: QDialog) -> None:
        self.error_label = QLabel(dialog)
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setVisible(False)
        self.main_layout.addWidget(self.error_label)

    def _on_search_text_changed(self, text: str) -> None:
        """Handle real-time validation of search input."""
        if not text.strip():
            return

        # Get current search type
        if self.radio_name.isChecked():
            if len(text) < 2:
                QMessageBox.warning(
                    None,
                    "Validation Error",
                    "Satellite name must be at least 2 characters long"
                )
        elif self.radio_country.isChecked():
            if not text.isalpha() or len(text) != 2:
                QMessageBox.warning(
                    None,
                    "Validation Error",
                    "Country code must be 2 letters (e.g., US)"
                )
        elif self.radio_norad.isChecked():
            if not self._is_valid_norad_input(text):
                QMessageBox.warning(
                    None,
                    "Validation Error",
                    "Invalid NORAD ID format. Use single ID, range (e.g., 25544-25550), or list (e.g., 25544,25545)"
                )

    def _is_valid_norad_input(self, text: str) -> bool:
        if text.isdigit():
            return True
        
        if '-' in text:
            parts = text.split('-')
            if len(parts) == 2 and all(p.isdigit() for p in parts):
                return True
        
        if ',' in text:
            parts = text.split(',')
            return all(p.strip().isdigit() for p in parts)
        
        return False

    def _update_placeholder_text(self) -> None:
        if self.radio_name.isChecked():
            self.line_edit_search.setPlaceholderText("Enter satellite name (e.g., STARLINK-1234)")
        elif self.radio_active.isChecked():
            self.line_edit_search.setPlaceholderText("No input needed - will show all active satellites")
        elif self.radio_country.isChecked():
            self.line_edit_search.setPlaceholderText("Enter country code (e.g., US)")
        elif self.radio_norad.isChecked():
            self.line_edit_search.setPlaceholderText("Enter NORAD ID, range (e.g., 25544-25550), or list (e.g., 25544,25545)")

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
        self._init_logger()
        self.client = SpacetrackClientWrapper(login, password)
        self.selected_ids = []
        self.custom_conds = []
        self.log_callback = log_callback

        self.ui = Ui_SpaceTrackDialog()
        self.ui.setup_ui(self)
        self.ui.retranslate_ui(self)
        self._connect_signals()
        self.ui.radio_name.setChecked(True)
        self.ui._update_placeholder_text()  # Initialize placeholder text

    def _init_logger(self):
        """Initialize the logger."""
        self.logger = logging.getLogger("SpaceTrackDialog")
        self.logger.setLevel(logging.DEBUG)
        log_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "SpaceTracePlugin.log"
        )
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def _log_to_file(self, message: str, level: str = "INFO"):
        """Log message to file with specified level."""
        if level.upper() == "DEBUG":
            self.logger.debug(message)
        elif level.upper() == "WARNING":
            self.logger.warning(message)
        elif level.upper() == "ERROR":
            self.logger.error(message)
        else:
            self.logger.info(message)

    def _log(self, message: str, level: str = "INFO") -> None:
        """Log message using log_callback and internal logger."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        if self.log_callback and level.upper() in ["INFO", "WARNING", "DEBUG"]:
            self.log_callback(formatted_message)
        
        if level.upper() == "DEBUG":
            self.logger.debug(message)
        elif level.upper() == "WARNING":
            self.logger.warning(message)
        elif level.upper() == "ERROR":
            self.logger.error(message)
        else:
            self.logger.info(message)

    def _connect_signals(self) -> None:
        ui = self.ui
        ui.push_button_search.clicked.connect(self.perform_search)
        ui.push_button_custom.clicked.connect(self.open_custom_query)
        ui.button_box.accepted.connect(self.on_accept)
        ui.button_box.rejected.connect(self.reject)
        ui.table_result.itemSelectionChanged.connect(self.on_selection_changed)
        ui.push_button_save.clicked.connect(self.save_selected_data)
        
        # Connect radio buttons to update placeholder text
        ui.radio_name.toggled.connect(self._on_search_type_changed)
        ui.radio_active.toggled.connect(self._on_search_type_changed)
        ui.radio_country.toggled.connect(self._on_search_type_changed)
        ui.radio_norad.toggled.connect(self._on_search_type_changed)

    def _on_search_type_changed(self, checked: bool) -> None:
        """Handle search type radio button changes."""
        if checked:
            self.ui._update_placeholder_text()
            self.ui.line_edit_search.clear()

    def perform_search(self) -> None:
        """Search satellites based on selected criteria and display results."""
        text = self.ui.line_edit_search.text().strip()
        limit = int(self.ui.combo_limit.currentText())
        self.ui.table_result.setRowCount(0)

        try:
            # Validate input before search
            if self.ui.radio_name.isChecked() and len(text) < 2:
                raise ValueError("Satellite name must be at least 2 characters long")
            elif self.ui.radio_country.isChecked() and (not text.isalpha() or len(text) != 2):
                raise ValueError("Country code must be 2 letters (e.g., US)")
            elif self.ui.radio_norad.isChecked() and not self.ui._is_valid_norad_input(text):
                raise ValueError("Invalid NORAD ID format")

            results = self._get_results(text, limit)
            if not results:
                QMessageBox.information(
                    self,
                    "No Results",
                    "No results found. Please try different search criteria."
                )
            else:
                self._display_results(results)
        except ValueError as err:
            self._handle_validation_error(str(err))
        except Exception as err:
            self._handle_error(f"Search error: {err}")

    def _handle_validation_error(self, message: str) -> None:
        """Handle validation errors with user-friendly messages."""
        QMessageBox.warning(self, "Validation Error", message)
        self._log(f"Validation error: {message}", "WARNING")

    def _handle_error(self, message: str) -> None:
        """Handle general errors with user-friendly messages."""
        QMessageBox.critical(self, "Error", "An error occurred during the search. Please try again.")
        self._log(message, "ERROR")

    def _get_results(self, text: str, limit: int):
        """Dispatch search by current radio selection."""
        ui = self.ui
        match True:
            case _ if ui.radio_name.isChecked():
                self._ensure_text(text, "Please enter a satellite name.")
                self._log(f"Searching by name: {text}, limit: {limit}", "DEBUG")
                return self.client.search_by_name(text, limit)
            case _ if ui.radio_active.isChecked():
                self._log(f"Searching all active satellites, limit: {limit}", "DEBUG")
                return self.client.get_active_satellites(limit)
            case _ if ui.radio_country.isChecked():
                self._ensure_text(text, "Please enter a country code (e.g., US).")
                self._log(f"Searching by country: {text}, limit: {limit}", "DEBUG")
                return self.client.search_by_country(text, limit)
            case _ if ui.radio_norad.isChecked():
                self._ensure_text(text, "Please enter a NORAD ID, range, or list.")
                self._log(f"Searching by NORAD ID: {text}, limit: {limit}", "DEBUG")
                return self.client.search_by_norad_id(text, limit)
            case _:
                self._log("No search criteria selected", "WARNING")
                return []

    def open_custom_query(self) -> None:
        self._log("Opening custom query dialog", "DEBUG")
        dialog = CustomQueryDialog(self)
        dialog.set_saved_conditions(self.custom_conds)
        if dialog.exec_() == QDialog.Accepted:
            self.custom_conds = dialog.get_saved_conditions()
            self._log(f"Custom query conditions: {self.custom_conds}", "DEBUG")
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
        
        paths = [(nid, os.path.join(dir_path, f"satellite_{nid}.{ext}")) for nid in ids]
        self._log(f"Selected save paths: {paths}", "DEBUG")
        return paths

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
        self._log(f"Warning: {message}", "WARNING")

    def get_selected_norad_ids(self) -> list:
        return self.selected_ids
