"""
SpaceTrackDialog module

This module defines the SpaceTrackDialog class, which provides a dialog interface to search satellite
data using the SpaceTrack API. Users can search by satellite name, country code, NORAD ID (single, range, or list),
or list all active satellites with a configurable limit. The dialog displays detailed satellite parameters
and logs all important actions.
"""

from PyQt5 import QtWidgets, QtCore
from ..spacetrack_client.spacetrack_client import SpacetrackClientWrapper
from .custom_query_dialog import CustomQueryDialog

class SpaceTrackDialog(QtWidgets.QDialog):
    """
    Dialog for querying satellite data from SpaceTrack and displaying it.

    Provides UI components for searching by name, country code, NORAD ID, or active status,
    and displays results in a sortable table. Translations are applied via Qt's
    QCoreApplication.translate to support multiple languages.
    """

    DISPLAY_ATTRIBUTES = {
        "NORAD_CAT_ID": "NORAD ID",
        "SATNAME": "Name",
        "COUNTRY": "Country",
        "LAUNCH": "Launch Date",
        "ECCENTRICITY": "Eccentricity",
        "PERIGEE": "Perigee (km)",
        "APOGEE": "Apogee (km)",
        "INCLINATION": "Inclination (°)"
    }

    def __init__(self, parent=None, login=None, password=None, log_callback=None, translator=None):
        """
        Initialize the SpaceTrack dialog with optional logging.

        :param parent: Parent QWidget.
        :param login: SpaceTrack API login (email).
        :param password: SpaceTrack API password.
        :param log_callback: Callable for external logging.
        """
        super().__init__(parent)
        self.selected_norad_id = None
        self.translator = translator
        self.log_callback = log_callback
        self.client = SpacetrackClientWrapper(login, password)
        self.init_ui()

    def init_ui(self):
        """
        Set up all UI components without hard‑coded text.
        Text is assigned in retranslate_ui().
        """
        self.resize(900, 500)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)

        # Search type radio buttons
        self.groupBoxSearchType = QtWidgets.QGroupBox(self)
        h_layout = QtWidgets.QHBoxLayout(self.groupBoxSearchType)
        self.radioName = QtWidgets.QRadioButton(self.groupBoxSearchType)
        self.radioActive = QtWidgets.QRadioButton(self.groupBoxSearchType)
        self.radioCountry = QtWidgets.QRadioButton(self.groupBoxSearchType)
        self.radioNorad = QtWidgets.QRadioButton(self.groupBoxSearchType)
        for r in (self.radioName, self.radioActive, self.radioCountry, self.radioNorad):
            h_layout.addWidget(r)
        self.verticalLayout.addWidget(self.groupBoxSearchType)

        # Search criteria input
        self.labelSearch = QtWidgets.QLabel(self)
        self.lineEditSearch = QtWidgets.QLineEdit(self)
        self.pushButtonSearch = QtWidgets.QPushButton(self)
        self.verticalLayout.addWidget(self.labelSearch)
        self.verticalLayout.addWidget(self.lineEditSearch)
        self.verticalLayout.addWidget(self.pushButtonSearch)

        # Limit selector
        self.labelLimit = QtWidgets.QLabel(self)
        self.comboLimit = QtWidgets.QComboBox(self)
        self.comboLimit.addItems(["1","5","10","25","50","100","500","1000"])
        self.comboLimit.setCurrentText("10")
        limit_layout = QtWidgets.QHBoxLayout()
        limit_layout.addWidget(self.labelLimit)
        limit_layout.addWidget(self.comboLimit)
        limit_layout.addStretch()
        self.verticalLayout.addLayout(limit_layout)

        # Results table
        self.tableResult = QtWidgets.QTableWidget(self)
        self.tableResult.setColumnCount(len(self.DISPLAY_ATTRIBUTES))
        self.tableResult.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tableResult.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableResult.horizontalHeader().setStretchLastSection(True)
        self.tableResult.setSortingEnabled(True)
        self.verticalLayout.addWidget(self.tableResult)

        # Buttons: Custom Query and OK/Cancel
        self.pushButtonCustomQuery = QtWidgets.QPushButton(self)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.verticalLayout.addWidget(self.pushButtonCustomQuery, 0, QtCore.Qt.AlignRight)
        self.verticalLayout.addWidget(self.buttonBox)

        # Signal connections
        self.pushButtonSearch.clicked.connect(self.perform_search)
        self.pushButtonCustomQuery.clicked.connect(self.open_custom_query_dialog)
        self.buttonBox.accepted.connect(self.on_accept)
        self.buttonBox.rejected.connect(self.reject)
        self.tableResult.itemSelectionChanged.connect(self.on_selection_changed)
        self.radioName.setChecked(True)

        self.retranslate_ui()

    def retranslate_ui(self):
        """
        Translate all UI strings for localization.
        """
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("SpaceTrackDialog", "SpaceTrack Search"))
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
        headers = [
            _translate("SpaceTrackDialog", lbl)
            for lbl in self.DISPLAY_ATTRIBUTES.values()
        ]
        self.tableResult.setHorizontalHeaderLabels(headers)

    def open_custom_query_dialog(self):
        """
        Launch the custom query dialog and perform search if accepted.
        """
        dlg = CustomQueryDialog(self, translator=self.translator)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            conds = dlg.get_conditions()
            if conds:
                self.perform_custom_search(conds)

    def perform_search(self):
        """
        Execute a search based on current input and selected search type.
        """
        self._log("Starting satellite search...")
        text = self.lineEditSearch.text().strip()
        limit = int(self.comboLimit.currentText())
        self.tableResult.setRowCount(0)
        try:
            results = self._get_search_results(text, limit)
            self._display_results(results)
        except Exception as e:
            self._handle_error(f"Search error: {e}")

    def _get_search_results(self, text, limit):
        """
        Route search request to appropriate API method.
        """
        if self.radioName.isChecked():
            if not text:
                self._warn("Please enter a satellite name.")
                return []
            return self.client.search_by_name(text, limit)
        if self.radioActive.isChecked():
            return self.client.get_active_satellites(limit)
        if self.radioCountry.isChecked():
            if not text:
                self._warn("Please enter a country code (e.g., US).")
                return []
            return self.client.search_by_country(text, limit)
        if self.radioNorad.isChecked():
            if not text:
                self._warn("Please enter a NORAD ID, range, or list.")
                return []
            return self.client.search_by_norad_id(text, limit)
        return []

    def perform_custom_search(self, conditions):
        """
        Execute a custom query with given conditions.
        """
        self._log("Starting custom satellite search...")
        limit = int(self.comboLimit.currentText())
        self.tableResult.setRowCount(0)
        try:
            results = self.client.search_by_custom_query(conditions, limit)
            self._display_results(results)
        except Exception as e:
            self._handle_error(f"Custom query error: {e}")

    def _display_results(self, results):
        """
        Populate the result table with satellite entries.
        """
        if not results:
            self._log("No results found.")
            self.tableResult.setRowCount(1)
            self.tableResult.setItem(0, 0, QtWidgets.QTableWidgetItem("No results"))
            return
        self._log(f"Found {len(results)} results.")
        for sat in results:
            if isinstance(sat, dict):
                self._add_result_row(sat)
            else:
                self._log(f"Unexpected result type: {type(sat)}")

    def _add_result_row(self, sat):
        """Add a single satellite record as a new row."""
        row = self.tableResult.rowCount()
        self.tableResult.insertRow(row)
        for col, key in enumerate(self.DISPLAY_ATTRIBUTES):
            val = self._format_value(key, sat)
            item = QtWidgets.QTableWidgetItem(val)
            if key == "NORAD_CAT_ID" and val.isdigit():
                item.setData(QtCore.Qt.UserRole, int(val))
            self.tableResult.setItem(row, col, item)

    def _format_value(self, key, sat):
        """
        Format values for display based on column type.
        """
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
        """
        Track which row is selected and store NORAD ID.
        """
        sel = self.tableResult.selectedIndexes()
        if sel:
            row = sel[0].row()
            item = self.tableResult.item(row, 0)
            self.selected_norad_id = item.text() if item else None
            self._log(f"Selected satellite NORAD ID: {self.selected_norad_id}")

    def on_accept(self):
        """
        Accept dialog if a satellite has been selected.
        """
        if self.selected_norad_id:
            self._log(f"Satellite {self.selected_norad_id} selected; accepting.")
            self.accept()
        else:
            self._warn("Please select a satellite from the list.")

    def get_selected_norad_id(self):
        """
        Return the currently selected NORAD ID (string).
        """
        return self.selected_norad_id

    def _warn(self, msg):
        """
        Show a warning message box and log it.
        """
        QtWidgets.QMessageBox.warning(self, "Warning", msg)
        self._log(msg)

    def _handle_error(self, msg):
        """
        Show an error message box and log it.
        """
        QtWidgets.QMessageBox.critical(self, "Error", msg)
        self._log(msg)

    def _log(self, msg):
        """
        Log a message via provided callback if available.
        """
        if self.log_callback:
            self.log_callback(msg)