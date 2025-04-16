"""
SpaceTrackDialog module

This module defines the SpaceTrackDialog class, which provides a dialog interface to search satellite
data using the SpaceTrack API. Users can search by satellite name, country code, NORAD ID (single, range, or list),
or list all active satellites with a configurable limit. The dialog displays detailed satellite parameters
and logs all important actions.
"""

from PyQt5 import QtWidgets, QtCore
from ..spacetrack_client.spacetrack_client import SpacetrackClientWrapper


class SpaceTrackDialog(QtWidgets.QDialog):
    """
    Dialog for querying satellite data from SpaceTrack and displaying it.

    Attributes:
        selected_norad_id (str): NORAD ID of the selected satellite.
        client (SpacetrackClientWrapper): Wrapper for SpaceTrack API requests.
        log_callback (callable): Callback for logging messages externally.
    """

    def __init__(self, parent=None, login=None, password=None, log_callback=None):
        """
        Initialize the SpaceTrack dialog window.

        Args:
            parent (QWidget): Parent widget.
            login (str): SpaceTrack API login.
            password (str): SpaceTrack API password.
            log_callback (callable): Callback for logging.
        """
        super().__init__(parent)
        self.selected_norad_id = None
        self.log_callback = log_callback
        self.client = SpacetrackClientWrapper(login, password)
        self.init_ui()

    def init_ui(self):
        """Set up the UI components of the dialog."""
        self.setWindowTitle("SpaceTrack Search")
        self.resize(900, 500)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)

        self._setup_search_type_controls()
        self._setup_search_input()
        self._setup_limit_selector()
        self._setup_result_table()
        self._setup_buttons()
        self._connect_signals()

    def _setup_search_type_controls(self):
        """Configure the radio buttons for search type selection."""
        self.groupBoxSearchType = QtWidgets.QGroupBox("Search Type", self)
        layout = QtWidgets.QHBoxLayout(self.groupBoxSearchType)

        self.radioName = QtWidgets.QRadioButton("By Name")
        self.radioActive = QtWidgets.QRadioButton("All Active")
        self.radioCountry = QtWidgets.QRadioButton("By Country")
        self.radioNorad = QtWidgets.QRadioButton("By NORAD ID")
        self.radioName.setChecked(True)

        for radio in (self.radioName, self.radioActive, self.radioCountry, self.radioNorad):
            layout.addWidget(radio)

        self.verticalLayout.addWidget(self.groupBoxSearchType)

    def _setup_search_input(self):
        """Configure search input field and button."""
        self.labelSearch = QtWidgets.QLabel("Search Criteria:")
        self.lineEditSearch = QtWidgets.QLineEdit()
        self.lineEditSearch.setPlaceholderText(
            "Enter name, country code (e.g., US), NORAD ID (e.g., 25544), range (e.g., 25544-25550), or list (e.g., 25544,25545)"
        )
        self.pushButtonSearch = QtWidgets.QPushButton("Search")

        self.verticalLayout.addWidget(self.labelSearch)
        self.verticalLayout.addWidget(self.lineEditSearch)
        self.verticalLayout.addWidget(self.pushButtonSearch)

    def _setup_limit_selector(self):
        """Configure the limit selection combo box."""
        self.labelLimit = QtWidgets.QLabel("Result Limit:")
        self.comboLimit = QtWidgets.QComboBox()
        self.comboLimit.addItems(["10", "50", "100", "500", "1000"])
        self.comboLimit.setCurrentText("100")

        limit_layout = QtWidgets.QHBoxLayout()
        limit_layout.addWidget(self.labelLimit)
        limit_layout.addWidget(self.comboLimit)
        limit_layout.addStretch()
        self.verticalLayout.addLayout(limit_layout)

    def _setup_result_table(self):
        """Configure the table for displaying satellite search results."""
        self.tableResult = QtWidgets.QTableWidget()
        self.tableResult.setColumnCount(7)
        self.tableResult.setHorizontalHeaderLabels([
            "NORAD ID", "Name", "Country", "Eccentricity", "Perigee (km)", "Apogee (km)", "Inclination (°)"
        ])
        self.tableResult.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tableResult.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableResult.horizontalHeader().setStretchLastSection(True)
        self.tableResult.setSortingEnabled(True)

        self.verticalLayout.addWidget(self.tableResult)

    def _setup_buttons(self):
        """Add OK and Cancel buttons."""
        self.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.verticalLayout.addWidget(self.buttonBox)

    def _connect_signals(self):
        """Connect UI events to corresponding methods."""
        self.pushButtonSearch.clicked.connect(self.perform_search)
        self.buttonBox.accepted.connect(self.on_accept)
        self.buttonBox.rejected.connect(self.reject)
        self.tableResult.itemSelectionChanged.connect(self.on_selection_changed)

    def perform_search(self):
        """Handle the search button press based on selected mode."""
        self._log("Starting satellite search...")
        search_text = self.lineEditSearch.text().strip()
        limit = int(self.comboLimit.currentText())
        self.tableResult.setRowCount(0)

        try:
            results = self._get_search_results(search_text, limit)
            self._display_results(results)
        except Exception as e:
            self._handle_error(f"Search error: {e}")

    def _get_search_results(self, search_text, limit):
        """
        Return results from the appropriate API method based on radio selection.

        Args:
            search_text (str): User input for search.
            limit (int): Maximum number of results to return.

        Returns:
            list: List of satellite data dictionaries.
        """
        if self.radioName.isChecked():
            if not search_text:
                self._warn("Please enter a satellite name.")
                return []
            return self.client.search_by_name(search_text, limit)

        elif self.radioActive.isChecked():
            return self.client.get_active_satellites(limit)

        elif self.radioCountry.isChecked():
            if not search_text:
                self._warn("Please enter a country code (e.g., US).")
                return []
            return self.client.search_by_country(search_text, limit)

        elif self.radioNorad.isChecked():
            if not search_text:
                self._warn("Please enter a NORAD ID, range, or list.")
                return []
            return self.client.search_by_norad_id(search_text, limit)

        return []

    def _display_results(self, results):
        """
        Populate the result table with satellite data.
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
        row = self.tableResult.rowCount()
        self.tableResult.insertRow(row)


        perigee = sat.get("PERIGEE")
        apogee = sat.get("APOGEE")
        eccentricity = sat.get("ECCENTRICITY")
        if eccentricity is None and perigee is not None and apogee is not None:
            try:
                rp = float(perigee)
                ra = float(apogee)
                eccentricity = (ra - rp) / (ra + rp)
            except Exception as e:
                self._log(f"Failed to calculate eccentricity: {e}")
                eccentricity = ""
        elif eccentricity is None:
            eccentricity = ""

        # Build values
        values = [
            str(sat.get("NORAD_CAT_ID", "")),
            sat.get("SATNAME", ""),
            sat.get("COUNTRY", ""),
            f"{eccentricity:.6f}" if isinstance(eccentricity, float) else str(eccentricity),
            f"{float(perigee):.3f}" if perigee is not None else "",
            f"{float(apogee):.3f}" if apogee is not None else "",
            f"{float(sat.get('INCLINATION', 0.0)):.3f}" if sat.get("INCLINATION") is not None else ""
        ]

        # Set cells
        for col, val in enumerate(values):
            item = QtWidgets.QTableWidgetItem(val)
            if col == 0:
                item.setData(QtCore.Qt.ItemDataRole.UserRole, int(val) if val.isdigit() else 0)
            self.tableResult.setItem(row, col, item)

    def on_selection_changed(self):
        """Update internal state when user selects a row in the table."""
        selected_rows = self.tableResult.selectedIndexes()
        if selected_rows:
            row = selected_rows[0].row()
            norad_item = self.tableResult.item(row, 0)  # Always get NORAD ID from column 0
            self.selected_norad_id = norad_item.text() if norad_item else None
            if self.selected_norad_id:
                self._log(f"Selected satellite NORAD ID: {self.selected_norad_id}")
            else:
                self._log("No valid NORAD ID in selected row")

    def on_accept(self):
        """Accept the dialog if a satellite is selected; otherwise show warning."""
        if self.selected_norad_id:
            self._log(f"Satellite {self.selected_norad_id} selected; accepting dialog.")
            self.accept()
        else:
            self._warn("Please select a satellite from the list.")
            self._log("No satellite selected; dialog not accepted.")

    def get_selected_norad_id(self):
        """
        Get the NORAD ID of the selected satellite.
        """
        return self.selected_norad_id

    def _warn(self, message):
        """
        Show warning dialog with a message.
        """
        QtWidgets.QMessageBox.warning(self, "Warning", message)
        self._log(message)

    def _handle_error(self, message):
        """
        Display error message and log it.
        """
        QtWidgets.QMessageBox.critical(self, "Error", message)
        self._log(message)

    def _log(self, message):
        """
        Log a message using the provided callback.
        """
        if self.log_callback:
            self.log_callback(message)