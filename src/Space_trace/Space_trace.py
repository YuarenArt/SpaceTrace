
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

class SpaceTracePlugin:
    """
    QGIS Plugin Implementation.

    This class handles all user interface operations. It delegates the core
    orbital track creation to the OrbitalOrchestrator, which manages the logic
    of retrieving TLE data and generating both persistent and in-memory layers.
    """
    def __init__(self, iface):
        """
        Constructor for the plugin.

        :param iface: QGIS interface instance.
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        # Initialize localization settings
        self._init_localization()
        # Initialize plugin attributes
        self.actions = []
        self.menu = self.tr('&Space trace')
        self.first_start = None
        
        self._init_localization()
        self._init_logger()
        self.logger.info("SpaceTracePlugin initialized.")
        
    def _init_logger(self):
        """
        Initialize the file logger for the plugin.
        """
        self.logger = logging.getLogger("SpaceTracePlugin")
        self.logger.setLevel(logging.DEBUG)
        # Avoid duplicate handlers
        if not self.logger.handlers:
            log_file = os.path.join(self.plugin_dir, "SpaceTracePlugin.log")
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s",
                                          datefmt="%Y-%m-%d %H:%M:%S")
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
                     
    def _init_localization(self):
        """
        Initialize localization settings.
        """
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'SpaceTracePlugin_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

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
                        text=self.tr('Draw flight path lines'),
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

    def execute_logic(self):
        """
        Execute the main plugin logic for generating orbital tracks.
        """
        
        self.dlg.switch_to_log_tab()
        self.log_message("Process started.")
        
        try:
            start_time = time.time()

            sat_id_text = self.dlg.lineEditSatID.text().strip()
            if not sat_id_text:
                raise Exception("Please enter the satellite NORAD ID.")
            sat_id = int(sat_id_text)
            track_day = self.dlg.dateEdit.date().toPyDate()
            step_minutes = self.dlg.spinBoxStepMinutes.value()
            output_path = self.dlg.lineEditOutputPath.text().strip()
            add_layer = self.dlg.checkBoxAddLayer.isChecked()
            login = self.dlg.lineEditLogin.text().strip()
            password = self.dlg.lineEditPassword.text().strip()
            if not login or not password:
                raise Exception("Please enter your SpaceTrack account login and password.")
            data_format = self.dlg.comboBoxDataFormat.currentText()
            create_line_layer = self.dlg.checkBoxCreateLineLayer.isChecked()
            
            if output_path:
                _, ext = os.path.splitext(output_path)
                file_format = ext[1:].lower()  
                if file_format not in ['shp', 'gpkg', 'geojson']:
                    raise Exception("Unsupported file format. Use .shp, .gpkg, or .geojson.")
            else:
                file_format = None
            
            self.log_message(
                f"User input: Sat ID={sat_id}, Track Day={track_day}, File Format={file_format}, "
                f"Step Minutes={step_minutes}, Output Path={output_path}, Data Format={data_format}",
                "DEBUG"
            )

            # Initialize the orbital orchestrator
            orchestrator = OrbitalOrchestrator(login, password, log_callback=self.log_message)
            self.log_message("OrbitalOrchestrator initialized.", "DEBUG")

            if output_path:
                point_file, line_file = orchestrator.process_persistent_track(
                    sat_id, track_day, step_minutes, output_path, data_format,
                    file_format, create_line_layer
                )
                self.log_message(f"Files created: Point={point_file}, Line={line_file}", "INFO")
                self.iface.messageBar().pushMessage("Success", f"{file_format.capitalize()} created successfully", level=0)
                
                point_layer_name = os.path.splitext(os.path.basename(point_file))[0]
                point_layer = QgsVectorLayer(point_file, point_layer_name, "ogr")
                if not point_layer.isValid():
                    self.iface.messageBar().pushMessage("Error", "Failed to load point layer", level=3)
                    self.log_message("Failed to load point layer from persistent file.", "ERROR")
                else:
                    QgsProject.instance().addMapLayer(point_layer)
                    num_points = point_layer.featureCount()
                    self.log_message(f"Point layer loaded with {num_points} features.", "INFO")
                    
                line_layer_name = os.path.splitext(os.path.basename(line_file))[0]
                line_layer = QgsVectorLayer(line_file, line_layer_name, "ogr")
                if not line_layer.isValid():
                    self.iface.messageBar().pushMessage("Error", "Failed to load line layer", level=3)
                    self.log_message("Failed to load line layer from persistent file.", "ERROR")
                else:
                    QgsProject.instance().addMapLayer(line_layer)
                    num_lines = line_layer.featureCount()
                    self.log_message(f"Line layer loaded with {num_lines} features.", "INFO")
            else:
                point_layer, line_layer = orchestrator.process_in_memory_track(
                    sat_id, track_day, step_minutes, data_format, create_line_layer
                )
                if add_layer:
                    QgsProject.instance().addMapLayer(point_layer)
                    QgsProject.instance().addMapLayer(line_layer)
                    self.log_message("Temporary layers added to the project.", "INFO")
                    
                    num_points = point_layer.featureCount()
                    num_lines = line_layer.featureCount()
                    self.log_message(f"Temporary Point layer contains {num_points} features.", "INFO")
                    self.log_message(f"Temporary Line layer contains {num_lines} features.", "INFO")
                    
                self.iface.messageBar().pushMessage("Success", "Temporary layers created successfully", level=0)

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
        if self.first_start:
            self.first_start = False
            self.dlg = SpaceTracePluginDialog()
            
            self.dlg.pushButtonExecute.clicked.connect(self.execute_logic)
            self.dlg.pushButtonClose.clicked.connect(self.dlg.close)
        self.dlg.show()  