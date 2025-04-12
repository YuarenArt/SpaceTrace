"""
SpaceTrackDialog module

This module defines the SpaceTrackDialog class which provides a dialog
for searching satellite data via the SpaceTrack API. The dialog supports
search by name, listing of all active satellites, and search by country code.
It logs key events and search results via a callback function.
"""

from PyQt5 import QtWidgets, QtCore
import json
from ..spacetrack_client.spacetrack_client import SpacetrackClientWrapper

class SpaceTrackDialog(QtWidgets.QDialog):
    """
    A dialog for searching satellites using the SpaceTrack API.

    Attributes:
        login (str): SpaceTrack login credential.
        password (str): SpaceTrack password.
        client (SpacetrackClientWrapper): Instance of the SpaceTrack API wrapper.
        log_callback (callable): Callback function to log messages (e.g., log_message from main plugin).
        selected_norad_id (str): The NORAD ID selected by the user.
    """
    def __init__(self, parent=None, login=None, password=None, log_callback=None):
        """
        Initialize the search dialog.

        :param parent: Parent widget.
        :param login: SpaceTrack account login.
        :param password: SpaceTrack account password.
        :param log_callback: Callback function for logging messages.
        """
        super().__init__(parent)
        self.selected_norad_id = None
        self.log_callback = log_callback
        self.client = SpacetrackClientWrapper(login, password)
        self.setupUi()

    def setupUi(self):
        """
        Set up the user interface for the dialog.
        """
        self.setWindowTitle(self.tr("SpaceTrack Search"))
        self.resize(600, 400)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)

        # Group for selecting the search type.
        self.groupBoxSearchType = QtWidgets.QGroupBox(self.tr("Search Type"), self)
        self.hLayoutSearchType = QtWidgets.QHBoxLayout(self.groupBoxSearchType)

        self.radioName = QtWidgets.QRadioButton(self.tr("By Name"), self.groupBoxSearchType)
        self.radioActive = QtWidgets.QRadioButton(self.tr("All Active"), self.groupBoxSearchType)
        self.radioCountry = QtWidgets.QRadioButton(self.tr("By Country"), self.groupBoxSearchType)
        # Default selection: search by name.
        self.radioName.setChecked(True)
        self.hLayoutSearchType.addWidget(self.radioName)
        self.hLayoutSearchType.addWidget(self.radioActive)
        self.hLayoutSearchType.addWidget(self.radioCountry)
        self.verticalLayout.addWidget(self.groupBoxSearchType)

        # Label and field for search criteria.
        self.labelSearch = QtWidgets.QLabel(self.tr("Search Criteria:"), self)
        self.verticalLayout.addWidget(self.labelSearch)
        self.lineEditSearch = QtWidgets.QLineEdit(self)
        self.lineEditSearch.setPlaceholderText(
            self.tr("Enter satellite name, country code (e.g., US), or leave empty for active satellites")
        )
        self.verticalLayout.addWidget(self.lineEditSearch)

        # Search button.
        self.pushButtonSearch = QtWidgets.QPushButton(self.tr("Search"), self)
        self.verticalLayout.addWidget(self.pushButtonSearch)

        # Table for displaying search results.
        self.tableResult = QtWidgets.QTableWidget(self)
        self.tableResult.setColumnCount(3)
        self.tableResult.setHorizontalHeaderLabels([self.tr("NORAD ID"), self.tr("Name"), self.tr("Country")])
        self.tableResult.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tableResult.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableResult.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout.addWidget(self.tableResult)

        # OK and Cancel buttons.
        self.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.verticalLayout.addWidget(self.buttonBox)

        # Connect signals to slots.
        self.pushButtonSearch.clicked.connect(self.perform_search)
        self.buttonBox.accepted.connect(self.on_accept)
        self.buttonBox.rejected.connect(self.reject)
        self.tableResult.itemSelectionChanged.connect(self.on_selection_changed)

    def perform_search(self):
        """
        Perform a search based on the selected search type and criteria.
        Display the results in the table, and log key events via the callback.
        """
        # Log the beginning of search.
        if self.log_callback:
            self.log_callback(self.tr("Starting satellite search..."))

        search_text = self.lineEditSearch.text().strip()
        self.tableResult.setRowCount(0)  # Clear previous results

        try:
            # Determine which search method to use based on the selected radio button.
            if self.radioName.isChecked():
                if not search_text:
                    QtWidgets.QMessageBox.warning(
                        self, self.tr("Error"), self.tr("Please enter a satellite name.")
                    )
                    if self.log_callback:
                        self.log_callback(self.tr("Satellite name was not provided for search."))
                    return
                results = self.client.search_by_name(search_text)
            elif self.radioActive.isChecked():
                results = self.client.get_active_satellites(limit=100)
            elif self.radioCountry.isChecked():
                if not search_text:
                    QtWidgets.QMessageBox.warning(
                        self, self.tr("Error"), self.tr("Please enter a country code (e.g., US).")
                    )
                    if self.log_callback:
                        self.log_callback(self.tr("Country code was not provided for search."))
                    return
                results = self.client.search_by_country(search_text)
            else:
                results = []

            # Log the number of results found.
            if self.log_callback:
                self.log_callback(
                    self.tr("Found {0} results.").format(len(results) if results else 0))

            if not results:
                self.tableResult.setRowCount(1)
                self.tableResult.setItem(0, 0, QtWidgets.QTableWidgetItem(self.tr("No results")))
                return

            # Populate the table with search results.
            for item in results:
                self.add_result_row(str(item.get('norad_id', '')), item.get('name', ''), item.get('country', ''))

        except Exception as e:
            error_message = self.tr("Search error: ") + str(e)
            QtWidgets.QMessageBox.critical(self, self.tr("Error"), error_message)
            if self.log_callback:
                self.log_callback(error_message)

    def add_result_row(self, norad_id, name, country):
        """
        Add a row to the result table.

        :param norad_id: Satellite NORAD ID.
        :param name: Satellite name.
        :param country: Satellite country code.
        """
        row = self.tableResult.rowCount()
        self.tableResult.insertRow(row)
        self.tableResult.setItem(row, 0, QtWidgets.QTableWidgetItem(norad_id))
        self.tableResult.setItem(row, 1, QtWidgets.QTableWidgetItem(name))
        self.tableResult.setItem(row, 2, QtWidgets.QTableWidgetItem(country))
        # Log the addition of each result row.
        if self.log_callback:
            self.log_callback(
                self.tr("Added result row: NORAD ID {0}, Name {1}, Country {2}").format(norad_id, name, country)
            )

    def on_selection_changed(self):
        """
        Update the selected NORAD ID based on the current table selection.
        """
        selected_items = self.tableResult.selectedItems()
        if selected_items:
            self.selected_norad_id = selected_items[0].text()
            if self.log_callback:
                self.log_callback(
                    self.tr("Selected satellite NORAD ID: {0}").format(self.selected_norad_id)
                )

    def on_accept(self):
        """
        Accept the dialog if a satellite has been selected;
        otherwise, show a warning message.
        """
        if self.selected_norad_id:
            if self.log_callback:
                self.log_callback(self.tr("Satellite {0} selected; accepting dialog.").format(self.selected_norad_id))
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self, self.tr("Error"), self.tr("Please select a satellite from the list.")
            )
            if self.log_callback:
                self.log_callback(self.tr("No satellite selected; dialog not accepted."))

    def get_selected_norad_id(self):
        """
        Return the selected NORAD ID.

        :return: The NORAD ID of the selected satellite.
        """
        return self.selected_norad_id
