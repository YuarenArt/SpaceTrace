from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsVectorLayer, QgsProject
import os.path
import time
from datetime import datetime

# Import Qt resources and the dialog for the plugin
from .resources import *
from .Space_trace_dialog import SpaceTracePluginDialog

# Import the refactored orbital logic module
from .src.Logic.orbital_orchestrator import OrbitalOrchestrator

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
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'SpaceTracePlugin_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        # Initialize plugin attributes
        self.actions = []
        self.menu = self.tr('&Space trace')
        self.first_start = None

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
            
    def log_message(self, message):
        """
        Log a message with a timestamp.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.dlg.appendLog(log_entry)

    def run(self):
        if self.first_start:
            self.first_start = False
            self.dlg = SpaceTracePluginDialog()
        self.dlg.show()
        if not self.dlg.exec_():
            self.log_message("User closed the dialog without executing.")
            return

        try:
            start_time = time.time()
            self.log_message("Process started.")

            # Retrieve and validate user input data
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

            # Get split type and count from UI
            split_type_text = self.dlg.comboBoxSplitType.currentText()
            if split_type_text == "Solid line":
                split_type = 'none'
            elif split_type_text == "Split by antimeridian":
                split_type = 'antimeridian'
            elif split_type_text == "Set the number of splits":
                split_type = 'custom'
                split_count = self.dlg.spinBoxSplitCount.value()
            else:
                raise ValueError("Invalid split type selected")
            split_count = split_count if split_type == 'custom' else 0

            file_format = self.dlg.comboBoxFileFormat.currentText()
            
            self.log_message(f"Retrieved user input: Sat ID={sat_id}, Track Day={track_day}, File Format={file_format}, Step Minutes={step_minutes}, Output Path={output_path}, Data Format={data_format}, Split Type={split_type}, Split Count={split_count}")

            # Initialize the orbital orchestrator
            orchestrator = OrbitalOrchestrator(login, password)

            if output_path:
                point_file, line_file = orchestrator.process_persistent_track(
                    sat_id, track_day, step_minutes, output_path, data_format=data_format,
                    file_format=file_format, split_type=split_type, split_count=split_count
                )
                self.log_message(f"Files created: Point={point_file}, Line={line_file}")
                self.iface.messageBar().pushMessage("Success", f"{file_format.capitalize()} created successfully", level=0)
                point_layer_name = os.path.splitext(os.path.basename(point_file))[0]
                point_layer = QgsVectorLayer(point_file, point_layer_name, "ogr")
                if not point_layer.isValid():
                    self.iface.messageBar().pushMessage("Error", "Failed to load point layer", level=3)
                else:
                    QgsProject.instance().addMapLayer(point_layer)
                line_layer_name = os.path.splitext(os.path.basename(line_file))[0]
                line_layer = QgsVectorLayer(line_file, line_layer_name, "ogr")
                if not line_layer.isValid():
                    self.iface.messageBar().pushMessage("Error", "Failed to load line layer", level=3)
                else:
                    QgsProject.instance().addMapLayer(line_layer)

            else:
                # Temporary layers mode
                point_layer, line_layer = orchestrator.process_in_memory_track(
                    sat_id, track_day, step_minutes, data_format=data_format,
                    split_type=split_type, split_count=split_count
                )
                if add_layer:
                    QgsProject.instance().addMapLayer(point_layer)
                    QgsProject.instance().addMapLayer(line_layer)
                    self.log_message("Temporary layers added to the project.")
                self.iface.messageBar().pushMessage("Success", "Temporary layers created successfully", level=0)

            end_time = time.time()
            duration = end_time - start_time
            self.log_message(f"Process completed in {duration:.2f} seconds.")

        except Exception as e:
            self.iface.messageBar().pushMessage("Error", str(e), level=3)
            self.log_message(f"Error: {str(e)}")