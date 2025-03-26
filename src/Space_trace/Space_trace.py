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
from ..orbital.orchestrator import OrbitalOrchestrator
from ..config.orbital import OrbitalConfig


class SpaceTracePlugin:
    """
    QGIS Plugin Implementation.

    This class handles all user interface operations and delegates
    the core orbital track creation to the OrbitalOrchestrator.
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
        locale = QSettings().value('locale/userLocale')[0:2]
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

    def log_message(self, message, level="INFO"):
        """
        Log a message with a timestamp to both the file and the UI log window.

        :param message: The log message.
        :param level: Log level ("INFO", "DEBUG", "WARNING", "ERROR").
        """
        message = self.tr(message)

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
        return {
            'data_file_path': self.dlg.lineEditDataPath.text().strip(),
            'sat_id_text': self.dlg.lineEditSatID.text().strip(),
            'track_day': self.dlg.dateEdit.date().toPyDate(),
            'step_minutes': self.dlg.spinBoxStepMinutes.value(),
            'output_path': self.dlg.lineEditOutputPath.text().strip(),
            'add_layer': self.dlg.checkBoxAddLayer.isChecked(),
            'login': self.dlg.lineEditLogin.text().strip(),
            'password': self.dlg.lineEditPassword.text().strip(),
            'data_format': self.dlg.comboBoxDataFormat.currentText(),
            'create_line_layer': self.dlg.checkBoxCreateLineLayer.isChecked(),
            'save_data': self.dlg.checkBoxSaveData.isChecked()
        }

    def _validate_inputs(self, inputs):
        """
        Validate user inputs and process the satellite ID and file format.

        :param inputs: Dictionary of user input values.
        :return: Tuple (sat_id, file_format) after validation.
        :raises Exception: When validation fails.
        """
        # Validate satellite ID only if no local file path is provided.
        if not inputs['data_file_path']:
            if not inputs['sat_id_text']:
                raise Exception(self.tr("Please enter a satellite NORAD ID."))
            try:
                sat_id = int(inputs['sat_id_text'])
                if sat_id <= 0:
                    raise ValueError("Satellite NORAD ID must be a positive integer.")
            except ValueError:
                raise Exception(self.tr("Invalid NORAD ID: Please enter a valid positive integer."))
        else:
            sat_id = None  # Skip validation if local file is provided

        # Validate that either a local file path or credentials are provided, but not both
        if inputs['data_file_path'] and (inputs['login'] or inputs['password']):
            raise Exception(self.tr("Please provide either a local data file path or SpaceTrack credentials, not both."))
        if not inputs['data_file_path'] and not (inputs['login'] and inputs['password']):
            raise Exception(self.tr("Please provide either a local data file path or SpaceTrack account login and password."))

        # Validate output file format if provided
        if inputs['output_path']:
            _, ext = os.path.splitext(inputs['output_path'])
            file_format = ext[1:].lower()
            if file_format not in ['shp', 'gpkg', 'geojson']:
                raise Exception(self.tr("Unsupported file format. Use .shp, .gpkg, or .geojson."))
        else:
            file_format = None

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
            track_day=inputs['track_day'],
            step_minutes=inputs['step_minutes'],
            output_path=inputs['output_path'],
            file_format=file_format,
            add_layer=inputs['add_layer'],
            login=inputs['login'] if inputs['login'] else None,
            password=inputs['password'] if inputs['password'] else None,
            data_format=inputs['data_format'],
            create_line_layer=inputs['create_line_layer'],
            save_data=inputs['save_data'],
            data_file_path=inputs['data_file_path']
        )

    def _process_track(self, config):
        """
        Process the orbital track based on the configuration.
        
        :param config: An OrbitalConfig instance.
        """
        orchestrator = OrbitalOrchestrator(config.login, config.password, log_callback=self.log_message)
        self.log_message("OrbitalOrchestrator initialized.", "DEBUG")
        if config.output_path:
            point_file, line_file = orchestrator.process_persistent_track(config)
            self.log_message(f"Files created: Point={point_file}, Line={line_file}", "INFO")
            self.iface.messageBar().pushMessage(
                self.tr("Success"),
                self.tr("{} created successfully").format(config.file_format.capitalize()),
                level=0
            )
            self._load_and_add_layer(point_file, "point")
            self._load_and_add_layer(line_file, "line")
        else:
            point_layer, line_layer = orchestrator.process_in_memory_track(config)
            if config.add_layer:
                QgsProject.instance().addMapLayer(point_layer)
                QgsProject.instance().addMapLayer(line_layer)
                self.log_message("Temporary layers added to the project.", "INFO")
                self.log_message(f"Temporary Point layer contains {point_layer.featureCount()} features.", "INFO")
                self.log_message(f"Temporary Line layer contains {line_layer.featureCount()} features.", "INFO")
            self.iface.messageBar().pushMessage("Success", "Temporary layers created successfully", level=0)

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

            # Gather user inputs from the dialog
            inputs = self._gather_user_inputs()

            # Validate inputs and process satellite ID and output file format
            sat_id, file_format = self._validate_inputs(inputs)

            # Log inputs for debugging
            self.log_message(
                f"User input: Sat ID={sat_id}, Track Day={inputs['track_day']}, File Format={file_format}, "
                f"Step Minutes={inputs['step_minutes']}, Output Path={inputs['output_path']}, "
                f"Data Format={inputs['data_format']}, Save Data={inputs['save_data']}, "
                f"Data File Path={inputs['data_file_path']}, Login={inputs['login'] if inputs['login'] else 'Not provided'}",
                "DEBUG"
            )

            # Create configuration object from inputs
            config = self._create_config(inputs, sat_id, file_format)

            # Process the orbital track based on the configuration
            self._process_track(config)

            # Log process completion time
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
            self.dlg = SpaceTracePluginDialog()
            self.dlg.pushButtonExecute.clicked.connect(self.execute_logic)
            self.dlg.pushButtonClose.clicked.connect(self.dlg.close)
        self.dlg.show()
