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
from .DataRetriever.data_retriver import LocalFileRetriever
from .DataRetriever.spacetrack import SpaceTrackRetriever

class SpaceTracePlugin:
    """
    QGIS Plugin Implementation.

    This class handles all user interface operations and delegates
    the core orbital track creation to the Facade
    """
    def __init__(self, iface):
        """
        Constructor for the plugin.

        :param iface: QGIS interface instance.
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.actions = []
        self.menu = self.tr('Space trace')
        self.first_start = None

        self._init_logger()
        self._init_localization()
        self.logger.info("SpaceTracePlugin initialized.")

    def _init_logger(self):
        """
        Initialize the file logger for the plugin.
        """
        self.logger = logging.getLogger("SpaceTracePlugin")
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            log_file = os.path.join(self.plugin_dir, "SpaceTracePlugin.log")
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def _init_localization(self):
        """
        Initialize localization settings.
        """
        locale = QSettings().value('locale/userLocale')
        locale = locale[0:2] if locale else 'en'
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'SpaceTracePlugin_{locale}.qm')

        self.logger.debug(f"Detected locale: {locale}")
        self.logger.debug(f"Expected translation file path: {locale_path}")

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            loaded = self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

            if loaded:
                self.logger.debug(f"Successfully loaded translation file: {locale_path}")
            else:
                self.logger.warning(f"Failed to load translation file: {locale_path}")
        else:
            self.logger.warning(f"Translation file does not exist: {locale_path}")

    def tr(self, message):
        """
        Translate a message using Qt translation API.
        """
        return QCoreApplication.translate('SpaceTracePlugin', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True,
                   add_to_toolbar=True, status_tip=None, whats_this=None, parent=None):
        """
        Add an action to the QGIS toolbar and menu.
        """
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
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
        """
        Initialize the GUI by creating menu entries and toolbar icons.
        """
        icon_path = ':/plugins/Space_trace/icon.png'
        self.add_action(icon_path,
                        text=self.tr('Draw flight path'),
                        callback=self.run,
                        parent=self.iface.mainWindow())
        self.first_start = True

    def unload(self):
        """
        Remove the plugin menu items and icons from QGIS GUI.
        """
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.tr('&Space trace'), action)
            self.iface.removeToolBarIcon(action)
            
        self.close_logger()

    def log_message(self, message, level="INFO"):
        """
        Log a message with a timestamp to both the file and the UI log window.

        :param message: The log message.
        :param level: Log level ("INFO", "DEBUG", "WARNING", "ERROR").
        """

        if level.upper() == "DEBUG":
            self.logger.debug(message)
        elif level.upper() == "WARNING":
            self.logger.warning(message)
        elif level.upper() == "ERROR":
            self.logger.error(message)
        else:
            self.logger.info(message)

        if self.dlg and level.upper() in ["INFO", "WARNING", "ERROR"]:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            self.dlg.appendLog(formatted_message)
        QApplication.processEvents()

    def _gather_user_inputs(self):
        """
        Retrieve user inputs from the dialog.

        :return: A dictionary containing all user input values.
        """
        return self.dlg.get_inputs()
        
    def _validate_inputs(self, inputs):
        """
        Validate user inputs and process satellite ID and file format.

        Args:
            inputs (dict): Dictionary of user input values.

        Returns:
            tuple: (sat_id, file_format) after validation.

        Raises:
            Exception: If validation fails.
        """
        # Validate data source specific inputs
        if not inputs["data_file_path"]:
            # SpaceTrack mode
            if not inputs["sat_id_text"]:
                raise Exception(self.tr("Please enter a satellite NORAD ID."))
            if not inputs["login"] or not inputs["password"]:
                raise Exception(self.tr("Please provide SpaceTrack login and password."))
            try:
                sat_id = int(inputs["sat_id_text"])
                if sat_id <= 0:
                    raise ValueError
            except ValueError:
                raise Exception(self.tr("Invalid NORAD ID: Please enter a positive integer."))
        else:
            # Local file mode
            if not os.path.isfile(inputs["data_file_path"]) or not os.access(inputs["data_file_path"], os.R_OK):
                raise Exception(self.tr("Local data file does not exist or is not readable."))
            sat_id = None

        # Validate output file path
        if inputs["output_path"]:
            _, ext = os.path.splitext(inputs["output_path"])
            file_format = ext[1:].lower()
            supported_formats = {"shp", "gpkg", "geojson"}
            if file_format not in supported_formats:
                raise Exception(self.tr("Unsupported file format. Use .shp, .gpkg, or .geojson."))
            output_dir = os.path.dirname(inputs["output_path"])
            if output_dir and (not os.path.isdir(output_dir) or not os.access(output_dir, os.W_OK)):
                raise Exception(self.tr("Output directory does not exist or is not writable."))
        else:
            file_format = None

        # Validate save data path
        if inputs["save_data"] and inputs["save_data_path"]:
            save_dir = os.path.dirname(inputs["save_data_path"])
            if save_dir and (not os.path.isdir(save_dir) or not os.access(save_dir, os.W_OK)):
                raise Exception(self.tr("Save data directory does not exist or is not writable."))

        return sat_id, file_format

    def _create_config(self, inputs, sat_id, file_format):
        """
        Create an OrbitalConfig object based on validated inputs.

        :param inputs: Dictionary of user input values.
        :param sat_id: Validated satellite NORAD ID (or None).
        :param file_format: Validated file format (or None).
        :return: An OrbitalConfig instance.
        """
        return OrbitalConfig(
            sat_id=sat_id,
            start_datetime=inputs['start_datetime'],
            duration_hours=inputs['duration_hours'],
            step_minutes=inputs['step_minutes'],
            output_path=inputs['output_path'],
            file_format=file_format,
            add_layer=inputs['add_layer'],
            login=inputs['login'] if inputs['login'] else None,
            password=inputs['password'] if inputs['password'] else None,
            data_format=inputs['data_format'],
            create_line_layer=inputs['create_line_layer'],
            save_data=inputs['save_data'],
            data_file_path=inputs['data_file_path'],
            save_data_path=inputs['save_data_path']
        )

    def _process_track(self, config):
        """
        Process the orbital track based on the configuration.
        
        :param config: An OrbitalConfig instance.
        """

        
        if config.data_file_path:
            retriever = LocalFileRetriever(log_callback=self.log_message)
        else:
            retriever = SpaceTrackRetriever(config.login, config.password, log_callback=self.log_message)

        facade = OrbitalTrackFacade(retriever, log_callback=self.log_message)
        self.log_message("OrbitalFacade initialized", "DEBUG")
        if config.output_path:
            point_file, line_file = facade.process_persistent_track(config)
            self.log_message(f"Files created: Point={point_file}, Line={line_file}", "INFO")
            self.iface.messageBar().pushMessage(
                self.tr("Success"),
                self.tr("{} created successfully").format(config.file_format.capitalize()),
                level=0
            )
            self._load_and_add_layer(point_file, "point")
            self._load_and_add_layer(line_file, "line")
        else:
            point_layer, line_layer = facade.process_in_memory_track(config)
            if config.add_layer:
                QgsProject.instance().addMapLayer(point_layer)
                QgsProject.instance().addMapLayer(line_layer)
                self.log_message("Temporary layers added to the project.", "INFO")
                self.log_message(f"Temporary Point layer contains {point_layer.featureCount()} features.", "INFO")
            self.iface.messageBar().pushMessage("Success", "Temporary layers created successfully", level=0)
            
    def close_logger(self):
        if hasattr(self, 'logger') and self.logger:
            for handler in self.logger.handlers:
                handler.close()
                self.logger.removeHandler(handler)
            

    def _load_and_add_layer(self, file_path, layer_type):
        """
        Load a vector layer from a file and add it to the QGIS project.

        :param file_path: The file path to load.
        :param layer_type: A string identifier for the layer type.
        """
        if not file_path:
            return
        layer_name = os.path.splitext(os.path.basename(file_path))[0]
        layer = QgsVectorLayer(file_path, layer_name, "ogr")
        if not layer.isValid():
            self.iface.messageBar().pushMessage("Error", f"Failed to load {layer_type} layer", level=3)
            self.log_message(f"Failed to load {layer_type} layer from {file_path}.", "ERROR")
        else:
            QgsProject.instance().addMapLayer(layer)
            self.log_message(f"{layer_type.capitalize()} layer loaded with {layer.featureCount()} features.", "INFO")

    def execute_logic(self):
        """
        Execute the main plugin logic for generating orbital tracks.
        Either a local data file path or SpaceTrack account credentials must be provided, but not both.
        """
        self.dlg.switch_to_log_tab()
        self.log_message("Process started.")

        try:
            start_time = time.time()

            inputs = self._gather_user_inputs()
            sat_id, file_format = self._validate_inputs(inputs)

            self.log_message(
                f"User input: Sat ID={sat_id}, Start Datetime={inputs['start_datetime']}, "
                f"Duration Hours={inputs['duration_hours']}, File Format={file_format}, "
                f"Step Minutes={inputs['step_minutes']}, Output Path={inputs['output_path']}, "
                f"Data Format={inputs['data_format']}, Save Data={inputs['save_data']}, "
                f"Data File Path={inputs['data_file_path']}",
                "DEBUG"
            )

            config = self._create_config(inputs, sat_id, file_format)
            self._process_track(config)

            end_time = time.time()
            duration = end_time - start_time
            self.log_message(f"Process completed in {duration:.2f} seconds.", "INFO")

        except Exception as e:
            self.iface.messageBar().pushMessage("Error", str(e), level=3)
            self.log_message(f"Error: {str(e)}", "ERROR")

    def run(self):
        """
        Launch the plugin and display the dialog.
        """
        if self.first_start is None or self.first_start is True:
            self.first_start = False
            self.dlg = SpaceTracePluginDialog(translator=self.translator)
            self.dlg.pushButtonExecute.clicked.connect(self.execute_logic)
            self.dlg.pushButtonClose.clicked.connect(self.dlg.close)
            self.dlg.pushButtonClose.clicked.connect(self._on_close_button_clicked)
            self.dlg.rejected.connect(self.close_logger)
        else:    
            self._init_logger()
        self.dlg.show()
        
    def _on_close_button_clicked(self):
        """
        Handle the close button click by closing the logger and the dialog.
        """
        self.close_logger()
        self.dlg.close()
