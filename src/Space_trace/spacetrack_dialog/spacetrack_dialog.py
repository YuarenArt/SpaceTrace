"""
SpaceTrackDialog module

This module defines the SpaceTrackDialog class, which provides a dialog interface to search satellite
data using the SpaceTrack API. Users can search by satellite name, country code, NORAD ID (single, range, or list),
or list all active satellites with a configurable limit. The dialog displays detailed satellite parameters
and logs all important actions.
"""

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton, QLabel, QLineEdit, 
    QPushButton, QComboBox, QTableWidget, QDialogButtonBox, QFileDialog )

from datetime import datetime, timezone
import json
import os

from ..spacetrack_client.spacetrack_client import SpacetrackClientWrapper
from .custom_query_dialog import CustomQueryDialog


class Ui_SpaceTrackDialog:
    """UI setup class for SpaceTrackDialog containing widget creation and layout."""

    def setup_ui(self, Dialog):
        """Set up all UI components."""
        Dialog.resize(900, 500)
        self.verticalLayout = QVBoxLayout(Dialog)
        
        self.display_attributes = {
            "NORAD_CAT_ID": "NORAD ID",
            "SATNAME": "Name",
            "COUNTRY": "Country",
            "LAUNCH": "Launch Date",
            "ECCENTRICITY": "Eccentricity",
            "PERIGEE": "Perigee (km)",
            "APOGEE": "Apogee (km)",
            "INCLINATION": "Inclination (°)"
        }

        # Search type radio buttons
        self.groupBoxSearchType = QGroupBox(Dialog)
        h_layout = QHBoxLayout(self.groupBoxSearchType)
        self.radioName = QRadioButton(self.groupBoxSearchType)
        self.radioActive = QRadioButton(self.groupBoxSearchType)
        self.radioCountry = QRadioButton(self.groupBoxSearchType)
        self.radioNorad = QRadioButton(self.groupBoxSearchType)
        for r in (self.radioName, self.radioActive, self.radioCountry, self.radioNorad):
            h_layout.addWidget(r)
        self.verticalLayout.addWidget(self.groupBoxSearchType)

        # Search criteria input
        self.labelSearch = QLabel(Dialog)
        self.lineEditSearch = QLineEdit(Dialog)
        self.pushButtonSearch = QPushButton(Dialog)
        self.verticalLayout.addWidget(self.labelSearch)
        self.verticalLayout.addWidget(self.lineEditSearch)
        self.verticalLayout.addWidget(self.pushButtonSearch)

        # Limit selector
        self.labelLimit = QLabel(Dialog)
        self.comboLimit = QComboBox(Dialog)
        self.comboLimit.addItems(["1", "5", "10", "25", "50", "100", "500", "1000"])
        self.comboLimit.setCurrentText("10")
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(self.labelLimit)
        limit_layout.addWidget(self.comboLimit)
        limit_layout.addStretch()
        self.verticalLayout.addLayout(limit_layout)

        # Results table
        self.tableResult = QTableWidget(Dialog)
        self.tableResult.setColumnCount(len(self.display_attributes))
        self.tableResult.setHorizontalHeaderLabels(list(self.display_attributes.values()))
        self.tableResult.setSelectionMode(QTableWidget.MultiSelection)
        self.tableResult.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableResult.horizontalHeader().setStretchLastSection(True)
        self.tableResult.setSortingEnabled(True)
        self.verticalLayout.addWidget(self.tableResult)
        
        # Save format selector and button
        self.save_layout = QHBoxLayout()
        self.labelSaveFormat = QLabel(Dialog)
        self.comboSaveFormat = QComboBox(Dialog)
        self.comboSaveFormat.addItems(["OMM", "TLE"])
        self.pushButtonSave = QPushButton(Dialog)
        self.save_layout.addWidget(self.labelSaveFormat)
        self.save_layout.addWidget(self.comboSaveFormat)
        self.save_layout.addWidget(self.pushButtonSave)
        self.save_layout.addStretch()
        self.verticalLayout.addLayout(self.save_layout)
        
        self.progressBar = QtWidgets.QProgressBar(Dialog)
        self.progressBar.setVisible(True)
        self.verticalLayout.addWidget(self.progressBar)

        # Buttons: Custom Query and OK/Cancel
        self.pushButtonCustomQuery = QPushButton(Dialog)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.verticalLayout.addWidget(self.pushButtonCustomQuery, 0, QtCore.Qt.AlignRight)
        self.verticalLayout.addWidget(self.buttonBox)

    def retranslate_ui(self, Dialog):
        """Translate all UI strings for localization."""
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("SpaceTrackDialog", "SpaceTrack Search"))
        self.groupBoxSearchType.setTitle(_translate("SpaceTrackDialog", "Search Type"))
        self.radioName.setText(_translate("SpaceTrackDialog", "By Name"))
        self.radioActive.setText(_translate("SpaceTrackDialog", "All Active"))
        self.radioCountry.setText(_translate("SpaceTrackDialog", "By Country"))
        self.radioNorad.setText(_translate("SpaceTrackDialog", "By NORAD ID"))
        self.labelSearch.setText(_translate("SpaceTrackDialog", "Search Criteria:"))
        self.lineEditSearch.setPlaceholderText(
            _translate(
                "SpaceTrackDialog",
                "Enter name, country code (e.g., US), NORAD ID (e.g., 25544), range (e.g., 25544-25550), or list (e.g., 25544,25545)"
            )
        )
        self.pushButtonSearch.setText(_translate("SpaceTrackDialog", "Search"))
        self.labelLimit.setText(_translate("SpaceTrackDialog", "Result Limit:"))
        self.pushButtonCustomQuery.setText(_translate("SpaceTrackDialog", "Custom Query"))
        self.labelSaveFormat.setText(_translate("SpaceTrackDialog", "Save Format:"))
        self.pushButtonSave.setText(_translate("SpaceTrackDialog", "Save Data"))
        
        self.display_attributes = {
            "NORAD_CAT_ID": _translate("SpaceTrackDialog", "NORAD ID"),
            "SATNAME": _translate("SpaceTrackDialog", "Name"),
            "COUNTRY": _translate("SpaceTrackDialog", "Country"),
            "LAUNCH": _translate("SpaceTrackDialog", "Launch Date"),
            "ECCENTRICITY": _translate("SpaceTrackDialog", "Eccentricity"),
            "PERIGEE": _translate("SpaceTrackDialog", "Perigee (km)"),
            "APOGEE": _translate("SpaceTrackDialog", "Apogee (km)"),
            "INCLINATION": _translate("SpaceTrackDialog", "Inclination (°)")
        }
        self.tableResult.setHorizontalHeaderLabels(list(self.display_attributes.values()))
        
class SpaceTrackDialog(QtWidgets.QDialog):
    """Logic implementation for SpaceTrackDialog to search and display satellite data."""

    def __init__(self, parent=None, login=None, password=None, log_callback=None, translator=None):
        super().__init__(parent)
        self.selected_norad_id = None
        self.translator = translator
        self.log_callback = log_callback
        self.client = SpacetrackClientWrapper(login, password)
        self.selected_norad_ids = []
        
        self.ui = Ui_SpaceTrackDialog()
        self.ui.setup_ui(self)
        self.ui.retranslate_ui(self)

        # Signal connections
        self.ui.pushButtonSearch.clicked.connect(self.perform_search)
        self.ui.pushButtonCustomQuery.clicked.connect(self.open_custom_query_dialog)
        self.ui.buttonBox.accepted.connect(self.on_accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.tableResult.itemSelectionChanged.connect(self.on_selection_changed)
        self.ui.radioName.setChecked(True)
        self.ui.pushButtonSave.clicked.connect(self.save_selected_satellite_data)

    def save_selected_satellite_data(self):
        """Save data for all selected satellites in the chosen format (OMM or TLE)."""
        _translate = QtCore.QCoreApplication.translate
        if not self.selected_norad_ids:
            self._warn(_translate("SpaceTrackDialog", "Please select at least one satellite to save its data."))
            return

        format_type = self.ui.comboSaveFormat.currentText()
        self._log(_translate("SpaceTrackDialog", f"Preparing to save data for NORAD IDs {', '.join(self.selected_norad_ids)} in {format_type} format."))

        # Open dialog to choose save directory
        save_dir = QFileDialog.getExistingDirectory(
            self,
            _translate("SpaceTrackDialog", "Select Directory to Save Satellite Data"),
            "",
            QFileDialog.ShowDirsOnly
        )
        if not save_dir:
            self._log(_translate("SpaceTrackDialog", "Save operation cancelled."))
            return

        # Set up progress bar
        self.ui.progressBar.setTextVisible(True)
        self.ui.progressBar.setRange(0, len(self.selected_norad_ids))

        start_datetime = datetime.now(timezone.utc)
        failed_satellites = []

        for i, norad_id in enumerate(self.selected_norad_ids):
            file_ext = 'json' if format_type == 'OMM' else 'txt'
            file_name = os.path.join(save_dir, f"satellite_{norad_id}.{file_ext}")
            self._log(_translate("SpaceTrackDialog", f"Saving data for NORAD ID {norad_id} to {file_name}."))

            try:
                if format_type == "OMM":
                    data = self.client.get_omm(norad_id, start_datetime)
                    with open(file_name, 'w') as f:
                        json.dump(data, f, indent=4)
                else:  # TLE
                    tle_1, tle_2, _ = self.client.get_tle(norad_id, start_datetime)
                    with open(file_name, 'w') as f:
                        f.write(f"{tle_1}\n{tle_2}\n")

                self._log(_translate("SpaceTrackDialog", f"Successfully saved {format_type} data for NORAD ID {norad_id} to {file_name}."))

            except Exception as e:
                error_msg = _translate("SpaceTrackDialog", f"Failed to save {format_type} data for NORAD ID {norad_id}: {e}")
                self._log(error_msg)
                failed_satellites.append(norad_id)
                

            self.ui.progressBar.setValue(i + 1)
            QtWidgets.QApplication.processEvents()

        self.ui.progressBar.setRange(0, 1)
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setFormat("") 
        self.ui.progressBar.setTextVisible(False) 
        
        # Report any failures after processing all satellites
        if failed_satellites:
            self._handle_error(_translate("SpaceTrackDialog", f"Failed to save data for NORAD IDs: {', '.join(failed_satellites)}. See log for details."))
        else:
            self._log(_translate("SpaceTrackDialog", "All satellite data saved successfully."))
    
    def open_custom_query_dialog(self):
        """Launch the custom query dialog and perform search if accepted."""
        dlg = CustomQueryDialog(self, translator=self.translator)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            conds = dlg.get_conditions()
            if conds:
                self.perform_custom_search(conds)

    def perform_search(self):
        """Execute a search based on current input and selected search type."""
        self._log("Starting satellite search...")
        text = self.ui.lineEditSearch.text().strip()
        limit = int(self.ui.comboLimit.currentText())
        self.ui.tableResult.setRowCount(0)
        try:
            results = self._get_search_results(text, limit)
            self._display_results(results)
        except Exception as e:
            self._handle_error(f"Search error: {e}")

    def _get_search_results(self, text, limit):
        """Route search request to appropriate API method."""
        if self.ui.radioName.isChecked():
            if not text:
                self._warn("Please enter a satellite name.")
                return []
            return self.client.search_by_name(text, limit)
        if self.ui.radioActive.isChecked():
            return self.client.get_active_satellites(limit)
        if self.ui.radioCountry.isChecked():
            if not text:
                self._warn("Please enter a country code (e.g., US).")
                return []
            return self.client.search_by_country(text, limit)
        if self.ui.radioNorad.isChecked():
            if not text:
                self._warn("Please enter a NORAD ID, range, or list.")
                return []
            return self.client.search_by_norad_id(text, limit)
        return []

    def perform_custom_search(self, conditions):
        """Execute a custom query with given conditions."""
        self._log("Starting custom satellite search...")
        limit = int(self.ui.comboLimit.currentText())
        self.ui.tableResult.setRowCount(0)
        try:
            results = self.client.search_by_custom_query(conditions, limit)
            self._display_results(results)
        except Exception as e:
            self._handle_error(f"Custom query error: {e}")

    def _display_results(self, results):
        """Populate the result table with satellite entries."""
        if not results:
            self._log("No results found.")
            self.ui.tableResult.setRowCount(1)
            self.ui.tableResult.setItem(0, 0, QtWidgets.QTableWidgetItem("No results"))
            return
        self._log(f"Found {len(results)} results.")
        for sat in results:
            if isinstance(sat, dict):
                self._add_result_row(sat)
            else:
                self._log(f"Unexpected result type: {type(sat)}")

    def _add_result_row(self, sat):
        """Add a single satellite record as a new row."""
        row = self.ui.tableResult.rowCount()
        self.ui.tableResult.insertRow(row)
        for col, key in enumerate(self.ui.display_attributes):
            val = self._format_value(key, sat)
            item = QtWidgets.QTableWidgetItem(val)
            if key == "NORAD_CAT_ID" and val.isdigit():
                item.setData(QtCore.Qt.UserRole, int(val))
            self.ui.tableResult.setItem(row, col, item)

    def _format_value(self, key, sat):
        """Format values for display based on column type."""
        value = sat.get(key)
        try:
            if key == "ECCENTRICITY" and value is None and sat.get("PERIGEE") and sat.get("APOGEE"):
                rp, ra = float(sat["PERIGEE"]), float(sat["APOGEE"])
                return f"{(ra - rp)/(ra + rp):.6f}"
            if key in ("PERIGEE", "APOGEE"):
                return f"{float(value):.0f}" if value is not None else ""
            if key == "INCLINATION":
                return f"{float(value):.3f}" if value is not None else ""
            if key == "ECCENTRICITY":
                return f"{float(value):.6f}" if value is not None else ""
            return str(value) if value is not None else ""
        except Exception as e:
            self._log(f"Error formatting {key}: {e}")
            return ""

    def on_selection_changed(self):
        """Track selected rows and store their NORAD IDs."""
        _translate = QtCore.QCoreApplication.translate
        selected_rows = set(index.row() for index in self.ui.tableResult.selectedIndexes())
        self.selected_norad_ids = []
        for row in selected_rows:
            item = self.ui.tableResult.item(row, 0)
            if item and item.text().isdigit():
                self.selected_norad_ids.append(item.text())
        self._log(_translate("SpaceTrackDialog", f"Selected satellite NORAD IDs: {', '.join(self.selected_norad_ids) if self.selected_norad_ids else 'None'}"))

    def on_accept(self):
        """Accept dialog if at least one satellite has been selected."""
        _translate = QtCore.QCoreApplication.translate
        if self.selected_norad_ids:
            self._log(_translate("SpaceTrackDialog", f"Satellites {', '.join(self.selected_norad_ids)} selected; accepting."))
            self.accept()
        else:
            self._warn(_translate("SpaceTrackDialog", "Please select at least one satellite from the list."))

    def get_selected_norad_ids(self):
        """Return the list of currently selected NORAD IDs."""
        return self.selected_norad_ids

    def _warn(self, msg):
        """Show a warning message box and log it."""
        _translate = QtCore.QCoreApplication.translate
        QtWidgets.QMessageBox.warning(self, _translate("SpaceTrackDialog", "Warning"), _translate("SpaceTrackDialog", msg))
        self._log(msg)

    def _handle_error(self, msg):
        """Show an error message box and log it."""
        _translate = QtCore.QCoreApplication.translate
        QtWidgets.QMessageBox.critical(self, _translate("SpaceTrackDialog", "Error"), _translate("SpaceTrackDialog", msg))
        self._log(msg)

    def _log(self, msg):
        """Log a message via provided callback if available."""
        if self.log_callback:
            self.log_callback(msg)