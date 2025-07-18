# -*- coding: utf-8 -*-
import os
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (
    QDialog, QFileDialog, QDialogButtonBox
)
from PyQt5.QtCore import QUrl
from .Space_trace_dialog_class import SpaceTracePluginDialogBase

class SpaceTracePluginDialog(SpaceTracePluginDialogBase):
    """Logic implementation for Space Trace Tool dialog."""

    def __init__(self, parent=None, translator=None):
        super().__init__(parent, translator)
        self._connect_signals()
        self.retranslate_ui()
        self._load_help_content()

    def _connect_signals(self):
        """Connect UI signals to slots."""
        self.radioLocalFile.toggled.connect(self._on_toggle_data_source)
        self.radioSpaceTrack.toggled.connect(self._on_toggle_data_source)
        self.checkBoxSaveData.toggled.connect(self._on_toggle_save_data)
        self.pushButtonBrowseData.clicked.connect(self._on_browse_data_file)
        self.pushButtonBrowseOutput.clicked.connect(self._on_browse_output_file)
        self.pushButtonBrowseSaveData.clicked.connect(self._on_browse_save_data)
        self.pushButtonSearchSatellites.clicked.connect(self._on_open_space_track_dialog)

        # Quick duration buttons
        durations = {"1 hour": 1.0, "1 day": 24.0, "1 week": 168.0}
        for label, hours in durations.items():
            btn = getattr(self, f"quickButton_{label.replace(' ', '_')}")
            btn.clicked.connect(lambda _, h=hours: self.spinBoxDuration.setValue(h))

    def _load_help_content(self):
        """Load help.html into help browser or show missing message."""
        ui_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        help_path = os.path.join(ui_dir, "help.html")
        if os.path.exists(help_path):
            with open(help_path, "r", encoding="utf-8") as f:
                html = f.read()
            self.textBrowserHelp.setHtml(html)
        else:
            self.textBrowserHelp.setPlainText("Help file not found.")
        self.textBrowserHelp.setOpenLinks(False)
        self.textBrowserHelp.anchorClicked.connect(self._open_link_in_browser)

    def _open_link_in_browser(self, url: QUrl):
        """Handle anchor clicks: scroll to anchor in widget for #links, open browser for external links."""
        url_str = url.toString()
        if url_str.startswith('#') or (not url.isRelative() and url.scheme() == ''):
            # Internal anchor: scroll inside QTextBrowser
            self.textBrowserHelp.setSource(url)
        elif url_str.startswith('http') or url_str.startswith('mailto:'):
            # External link: open in browser
            import webbrowser
            webbrowser.open(url_str)
        else:
            # Fallback: try to scroll in widget
            self.textBrowserHelp.setSource(url)

    def _on_toggle_data_source(self):
        """Show or hide UI groups based on selected data source."""
        use_local = self.radioLocalFile.isChecked()
        self.groupBoxLocalFile.setVisible(use_local)
        self.groupBoxLocalFile.setEnabled(use_local)
        self.groupBoxSpaceTrack.setVisible(not use_local)
        self.groupBoxSpaceTrack.setEnabled(not use_local)
        self.groupBoxSaveData.setVisible(not use_local)
        self.groupBoxSaveData.setEnabled(not use_local)

    def _on_toggle_save_data(self):
        """Enable or disable save-data path inputs."""
        enabled = self.checkBoxSaveData.isChecked()
        self.lineEditSaveDataPath.setEnabled(enabled)
        self.pushButtonBrowseSaveData.setEnabled(enabled)

    def _on_browse_data_file(self):
        """Select input data file(s) (TLE or JSON)."""
        fmt = (self.comboBoxDataFormatLocal.currentText()
               if self.radioLocalFile.isChecked()
               else self.comboBoxDataFormatSpaceTrack.currentText())
        filter_ = "Text Files (*.txt)" if fmt == "TLE" else "JSON Files (*.json)"
        
        # Allow multiple file selection for local files
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("Select Data File(s)"),
            "",
            filter_
        )
        if paths:
            # Join multiple paths with semicolon separator
            self.lineEditDataPath.setText(";".join(paths))

    def _on_browse_output_file(self):
        """Select output path for layer(s), handling multiple IDs or files."""

        data_source_local = self.radioLocalFile.isChecked()
        if data_source_local:
            data_file_path = self.lineEditDataPath.text().strip()
            num_items = len([path.strip() for path in data_file_path.split(';') if path.strip()]) if data_file_path else 1
        else:
            sat_ids = self._parse_satellite_ids(self.lineEditSatID.text())
            num_items = len(sat_ids) if sat_ids else 1

        if num_items > 1:
            directory = QFileDialog.getExistingDirectory(
                self,
                self.tr("Select Folder to Save Layers"),
                ""
            )
            if directory:
                fmt = self._show_format_selection_dialog()
                if fmt:
                    self.lineEditOutputPath.setText(f"{directory}|{fmt}")
        else:
        
            path, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("Select Output File"),
                "",
                "Shapefiles (*.shp);;GeoPackage (*.gpkg);;GeoJSON (*.geojson);;All Files (*)"
            )
            if path:
                self.lineEditOutputPath.setText(path)

    def _show_format_selection_dialog(self) -> str:
        """Show dialog for selecting folder export format; return chosen format."""
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Select Output Format"))
        layout = QtWidgets.QVBoxLayout(dlg)
        layout.addWidget(QtWidgets.QLabel(self.tr("Select format for saving layers:")))
        combo = QtWidgets.QComboBox(dlg)
        combo.addItems(["shp", "gpkg", "geojson"])
        layout.addWidget(combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dlg)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        return combo.currentText() if dlg.exec_() == QDialog.Accepted else ""

    def _on_browse_save_data(self):
        """Select save path for downloaded data, file or folder based on mode."""
        fmt = (self.comboBoxDataFormatLocal.currentText()
               if self.radioLocalFile.isChecked()
               else self.comboBoxDataFormatSpaceTrack.currentText())
        ext = ".txt" if fmt == "TLE" else ".json"

        if self.checkBoxSaveData.isChecked() and self.radioSpaceTrack.isChecked():
            directory = QFileDialog.getExistingDirectory(
                self,
                self.tr("Select Folder to Save Data"),
                ""
            )
            if directory:
                self.lineEditSaveDataPath.setText(directory)
        else:
            path, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("Select Save Path"),
                "",
                f"{fmt} (*{ext})"
            )
            if path:
                if not path.lower().endswith(ext):
                    path += ext
                self.lineEditSaveDataPath.setText(path)

    def _on_open_space_track_dialog(self):
        """Open SpaceTrack API dialog and update satellite ID field."""
        from ..spacetrack_dialog.spacetrack_dialog import SpaceTrackDialog

        login = self.lineEditLogin.text().strip()
        password = self.lineEditPassword.text().strip()
        if not login or not password:
            QtWidgets.QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("Please enter SpaceTrack login and password.")
            )
            return

        dlg = SpaceTrackDialog(self, login=login, password=password,
                               log_callback=self.appendLog, translator=self.translator)
        if dlg.exec_() == QDialog.Accepted:
            ids = sorted(int(i) for i in dlg.get_selected_norad_ids())
            self.lineEditSatID.setText(self._format_id_ranges(ids))

    def _parse_satellite_ids(self, text: str) -> list:
        """Parse comma/range-separated satellite IDs into a list of ints."""
        ids = set()
        for part in text.split(','):
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                try:
                    start, end = map(int, part.split('-', 1))
                    if start <= end:
                        ids.update(range(start, end + 1))
                except ValueError:
                    continue
            else:
                try:
                    ids.add(int(part))
                except ValueError:
                    continue
        return sorted(ids)

    def _format_id_ranges(self, ids: list) -> str:
        """Convert sorted list of ints into comma-/dash-separated string."""
        if not ids:
            return ""
        ranges, start, prev = [], ids[0], ids[0]
        for curr in ids[1:] + [None]:
            if curr is None or curr > prev + 1:
                ranges.append(f"{start}-{prev}" if start != prev else str(start))
                if curr is not None:
                    start = curr
            prev = curr if curr is not None else prev
        return ",".join(ranges)

    def appendLog(self, message: str):
        """Append a line to the log text box."""
        self.textEditLog.append(message)

    def switch_to_log_tab(self):
        """Switch programmatically to the Log tab."""
        idx = self.tabWidget.indexOf(self.tabLog)
        self.tabWidget.setCurrentIndex(idx)

    def get_inputs(self) -> dict:
        """Collect current dialog values into a dictionary."""
        data_source_local = self.radioLocalFile.isChecked()
        save_data = self.checkBoxSaveData.isChecked()
        
        # Handle multiple file paths for local files
        data_file_path = self.lineEditDataPath.text().strip()
        if data_source_local and data_file_path:
            # Split multiple file paths by semicolon
            data_file_paths = [path.strip() for path in data_file_path.split(';') if path.strip()]
        else:
            data_file_paths = [data_file_path] if data_file_path else []
        
        return {
            "data_file_paths": data_file_paths,  # List of file paths for local files
            "data_file_path": data_file_path,    # Original single path (for backward compatibility)
            "sat_id_text": self.lineEditSatID.text().strip(),
            "start_datetime": self.dateTimeEdit.dateTime().toPyDateTime(),
            "duration_hours": self.spinBoxDuration.value(),
            "step_minutes": self.spinBoxStepMinutes.value(),
            "output_path": self.lineEditOutputPath.text().strip(),
            "add_layer": self.checkBoxAddLayer.isChecked(),
            "login": "" if data_source_local else self.lineEditLogin.text().strip(),
            "password": "" if data_source_local else self.lineEditPassword.text().strip(),
            "data_format": (
                self.comboBoxDataFormatLocal.currentText()
                if data_source_local
                else self.comboBoxDataFormatSpaceTrack.currentText()
            ),
            "create_line_layer": self.checkBoxCreateLineLayer.isChecked(),
            "save_data": save_data,
            "save_data_path": self.lineEditSaveDataPath.text().strip() if save_data else ""
        }
