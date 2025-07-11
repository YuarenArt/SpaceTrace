# -*- coding: utf-8 -*-
import os
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (
    QDialog, QGroupBox, QRadioButton, QButtonGroup,
    QDialogButtonBox, QPushButton, QTextBrowser, QFileDialog
)

from PyQt5.QtCore import QUrl
import webbrowser

from ..spacetrack_dialog.spacetrack_dialog import SpaceTrackDialog
from .Space_trace_dialog_class import SpaceTracePluginDialogBase

class SpaceTracePluginDialog(SpaceTracePluginDialogBase):
    """Logic implementation for Space Trace Tool dialog."""
    
    def __init__(self, parent=None, translator=None):
        super().__init__(parent, translator)
        self._connect_signals()
        self.retranslate_ui()
        self._load_help_content()

    def _connect_signals(self):
        """Connect all signals to their respective slots."""
        self.radioLocalFile.toggled.connect(self.toggle_data_source)
        self.radioSpaceTrack.toggled.connect(self.toggle_data_source)
        self.checkBoxSaveData.toggled.connect(self.toggle_save_data_path)
        self.pushButtonBrowseData.clicked.connect(self.browseDataFile)
        self.pushButtonBrowseOutput.clicked.connect(self.browseOutputFile)
        self.pushButtonBrowseSaveData.clicked.connect(self.browseSaveDataFile)
        self.pushButtonSearchSatellites.clicked.connect(self.open_space_track_dialog)
        
        # Connect quick duration buttons
        for text, hrs in [("1 hour", 1.0), ("1 day", 24.0), ("1 week", 168.0)]:
            btn = getattr(self, f"quickButton_{text.replace(' ', '_')}")
            btn.clicked.connect(lambda _, h=hrs: self.spinBoxDuration.setValue(h))

    def _load_help_content(self):
        """Load 'readme.html' into the help tab, or show error if missing."""
        ui_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        help_file = os.path.join(ui_dir, "help.html")
        if os.path.exists(help_file):
            with open(help_file, "r", encoding="utf-8") as f:
                self.textBrowserHelp.setHtml(f.read())
        else:
            self.textBrowserHelp.setPlainText("Help file not found.")

        self.textBrowserHelp.setOpenLinks(False)
        self.textBrowserHelp.setOpenExternalLinks(False)

    def _open_link_in_browser(self, url: QUrl):
        webbrowser.open(url.toString())
        self.textBrowserHelp.setSource(QtCore.QUrl())

    def toggle_data_source(self):
        """Enable/disable and show/hide groups based on data source selection."""
        if self.radioLocalFile.isChecked():
            self.groupBoxLocalFile.setEnabled(True)
            self.groupBoxLocalFile.show()
            self.groupBoxSpaceTrack.setEnabled(False)
            self.groupBoxSpaceTrack.hide()
            self.groupBoxSaveData.setEnabled(False)
            self.groupBoxSaveData.hide()
        else:
            self.groupBoxLocalFile.setEnabled(False)
            self.groupBoxLocalFile.hide()
            self.groupBoxSpaceTrack.setEnabled(True)
            self.groupBoxSpaceTrack.show()
            self.groupBoxSaveData.setEnabled(True)
            self.groupBoxSaveData.show()

    def toggle_save_data_path(self):
        """Enable/disable save path widgets when saving data."""
        enabled = self.checkBoxSaveData.isChecked()
        self.lineEditSaveDataPath.setEnabled(enabled)
        self.pushButtonBrowseSaveData.setEnabled(enabled)

    def browseDataFile(self):
        """Open file dialog to select data file (TLE or JSON)."""
        fmt = self.comboBoxDataFormatLocal.currentText() if self.radioLocalFile.isChecked() else self.comboBoxDataFormatSpaceTrack.currentText()
        filter_ = "Text Files (*.txt)" if fmt == "TLE" else "JSON Files (*.json)"
        file, _ = QFileDialog.getOpenFileName(
            self,
            QtCore.QCoreApplication.translate("SpaceTracePluginDialog", "Select Data File"),
            "",
            filter_
        )
        if file:
            self.lineEditDataPath.setText(file)

    def browseOutputFile(self):
        """Open file dialog to choose where to save the output layer."""
        sat_id_text = self.lineEditSatID.text().strip()
        multiple_ids = False
        if sat_id_text:
            ids = set()
            parts = [p.strip() for p in sat_id_text.split(',') if p.strip()]
            for part in parts:
                if '-' in part:
                    try:
                        start, end = part.split('-')
                        start_i, end_i = int(start), int(end)
                        if start_i > end_i:
                            continue
                        ids.update(range(start_i, end_i + 1))
                    except Exception:
                        continue
                else:
                    try:
                        ids.add(int(part))
                    except Exception:
                        continue
            multiple_ids = len(ids) > 1

        if multiple_ids:
            directory = QFileDialog.getExistingDirectory(
                self,
                QtCore.QCoreApplication.translate("SpaceTracePluginDialog", "Select Folder to Save Layers"),
                ""
            )
            if directory:
                # Показываем диалог для выбора формата
                format_dialog = QtWidgets.QDialog(self)
                format_dialog.setWindowTitle("Select Output Format")
                layout = QtWidgets.QVBoxLayout(format_dialog)
                label = QtWidgets.QLabel("Select format for saving layers:", format_dialog)
                layout.addWidget(label)
                combo = QtWidgets.QComboBox(format_dialog)
                combo.addItems(["shp", "gpkg", "geojson"])
                layout.addWidget(combo)
                btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, format_dialog)
                layout.addWidget(btns)
                btns.accepted.connect(format_dialog.accept)
                btns.rejected.connect(format_dialog.reject)
                if format_dialog.exec_() == QtWidgets.QDialog.Accepted:
                    fmt = combo.currentText()
                    # Сохраняем путь и формат через разделитель (например, 'C:/folder|shp')
                    self.lineEditOutputPath.setText(f"{directory}|{fmt}")
        else:
            file, _ = QFileDialog.getSaveFileName(
                self,
                QtCore.QCoreApplication.translate("SpaceTracePluginDialog", "Select Output File"),
                "",
                "Shapefiles (*.shp);;GeoPackage (*.gpkg);;GeoJSON (*.geojson);;All Files (*)"
            )
            if file:
                self.lineEditOutputPath.setText(file)

    def browseSaveDataFile(self):
        """Open file/folder dialog depending on data format and save mode."""
        fmt = self.comboBoxDataFormatLocal.currentText() if self.radioLocalFile.isChecked() else self.comboBoxDataFormatSpaceTrack.currentText()

        # Determine file extension and filter
        if fmt == "TLE":
            filter_, ext = "Text Files (*.txt)", ".txt"
        else:
            filter_, ext = "JSON Files (*.json)", ".json"

        # Determine whether it's a batch save operation
        if self.checkBoxSaveData.isChecked() and self.radioSpaceTrack.isChecked():
            # Multiple satellites => use folder selection
            directory = QFileDialog.getExistingDirectory(
                self,
                QtCore.QCoreApplication.translate("SpaceTracePluginDialog", "Select Folder to Save Data"),
                ""
            )
            if directory:
                self.lineEditSaveDataPath.setText(directory)
        else:
            # Single file save
            file, _ = QFileDialog.getSaveFileName(
                self,
                QtCore.QCoreApplication.translate("SpaceTracePluginDialog", "Select Save Path"),
                "",
                filter_
            )
            if file:
                if not file.lower().endswith(ext):
                    file += ext
                self.lineEditSaveDataPath.setText(file)

    def open_space_track_dialog(self):
        """Open the SpaceTrack API search dialog and pass selected IDs as list or range."""
        login = self.lineEditLogin.text().strip()
        password = self.lineEditPassword.text().strip()
        if not login or not password:
            QtWidgets.QMessageBox.warning(
                self,
                QtCore.QCoreApplication.translate("SpaceTracePluginDialog", "Error"),
                QtCore.QCoreApplication.translate("SpaceTracePluginDialog", "Please enter SpaceTrack login and password.")
            )
            return

        dlg = SpaceTrackDialog(self, login=login, password=password, 
                            log_callback=self.appendLog, translator=self.translator)
        if dlg.exec_() == QDialog.Accepted:
            norad_list = dlg.get_selected_norad_ids()
            if norad_list:
                # Convert list of strings to sorted list of ints
                ids_int = sorted(int(i) for i in norad_list)
                
                # Group consecutive IDs into ranges
                ranges = []
                start = ids_int[0]
                prev = start
                
                for current in ids_int[1:] + [None]:  # Add None as sentinel
                    if current is None or current > prev + 1:
                        # End of a range or sequence
                        if start == prev:
                            ranges.append(str(start))  # Single ID
                        else:
                            ranges.append(f"{start}-{prev}")  # Range
                        if current is not None:
                            start = current
                    prev = current if current is not None else prev
                
                # Join ranges and single IDs with commas
                text = ",".join(ranges)
                
                # Set combined text into the main dialog
                self.lineEditSatID.setText(text)

    def appendLog(self, message):
        """Append a line to the log text box."""
        self.textEditLog.append(message)

    def switch_to_log_tab(self):
        """Programmatically switch to the Log tab."""
        self.tabWidget.setCurrentIndex(self.tabWidget.indexOf(self.tabLog))

    def get_inputs(self):
        """Gather all current user inputs into a dict for processing."""
        return {
            "data_file_path": self.lineEditDataPath.text().strip() if self.radioLocalFile.isChecked() else "",
            "sat_id_text": self.lineEditSatID.text().strip(),
            "start_datetime": self.dateTimeEdit.dateTime().toPyDateTime(),
            "duration_hours": self.spinBoxDuration.value(),
            "step_minutes": self.spinBoxStepMinutes.value(),
            "output_path": self.lineEditOutputPath.text().strip(),
            "add_layer": self.checkBoxAddLayer.isChecked(),
            "login": self.lineEditLogin.text().strip() if not self.radioLocalFile.isChecked() else "",
            "password": self.lineEditPassword.text().strip() if not self.radioLocalFile.isChecked() else "",
            "data_format": (
                self.comboBoxDataFormatLocal.currentText() if self.radioLocalFile.isChecked()
                else self.comboBoxDataFormatSpaceTrack.currentText()
            ),
            "create_line_layer": self.checkBoxCreateLineLayer.isChecked(),
            "save_data": self.checkBoxSaveData.isChecked(),
            "save_data_path": self.lineEditSaveDataPath.text().strip() if self.checkBoxSaveData.isChecked() else ""
        }