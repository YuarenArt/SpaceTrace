# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QApplication
from qgis.core import QgsVectorLayer, QgsProject

import os.path
import time
from datetime import datetime
import logging

from ...resources import *
from .Space_trace_dialog import SpaceTracePluginDialog
from .orbital.facade import OrbitalTrackFacade
from ..config.orbital import OrbitalConfig


class SpaceTracePlugin:
    """QGIS Plugin for generating orbital tracks from local files or SpaceTrack data.

    Integrates a GUI dialog for user input and processes satellite orbital tracks using OrbitalTrackFacade.
    """

    def __init__(self, iface):
        """Initialize the plugin with QGIS interface.

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
        """Set up file logging for the plugin."""
        self.logger = logging.getLogger("SpaceTracePlugin")
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)
            log_file = os.path.join(self.plugin_dir, "SpaceTracePlugin.log")
            handler = logging.FileHandler(log_file, encoding="utf-8")
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            self.logger.addHandler(handler)
            self.logger.propagate = False

    def _init_localization(self):
        """Configure localization based on QGIS settings."""
        locale = QSettings().value('locale/userLocale', 'en')[:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'SpaceTracePlugin_{locale}.qm')

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            if self.translator.load(locale_path):
                QCoreApplication.installTranslator(self.translator)
                self.logger.debug(f"Loaded translation: {locale_path}")
            else:
                self.logger.warning(f"Failed to load translation: {locale_path}")
        else:
            self.logger.warning(f"Translation file missing: {locale_path}")

    def tr(self, message: str) -> str:
        """Translate a message using Qt's translation system.

        Args:
            message (str): Text to translate.

        Returns:
            str: Translated text.
        """
        return QCoreApplication.translate('SpaceTracePlugin', message)

    def _add_action(self, icon_path: str, text: str, callback, parent) -> QAction:
        """Add an action to the QGIS menu and toolbar.

        Args:
            icon_path (str): Path to the icon file.
            text (str): Action label.
            callback: Function to call when action is triggered.
            parent: Parent widget (usually main window).

        Returns:
            QAction: Created action object.
        """
        action = QAction(QIcon(icon_path), text, parent)
        action.triggered.connect(callback)
        action.setEnabled(True)
        self.iface.addToolBarIcon(action)
        self.iface.addPluginToVectorMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        """Set up the plugin's GUI elements."""
        icon_path = ':/plugins/Space_trace/icon.png'
        self._add_action(
            icon_path=icon_path,
            text=self.tr('Draw flight path'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )

    def unload(self):
        """Clean up GUI elements on plugin unload."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        self._close_logger()

    def _close_logger(self):
        """Close all logger handlers."""
        if self.logger:
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)

    def log_message(self, message: str, level: str = "INFO"):
        """Log a message to file and dialog.

        Args:
            message (str): Message content.
            level (str): Log level ("INFO", "DEBUG", "WARNING", "ERROR").
        """
        log_func = {
            "DEBUG": self.logger.debug,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "INFO": self.logger.info
        }.get(level.upper(), self.logger.info)
        log_func(message)

        if self.dlg and level in ["INFO", "WARNING", "ERROR"]:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.dlg.appendLog(f"[{timestamp}] {message}")
        QApplication.processEvents()

    def _parse_norad_ids(self, text: str) -> list[int]:
        """Parse NORAD IDs from a string.

        Args:
            text (str): Comma-separated IDs or ranges (e.g., "25544, 40000-40002").

        Returns:
            list[int]: Sorted list of unique NORAD IDs.

        Raises:
            ValueError: If ID format or range is invalid.
        """
        ids = set()
        for part in [p.strip() for p in text.split(',') if p.strip()]:
            if '-' in part:
                start, end = map(int, part.split('-'))
                if start > end:
                    raise ValueError(f"Invalid range: {part}")
                ids.update(range(start, end + 1))
            else:
                ids.add(int(part))
        return sorted(ids)

    def _validate_output_path(self, output_path: str, num_items: int) -> tuple[str, str]:
        """Validate and parse output path.

        Args:
            output_path (str): User-provided output path (e.g., "dir|shp" or "file.shp").
            num_items (int): Number of items to process.

        Returns:
            tuple[str, str]: (directory or file path, file format).

        Raises:
            Exception: If path or format is invalid.
        """
        if not output_path:
            return None, None

        if '|' in output_path:
            directory, fmt = output_path.split('|', 1)
            directory = directory.strip()
            fmt = fmt.strip().lower()
            if fmt not in {"shp", "gpkg", "geojson"}:
                raise Exception(self.tr("Unsupported format. Use shp, gpkg, or geojson."))
            if not os.path.isdir(directory):
                raise Exception(self.tr("Output directory does not exist or is not writable."))
            return directory, fmt

        if num_items > 1:
            output_dir = os.path.dirname(output_path)
            if not output_dir:
                output_dir = os.getcwd()
            _, ext = os.path.splitext(output_path)
            fmt = ext[1:].lower() if ext else "shp"
            if fmt not in {"shp", "gpkg", "geojson"}:
                raise Exception(self.tr("Unsupported format. Use shp, gpkg, or geojson."))
            if not os.path.isdir(output_dir):
                raise Exception(self.tr("Output directory does not exist or is not writable."))
            return output_dir, fmt

        _, ext = os.path.splitext(output_path)
        fmt = ext[1:].lower()
        if fmt not in {"shp", "gpkg", "geojson"}:
            raise Exception(self.tr("Unsupported format. Use shp, gpkg, or geojson."))
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.isdir(output_dir):
            raise Exception(self.tr("Output directory does not exist or is not writable."))
        return output_path, fmt

    def _validate_save_data_path(self, save_data_path: str, save_data: bool, num_items: int) -> None:
        """Validate save data path.

        Args:
            save_data_path (str): Path for saving data.
            save_data (bool): Whether data saving is enabled.
            num_items (int): Number of items to process.

        Raises:
            Exception: If path is invalid for the context.
        """
        if not save_data or not save_data_path:
            return

        if num_items > 1:
            if not os.path.isdir(save_data_path):
                raise Exception(self.tr("For multiple items, save data path must be a directory."))
        else:
            save_dir = os.path.dirname(save_data_path)
            if save_dir and not os.path.isdir(save_dir):
                raise Exception(self.tr("Save data directory does not exist or is not writable."))

    def _validate_inputs(self, inputs: dict) -> tuple[list[int], str, str]:
        """Validate and extract user inputs.

        Args:
            inputs (dict): User inputs from dialog.

        Returns:
            tuple[list[int], str, str]: (satellite IDs or indices, file format, output path).

        Raises:
            Exception: If inputs are invalid.
        """
        # Handle local files or SpaceTrack data
        if inputs["data_file_paths"]:
            sat_ids = list(range(len(inputs["data_file_paths"])))
            for i, file_path in enumerate(inputs["data_file_paths"]):
                if not os.path.isfile(file_path):
                    raise Exception(self.tr(f"File {i+1} is not readable: {file_path}"))
        else:
            if not inputs["sat_id_text"]:
                raise Exception(self.tr("Enter at least one NORAD ID."))
            sat_ids = self._parse_norad_ids(inputs["sat_id_text"])
            if not inputs["login"] or not inputs["password"]:
                raise Exception(self.tr("Provide SpaceTrack login and password."))

        # Validate paths
        output_path, file_format = self._validate_output_path(inputs["output_path"], len(sat_ids))
        self._validate_save_data_path(inputs["save_data_path"], inputs["save_data"], len(sat_ids))

        return sat_ids, file_format, output_path

    def _create_config_for_local_file(self, inputs: dict, file_index: int, file_format: str) -> OrbitalConfig:
        """Create config for a local file.

        Args:
            inputs (dict): User inputs.
            file_index (int): Index of the file in data_file_paths.
            file_format (str): Output file format.

        Returns:
            OrbitalConfig: Configuration object.
        """
        file_path = inputs["data_file_paths"][file_index]
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_path = inputs["output_path"]
        save_data_path = inputs["save_data_path"]

        if output_path and os.path.isdir(output_path):
            output_path = os.path.join(output_path, f"{base_name}_points.{file_format}")
        if inputs["save_data"] and save_data_path and os.path.isdir(save_data_path):
            save_data_path = os.path.join(save_data_path, f"{base_name}.{inputs['data_format'].lower()}")

        return OrbitalConfig(
            sat_id=file_index,
            start_datetime=inputs["start_datetime"],
            duration_hours=inputs["duration_hours"],
            step_minutes=inputs["step_minutes"],
            output_path=output_path,
            file_format=file_format,
            add_layer=inputs["add_layer"],
            login=None,
            password=None,
            data_format=inputs["data_format"],
            create_line_layer=inputs["create_line_layer"],
            save_data=inputs["save_data"],
            data_file_path=file_path,
            save_data_path=save_data_path
        )

    def _create_config_for_spacetrack(self, inputs: dict, sat_id: int, file_format: str) -> OrbitalConfig:
        """Create config for SpaceTrack data.

        Args:
            inputs (dict): User inputs.
            sat_id (int): NORAD ID of the satellite.
            file_format (str): Output file format.

        Returns:
            OrbitalConfig: Configuration object.
        """
        output_path = inputs["output_path"]
        save_data_path = inputs["save_data_path"]

        if output_path and os.path.isdir(output_path):
            output_path = os.path.join(output_path, f"sat_{sat_id}_points.{file_format}")
        if inputs["save_data"] and save_data_path and os.path.isdir(save_data_path):
            save_data_path = os.path.join(save_data_path, f"{sat_id}.tle")

        return OrbitalConfig(
            sat_id=sat_id,
            start_datetime=inputs["start_datetime"],
            duration_hours=inputs["duration_hours"],
            step_minutes=inputs["step_minutes"],
            output_path=output_path,
            file_format=file_format,
            add_layer=inputs["add_layer"],
            login=inputs["login"],
            password=inputs["password"],
            data_format=inputs["data_format"],
            create_line_layer=inputs["create_line_layer"],
            save_data=inputs["save_data"],
            data_file_path=inputs["data_file_path"],
            save_data_path=save_data_path
        )

    def _load_layer(self, file_path: str, layer_type: str) -> None:
        """Load and add a vector layer to QGIS.

        Args:
            file_path (str): Path to the layer file.
            layer_type (str): "point" or "line".
        """
        if not file_path:
            return
        layer_name = os.path.splitext(os.path.basename(file_path))[0]
        layer = QgsVectorLayer(file_path, layer_name, "ogr")
        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            self.log_message(f"{layer_type.capitalize()} layer loaded with {layer.featureCount()} features.", "INFO")
        else:
            self.log_message(f"Failed to load {layer_type} layer: {file_path}", "ERROR")
            self.iface.messageBar().pushMessage("Error", f"Failed to load {layer_type} layer", level=3)

    def _process_track(self, config: OrbitalConfig, facade: OrbitalTrackFacade) -> None:
        """Generate an orbital track based on configuration.

        Args:
            config (OrbitalConfig): Track configuration.
            facade (OrbitalTrackFacade): Processing facade.
        """
        if config.output_path:
            point_file, line_file = facade.process_persistent_track(config)
            self.log_message(f"Files created: Point={point_file}, Line={line_file}", "INFO")
            self._load_layer(point_file, "point")
            self._load_layer(line_file, "line")
            self.iface.messageBar().pushMessage(
                self.tr("Success"),
                self.tr(f"{config.file_format.capitalize()} created"),
                level=0
            )
        else:
            point_layer, line_layer = facade.process_in_memory_track(config)
            if config.add_layer:
                QgsProject.instance().addMapLayer(point_layer)
                QgsProject.instance().addMapLayer(line_layer)
                self.log_message(f"Temporary layers added: {point_layer.featureCount()} points.", "INFO")
            self.iface.messageBar().pushMessage(
                self.tr("Success"),
                self.tr("Temporary layers created"),
                level=0
            )

    def _process_item(self, item_id: int, inputs: dict, file_format: str, facade: OrbitalTrackFacade) -> bool:
        """Process a single satellite or file.

        Args:
            item_id (int): NORAD ID or file index.
            inputs (dict): User inputs.
            file_format (str): Output file format.
            facade (OrbitalTrackFacade): Processing facade.

        Returns:
            bool: True if successful, False otherwise.
        """
        is_local = bool(inputs["data_file_paths"])
        item_name = os.path.basename(inputs["data_file_paths"][item_id]) if is_local else str(item_id)

        try:
            config = (self._create_config_for_local_file if is_local else self._create_config_for_spacetrack)(
                inputs, item_id, file_format
            )
            self.log_message(f"Processing {'file' if is_local else 'NORAD ID'}: {item_name}", "INFO")
            self._process_track(config, facade)
            self.log_message(f"Processed {'file' if is_local else 'NORAD ID'}: {item_name}", "INFO")
            return True
        except Exception as e:
            self.log_message(f"Error processing {'file' if is_local else 'NORAD ID'} {item_name}: {str(e)}", "ERROR")
            self.iface.messageBar().pushMessage(
                self.tr("Warning"),
                f"Failed to process {'file' if is_local else 'satellite'} {item_name}: {str(e)}",
                level=2
            )
            return False

    def _process_satellites(self, sat_ids: list[int], inputs: dict, file_format: str) -> tuple[list[int], list[int]]:
        """Process all satellites or files.

        Args:
            sat_ids (list[int]): List of NORAD IDs or file indices.
            inputs (dict): User inputs.
            file_format (str): Output file format.

        Returns:
            tuple[list[int], list[int]]: (successful IDs, failed IDs).
        """
        from ..data_retriver.data_retriver import LocalFileRetriever
        from ..data_retriver.spacetrack_retriver import SpaceTrackRetriever

        retriever = (
            LocalFileRetriever(log_callback=self.log_message) if inputs["data_file_paths"]
            else SpaceTrackRetriever(inputs["login"], inputs["password"], log_callback=self.log_message)
        )
        facade = OrbitalTrackFacade(retriever, log_callback=self.log_message)

        successful, failed = [], []
        for item_id in sat_ids:
            if self._process_item(item_id, inputs, file_format, facade):
                successful.append(item_id)
            else:
                failed.append(item_id)
        return successful, failed

    def _log_summary(self, successful: list[int], failed: list[int], inputs: dict, duration: float) -> None:
        """Log processing summary.

        Args:
            successful (list[int]): IDs of successfully processed items.
            failed (list[int]): IDs of failed items.
            inputs (dict): User inputs.
            duration (float): Processing time in seconds.
        """
        is_local = bool(inputs["data_file_paths"])
        item_type = "files" if is_local else "satellites"
        total = len(successful) + len(failed)

        self.log_message(f"Completed in {duration:.2f} seconds.", "INFO")
        self.log_message(f"Summary: {len(successful)}/{total} {item_type} processed.", "INFO")

        if successful:
            names = [os.path.basename(inputs["data_file_paths"][i]) if is_local else str(i) for i in successful]
            self.log_message(f"Successful {item_type}: {', '.join(names)}", "INFO")
        if failed:
            names = [os.path.basename(inputs["data_file_paths"][i]) if is_local else str(i) for i in failed]
            self.log_message(f"Failed {item_type}: {', '.join(names)}", "WARNING")
            self.iface.messageBar().pushMessage(
                self.tr("Processing Complete"),
                f"Processed {len(successful)}/{total} {item_type}. {len(failed)} failed.",
                level=1
            )
        else:
            self.iface.messageBar().pushMessage(
                self.tr("Success"),
                f"All {total} {item_type} processed successfully.",
                level=0
            )

    def execute_logic(self):
        """Run the main logic to generate orbital tracks."""
        self.dlg.switch_to_log_tab()
        self.log_message("Process started.", "INFO")

        try:
            start_time = time.time()
            inputs = self.dlg.get_inputs()
            sat_ids, file_format, validated_output_path = self._validate_inputs(inputs)
            inputs["output_path"] = validated_output_path
            inputs["file_format"] = file_format
            successful, failed = self._process_satellites(sat_ids, inputs, file_format)
            self._log_summary(successful, failed, inputs, time.time() - start_time)
        except Exception as e:
            self.log_message(f"Error: {str(e)}", "ERROR")
            self.iface.messageBar().pushMessage("Error", str(e), level=3)

    def run(self):
        """Display the plugin dialog."""
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
        """Handle dialog closure."""
        self._close_logger()
        self.dlg.close()