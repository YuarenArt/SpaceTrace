# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QApplication, QMessageBox
from qgis.core import QgsVectorLayer, QgsProject

import os.path
import time
from datetime import datetime
import logging

from ...resources import *
from .Space_trace_dialog import SpaceTracePluginDialog
from .orbital.facade import OrbitalTrackFacade
from ..config.orbital import OrbitalConfig
from ..data_retriver.data_retriver import LocalFileRetriever
from ..data_retriver.spacetrack_retriver import SpaceTrackRetriever


class SpaceTracePlugin:
    """
    QGIS Plugin for generating orbital tracks.

    Handles user interface operations and delegates core orbital track creation to OrbitalTrackFacade.
    """
    
    def __init__(self, iface):
        """
        Initialize the Space Trace Plugin.

        Args:
            iface: QGIS interface instance.
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.actions = []
        self.menu = self.tr('Space trace')
        self.first_start = True
        self.dlg = None
        self.logger = None
        self.translator = None

        self._init_logger()
        self._init_localization()
        self.logger.info("SpaceTracePlugin initialized.")

    def _init_logger(self):
        """Initialize the file logger for the plugin."""
        self.logger = logging.getLogger("SpaceTracePlugin")
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            log_file = os.path.join(self.plugin_dir, "SpaceTracePlugin.log")
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.propagate = False

    def _init_localization(self):
        """Initialize localization settings for the plugin."""
        locale = QSettings().value('locale/userLocale', 'en')[:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'SpaceTracePlugin_{locale}.qm')
        
        self.logger.debug(f"Detected locale: {locale}")
        self.logger.debug(f"Expected translation file path: {locale_path}")

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            if self.translator.load(locale_path):
                QCoreApplication.installTranslator(self.translator)
                self.logger.debug(f"Successfully loaded translation file: {locale_path}")
            else:
                self.logger.warning(f"Failed to load translation file: {locale_path}")
        else:
            self.logger.warning(f"Translation file does not exist: {locale_path}")

    def tr(self, message: str) -> str:
        """
        Translate a message using Qt translation API.

        Args:
            message (str): Message to translate.

        Returns:
            str: Translated message.
        """
        return QCoreApplication.translate('SpaceTracePlugin', message)

    def _add_action(self, icon_path: str, text: str, callback, parent, 
                    enabled: bool = True, add_to_menu: bool = True, add_to_toolbar: bool = True,
                    status_tip: str = None, whats_this: str = None) -> QAction:
        """
        Add an action to the QGIS toolbar and/or menu.

        Args:
            icon_path (str): Path to the action icon.
            text (str): Text for the action.
            callback: Callback function for the action.
            parent: Parent widget for the action.
            enabled (bool): Whether the action is enabled.
            add_to_menu (bool): Add action to menu.
            add_to_toolbar (bool): Add action to toolbar.
            status_tip (str): Status tip for the action.
            whats_this (str): What's this help text.

        Returns:
            QAction: Created action.
        """
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled)
        if status_tip:
            action.setStatusTip(status_tip)
        if whats_this:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToVectorMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        """Initialize the GUI by adding menu entries and toolbar icons."""
        icon_path = ':/plugins/Space_trace/icon.png'
        self._add_action(
            icon_path=icon_path,
            text=self.tr('Draw flight path'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )

    def unload(self):
        """Remove plugin menu items and icons from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.tr('&Space trace'), action)
            self.iface.removeToolBarIcon(action)
        self._close_logger()

    def _close_logger(self):
        """Close all logger handlers."""
        if self.logger:
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)

    def log_message(self, message: str, level: str = "INFO"):
        """
        Log a message to file and UI log window.

        Args:
            message (str): Message to log.
            level (str): Log level ("INFO", "DEBUG", "WARNING", "ERROR").
        """
        level = level.upper()
        log_functions = {
            "DEBUG": self.logger.debug,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "INFO": self.logger.info
        }
        log_functions.get(level, self.logger.info)(message)

        if self.dlg and level in ["INFO", "WARNING", "ERROR"]:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.dlg.appendLog(f"[{timestamp}] {message}")
        QApplication.processEvents()

    def _parse_norad_ids(self, text: str) -> list:
        """
        Parse NORAD IDs from input text (single, comma-separated, or ranges).

        Args:
            text (str): Input string with NORAD IDs.

        Returns:
            list: Sorted list of NORAD IDs.

        Raises:
            ValueError: If a range is invalid.
        """
        ids = set()
        for part in [p.strip() for p in text.split(',') if p.strip()]:
            if '-' in part:
                start, end = map(int, part.split('-'))
                if start > end:
                    raise ValueError(f"Invalid range {part}")
                ids.update(range(start, end + 1))
            else:
                ids.add(int(part))
        return sorted(ids)

    def _validate_inputs(self, inputs: dict) -> tuple[list, str, str]:
        """
        Validate user inputs and extract satellite IDs, file format, and output path.

        Args:
            inputs (dict): User inputs from the dialog.

        Returns:
            tuple: (satellite IDs, file format, output path).

        Raises:
            Exception: If inputs are invalid.
        """
        if not inputs["data_file_paths"]:
            if not inputs["sat_id_text"]:
                raise Exception(self.tr("Please enter at least one NORAD ID."))
            try:
                sat_ids = self._parse_norad_ids(inputs["sat_id_text"])
            except ValueError as e:
                raise Exception(self.tr(f"Invalid NORAD ID format: {str(e)}"))
            if not inputs["login"] or not inputs["password"]:
                raise Exception(self.tr("Please provide SpaceTrack login and password."))
        else:
            # For local files, create a list of file indices (0, 1, 2, ...)
            # Each index will be used to identify the file in processing
            sat_ids = list(range(len(inputs["data_file_paths"])))
            
            # Validate each file exists and is readable
            for i, file_path in enumerate(inputs["data_file_paths"]):
                if not os.path.isfile(file_path):
                    raise Exception(self.tr(f"Local data file {i+1} does not exist or is not readable: {file_path}"))

        output_path = inputs["output_path"]
        file_format = None
        if output_path and '|' in output_path:
            directory, fmt = output_path.split('|', 1)
            directory = directory.strip()
            fmt = fmt.strip().lower()
            if fmt not in {"shp", "gpkg", "geojson"}:
                raise Exception(self.tr("Unsupported file format. Use .shp, .gpkg, or .geojson."))
            if not os.path.isdir(directory):
                raise Exception(self.tr("Output directory does not exist or is not writable."))
            output_path = directory
            file_format = fmt
        elif output_path:
            _, ext = os.path.splitext(output_path)
            fmt = ext[1:].lower()
            if fmt not in {"shp", "gpkg", "geojson"}:
                raise Exception(self.tr("Unsupported file format. Use .shp, .gpkg, or .geojson."))
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.isdir(output_dir):
                raise Exception(self.tr("Output directory does not exist or is not writable."))
            file_format = fmt

        if inputs["save_data"] and inputs["save_data_path"]:
            save_dir = os.path.dirname(inputs["save_data_path"])
            if save_dir and not os.path.isdir(save_dir):
                raise Exception(self.tr("Save data directory does not exist or is not writable."))

        return sat_ids, file_format, output_path

    def _create_config(self, inputs: dict, sat_id: int, file_format: str) -> OrbitalConfig:
        """
        Create OrbitalConfig for a satellite based on inputs.

        Args:
            inputs (dict): User inputs from the dialog.
            sat_id (int): Satellite NORAD ID (for SpaceTrack) or file index (for local files).
            file_format (str): Output file format.

        Returns:
            OrbitalConfig: Configuration object for orbital track processing.
        """
        # Determine if we're processing local files or SpaceTrack data
        is_local_files = bool(inputs["data_file_paths"])
        
        if is_local_files:
            # For local files, sat_id is the file index
            file_index = sat_id
            file_path = inputs["data_file_paths"][file_index]
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            save_data_path = inputs['save_data_path']
            if inputs['save_data'] and save_data_path and os.path.isdir(save_data_path):
                save_data_path = os.path.join(save_data_path, f"{base_name}.{inputs['data_format'].lower()}")

            output_path = inputs['output_path']
            if output_path and '|' in output_path:
                output_path = output_path.split('|', 1)[0].strip()

            if output_path and os.path.isdir(output_path):
                output_path = os.path.join(output_path, f"{base_name}_points.{file_format}")

            return OrbitalConfig(
                sat_id=file_index,  # Use file index as sat_id for local files
                start_datetime=inputs['start_datetime'],
                duration_hours=inputs['duration_hours'],
                step_minutes=inputs['step_minutes'],
                output_path=output_path,
                file_format=file_format,
                add_layer=inputs['add_layer'],
                login=None,  # No login needed for local files
                password=None,  # No password needed for local files
                data_format=inputs['data_format'],
                create_line_layer=inputs['create_line_layer'],
                save_data=inputs['save_data'],
                data_file_path=file_path,  # Use specific file path
                save_data_path=save_data_path
            )
        else:
            # For SpaceTrack, sat_id is the actual NORAD ID
            save_data_path = inputs['save_data_path']
            if inputs['save_data'] and save_data_path and os.path.isdir(save_data_path):
                save_data_path = os.path.join(save_data_path, f"{sat_id}.tle")

            output_path = inputs['output_path']
            if output_path and '|' in output_path:
                output_path = output_path.split('|', 1)[0].strip()

            if output_path and os.path.isdir(output_path):
                base_name = f"sat_{sat_id}_points"
                output_path = os.path.join(output_path, f"{base_name}.{file_format}")

            return OrbitalConfig(
                sat_id=sat_id,
                start_datetime=inputs['start_datetime'],
                duration_hours=inputs['duration_hours'],
                step_minutes=inputs['step_minutes'],
                output_path=output_path,
                file_format=file_format,
                add_layer=inputs['add_layer'],
                login=inputs['login'] or None,
                password=inputs['password'] or None,
                data_format=inputs['data_format'],
                create_line_layer=inputs['create_line_layer'],
                save_data=inputs['save_data'],
                data_file_path=inputs['data_file_path'],
                save_data_path=save_data_path
            )

    def _load_and_add_layer(self, file_path: str, layer_type: str):
        """
        Load a vector layer and add it to the QGIS project.

        Args:
            file_path (str): Path to the layer file.
            layer_type (str): Type of layer ("point" or "line").
        """
        if not file_path:
            return
        layer_name = os.path.splitext(os.path.basename(file_path))[0]
        layer = QgsVectorLayer(file_path, layer_name, "ogr")
        if not layer.isValid():
            self.log_message(f"Failed to load {layer_type} layer from {file_path}.", "ERROR")
            self.iface.messageBar().pushMessage("Error", f"Failed to load {layer_type} layer", level=3)
        else:
            QgsProject.instance().addMapLayer(layer)
            self.log_message(f"{layer_type.capitalize()} layer loaded with {layer.featureCount()} features.", "INFO")

    def _process_track(self, config: OrbitalConfig, facade: OrbitalTrackFacade):
        """
        Process an orbital track for a given configuration.

        Args:
            config (OrbitalConfig): Configuration for track processing.
            facade (OrbitalTrackFacade): Facade for track generation.
        """
        if config.output_path:
            point_file, line_file = facade.process_persistent_track(config)
            self.log_message(f"Files created: Point={point_file}, Line={line_file}", "INFO")
            self.iface.messageBar().pushMessage(
                self.tr("Success"),
                self.tr(f"{config.file_format.capitalize()} created successfully"),
                level=0
            )
            self._load_and_add_layer(point_file, "point")
            self._load_and_add_layer(line_file, "line")
        else:
            point_layer, line_layer = facade.process_in_memory_track(config)
            if config.add_layer:
                QgsProject.instance().addMapLayer(point_layer)
                QgsProject.instance().addMapLayer(line_layer)
                self.log_message(f"Temporary layers added to the project.", "INFO")
                self.log_message(f"Temporary Point layer contains {point_layer.featureCount()} features.", "INFO")
            self.iface.messageBar().pushMessage(
                self.tr("Success"),
                self.tr("Temporary layers created successfully"),
                level=0
            )

    def _process_satellites(self, sat_ids: list, inputs: dict, file_format: str, output_path: str):
        """
        Process orbital tracks for all satellites or local files.

        Args:
            sat_ids (list): List of NORAD IDs (for SpaceTrack) or file indices (for local files).
            inputs (dict): User inputs.
            file_format (str): Output file format.
            output_path (str): Output path or directory.

        Returns:
            tuple: Lists of successful and failed satellite IDs or file indices.
        """
        is_local_files = bool(inputs["data_file_paths"])
        multiple_items = len(sat_ids) > 1
        
        if multiple_items and output_path and not os.path.isdir(output_path):
            item_type = "files" if is_local_files else "satellites"
            raise Exception(self.tr(f"When saving multiple {item_type}, 'Output path' must be a directory."))
        if multiple_items and inputs["save_data"] and not os.path.isdir(inputs["save_data_path"]):
            item_type = "files" if is_local_files else "satellites"
            raise Exception(self.tr(f"When saving multiple {item_type}, 'Save data path' must be a valid directory."))

        retriever = (
            LocalFileRetriever(log_callback=self.log_message) if is_local_files
            else SpaceTrackRetriever(inputs["login"], inputs["password"], log_callback=self.log_message)
        )
        facade = OrbitalTrackFacade(retriever, log_callback=self.log_message)
        self.log_message("OrbitalTrackFacade initialized", "DEBUG")

        successful_items, failed_items = [], []
        for item_id in sat_ids:
            try:
                config = self._create_config(inputs, item_id, file_format)
                
                if is_local_files:
                    file_path = inputs["data_file_paths"][item_id]
                    file_name = os.path.basename(file_path)
                    self.log_message(f"Processing file {item_id+1}/{len(sat_ids)}: {file_name}", "INFO")
                else:
                    self.log_message(f"Processing NORAD ID={item_id}", "INFO")
                
                self._process_track(config, facade)
                successful_items.append(item_id)
                
                if is_local_files:
                    file_path = inputs["data_file_paths"][item_id]
                    file_name = os.path.basename(file_path)
                    self.log_message(f"Successfully processed file: {file_name}", "INFO")
                else:
                    self.log_message(f"Successfully processed NORAD ID={item_id}", "INFO")
                    
            except Exception as e:
                if is_local_files:
                    file_path = inputs["data_file_paths"][item_id]
                    file_name = os.path.basename(file_path)
                    self.log_message(f"Error processing file {file_name}: {str(e)}", "ERROR")
                    self.iface.messageBar().pushMessage(
                        self.tr("Warning"),
                        f"Failed to process file {file_name}: {str(e)}",
                        level=2
                    )
                else:
                    self.log_message(f"Error processing NORAD ID={item_id}: {str(e)}", "ERROR")
                    self.iface.messageBar().pushMessage(
                        self.tr("Warning"),
                        f"Failed to process satellite {item_id}: {str(e)}",
                        level=2
                    )
                failed_items.append(item_id)

        return successful_items, failed_items

    def execute_logic(self):
        """Execute the main plugin logic for generating orbital tracks."""
        self.dlg.switch_to_log_tab()
        self.log_message("Process started.")

        try:
            start_time = time.time()
            inputs = self.dlg.get_inputs()
            sat_ids, file_format, output_path = self._validate_inputs(inputs)
            successful_items, failed_items = self._process_satellites(sat_ids, inputs, file_format, output_path)

            end_time = time.time()
            duration = end_time - start_time
            total_items = len(sat_ids)
            successful_count = len(successful_items)
            failed_count = len(failed_items)
            
            is_local_files = bool(inputs["data_file_paths"])
            item_type = "files" if is_local_files else "satellites"

            self.log_message(f"Process completed in {duration:.2f} seconds.", "INFO")
            self.log_message(f"Processing summary: {successful_count}/{total_items} {item_type} processed successfully.", "INFO")

            if successful_count > 0:
                if is_local_files:
                    successful_names = [os.path.basename(inputs["data_file_paths"][i]) for i in successful_items]
                    self.log_message(f"Successfully processed files: {', '.join(successful_names)}", "INFO")
                else:
                    self.log_message(f"Successfully processed satellites: {', '.join(map(str, successful_items))}", "INFO")
                    
            if failed_count > 0:
                if is_local_files:
                    failed_names = [os.path.basename(inputs["data_file_paths"][i]) for i in failed_items]
                    self.log_message(f"Failed to process files: {', '.join(failed_names)}", "WARNING")
                else:
                    self.log_message(f"Failed to process satellites: {', '.join(map(str, failed_items))}", "WARNING")
                    
                self.iface.messageBar().pushMessage(
                    self.tr("Processing Complete"),
                    f"Processed {successful_count}/{total_items} {item_type}. {failed_count} failed.",
                    level=1
                )
            else:
                self.log_message(f"All {item_type} processed successfully.", "INFO")
                self.iface.messageBar().pushMessage(
                    self.tr("Success"),
                    f"All {total_items} {item_type} processed successfully.",
                    level=0
                )

        except Exception as e:
            self.log_message(f"Error: {str(e)}", "ERROR")
            self.iface.messageBar().pushMessage("Error", str(e), level=3)

    def run(self):
        """Launch the plugin and display the dialog."""
        if self.first_start:
            self.first_start = False
            self.dlg = SpaceTracePluginDialog(translator=self.translator)
            self.dlg.pushButtonExecute.clicked.connect(self.execute_logic)
            self.dlg.pushButtonClose.clicked.connect(self._on_close_dialog)
            self.dlg.rejected.connect(self._close_logger)
        else:
            self._init_logger()
        self.dlg.show()

    def _on_close_dialog(self):
        """Handle dialog close event."""
        self._close_logger()
        self.dlg.close()