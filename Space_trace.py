from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsVectorLayer, QgsProject
import os.path

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

    def run(self):
        """
        Main method to run the plugin.
        Displays the dialog and, upon confirmation, processes the orbital data.
        """
        if self.first_start:
            self.first_start = False
            self.dlg = SpaceTracePluginDialog()
        self.dlg.show()
        # exec_() returns True if the Execute (Accept) button is clicked
        if not self.dlg.exec_():
            return  # User closed the dialog without executing

        try:
            # Retrieve and validate user input data
            sat_id_text = self.dlg.lineEditSatID.text().strip()
            if not sat_id_text:
                raise Exception("Please enter the satellite NORAD ID.")
            sat_id = int(sat_id_text)
            track_day = self.dlg.dateEdit.date().toPyDate()
            step_minutes = self.dlg.spinBoxStepMinutes.value()
            output_path = self.dlg.lineEditOutputPath.text().strip()
            add_layer = self.dlg.checkBoxAddLayer.isChecked()
            # Retrieve SpaceTrack login credentials
            login = self.dlg.lineEditLogin.text().strip()
            password = self.dlg.lineEditPassword.text().strip()
            if not login or not password:
                raise Exception("Please enter your SpaceTrack account login and password.")
            data_format = self.dlg.comboBoxDataFormat.currentText()

            # Initialize the orbital orchestrator with provided data
            orchestrator = OrbitalOrchestrator(login, password)

            if output_path:
                # Persistent mode: create shapefile on disk
                point_shp, line_shp = orchestrator.process_persistent_track(
                    sat_id, track_day, step_minutes, output_path, data_format=data_format
                )
                self.iface.messageBar().pushMessage("Success", "Shapefile created successfully", level=0)
                # Load and add point layer
                point_layer_name = os.path.splitext(os.path.basename(point_shp))[0]
                point_layer = QgsVectorLayer(point_shp, point_layer_name, "ogr")
                if not point_layer.isValid():
                    self.iface.messageBar().pushMessage("Error", "Failed to load point layer", level=3)
                else:
                    QgsProject.instance().addMapLayer(point_layer)
                # Load and add line layer
                line_layer_name = os.path.splitext(os.path.basename(line_shp))[0]
                line_layer = QgsVectorLayer(line_shp, line_layer_name, "ogr")
                if not line_layer.isValid():
                    self.iface.messageBar().pushMessage("Error", "Failed to load line layer", level=3)
                else:
                    QgsProject.instance().addMapLayer(line_layer)
            else:
                # Temporary layers mode: create in-memory layers
                point_layer, line_layer = orchestrator.process_in_memory_track(
                    sat_id, track_day, step_minutes, data_format=data_format
                )
                if add_layer:
                    QgsProject.instance().addMapLayer(point_layer)
                    QgsProject.instance().addMapLayer(line_layer)
                self.iface.messageBar().pushMessage("Success", "Temporary layers created successfully", level=0)
        except Exception as e:
            self.iface.messageBar().pushMessage("Error", str(e), level=3)
