import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialogButtonBox, QPushButton, QGroupBox, QRadioButton, QButtonGroup, QTextBrowser
from PyQt5.QtCore import Qt

class Ui_SpaceTracePluginDialogBase(object):

    def setupUi(self, Dialog):
        """
        Set up the UI for the dialog window.
        
        Args:
            Dialog (QtWidgets.QDialog): The dialog window that will contain all UI elements.
        """
        # Set dialog properties
        Dialog.setObjectName("SpaceTracePluginDialogBase")
        Dialog.resize(600, 450)

        # Create the main vertical layout for the dialog
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")

        # Create the tab widget for different settings
        self.tabWidget = QtWidgets.QTabWidget(Dialog)
        self.tabWidget.setObjectName("tabWidget")
        self.verticalLayout.addWidget(self.tabWidget)

        # ========================
        # Main Settings Tab
        # ========================
        self.tabMain = QtWidgets.QWidget()
        self.tabMain.setObjectName("tabMain")
        self.verticalLayoutMain = QtWidgets.QVBoxLayout(self.tabMain)
        self.verticalLayoutMain.setObjectName("verticalLayoutMain")

        # Data source group box: Allows the user to choose between loading data from a file or SpaceTrack API
        self.groupBoxDataSource = QGroupBox("Data Source", self.tabMain)
        self.verticalLayoutDataSource = QtWidgets.QVBoxLayout(self.groupBoxDataSource)
        
        self.radioLocalFile = QRadioButton("Load from local file", self.groupBoxDataSource)
        self.radioSpaceTrack = QRadioButton("Fetch from SpaceTrack API", self.groupBoxDataSource)
        self.radioSpaceTrack.setChecked(True)  # Default to SpaceTrack API
        self.verticalLayoutDataSource.addWidget(self.radioLocalFile)
        self.verticalLayoutDataSource.addWidget(self.radioSpaceTrack)

        # Add buttons to a button group for exclusive selection
        self.buttonGroupDataSource = QButtonGroup(self.groupBoxDataSource)
        self.buttonGroupDataSource.addButton(self.radioLocalFile)
        self.buttonGroupDataSource.addButton(self.radioSpaceTrack)
        self.verticalLayoutMain.addWidget(self.groupBoxDataSource)

        # Local file settings group box
        self.groupBoxLocalFile = QGroupBox("Local File Settings", self.tabMain)
        self.verticalLayoutLocalFile = QtWidgets.QVBoxLayout(self.groupBoxLocalFile)

        # Layout for selecting data file path
        self.horizontalLayoutData = QtWidgets.QHBoxLayout()
        self.lineEditDataPath = QtWidgets.QLineEdit(self.groupBoxLocalFile)
        self.lineEditDataPath.setPlaceholderText("Specify the path to the TLE/OMM data file")
        self.horizontalLayoutData.addWidget(self.lineEditDataPath)
        self.pushButtonBrowseData = QtWidgets.QPushButton("Browse", self.groupBoxLocalFile)
        self.horizontalLayoutData.addWidget(self.pushButtonBrowseData)
        self.verticalLayoutLocalFile.addLayout(self.horizontalLayoutData)

        # Combo box for selecting data format (TLE/OMM)
        self.comboBoxDataFormatLocal = QtWidgets.QComboBox(self.groupBoxLocalFile)
        self.comboBoxDataFormatLocal.addItems(["TLE", "OMM"])
        self.verticalLayoutLocalFile.addWidget(self.comboBoxDataFormatLocal)
        self.verticalLayoutMain.addWidget(self.groupBoxLocalFile)
        
        self.groupBoxLocalFile.setEnabled(False)  # Disable the group by default
        self.groupBoxLocalFile.hide()  # Hide the group by default

        # SpaceTrack API settings group box
        self.groupBoxSpaceTrack = QGroupBox("SpaceTrack API Settings", self.tabMain)
        self.verticalLayoutSpaceTrack = QtWidgets.QVBoxLayout(self.groupBoxSpaceTrack)

        # Input fields for SpaceTrack API settings
        self.lineEditSatID = QtWidgets.QLineEdit(self.groupBoxSpaceTrack)
        self.lineEditSatID.setPlaceholderText("Enter satellite's NORAD ID")
        self.verticalLayoutSpaceTrack.addWidget(self.lineEditSatID)

        self.lineEditLogin = QtWidgets.QLineEdit(self.groupBoxSpaceTrack)
        self.lineEditLogin.setPlaceholderText("Enter your SpaceTrack account email")
        self.verticalLayoutSpaceTrack.addWidget(self.lineEditLogin)

        self.lineEditPassword = QtWidgets.QLineEdit(self.groupBoxSpaceTrack)
        self.lineEditPassword.setPlaceholderText("Enter your SpaceTrack account password")
        self.lineEditPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.verticalLayoutSpaceTrack.addWidget(self.lineEditPassword)

        # Combo box for selecting data format (TLE/OMM)
        self.comboBoxDataFormatSpaceTrack = QtWidgets.QComboBox(self.groupBoxSpaceTrack)
        self.comboBoxDataFormatSpaceTrack.addItems(["TLE", "OMM"])
        self.verticalLayoutSpaceTrack.addWidget(self.comboBoxDataFormatSpaceTrack)
        self.verticalLayoutMain.addWidget(self.groupBoxSpaceTrack)

        # Connect radio buttons for toggling data source
        self.radioLocalFile.toggled.connect(self.toggle_data_source)
        self.radioSpaceTrack.toggled.connect(self.toggle_data_source)

        # Track settings group box
        self.groupBoxTrackSettings = QGroupBox("Track Settings", self.tabMain)
        self.verticalLayoutTrackSettings = QtWidgets.QVBoxLayout(self.groupBoxTrackSettings)

    
        self.dateTimeEdit = QtWidgets.QDateTimeEdit(self.groupBoxTrackSettings)
        self.dateTimeEdit.setCalendarPopup(True)
        self.dateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())
        self.verticalLayoutTrackSettings.addWidget(self.dateTimeEdit)
        
        self.labelDuration = QtWidgets.QLabel("Duration (hours):", self.groupBoxTrackSettings)
        self.verticalLayoutTrackSettings.addWidget(self.labelDuration)
        self.spinBoxDuration = QtWidgets.QDoubleSpinBox(self.groupBoxTrackSettings)
        self.spinBoxDuration.setMinimum(0.1)  
        self.spinBoxDuration.setMaximum(168.0) 
        self.spinBoxDuration.setValue(24.0)  
        self.verticalLayoutTrackSettings.addWidget(self.spinBoxDuration)
        
        self.button1Hour = QtWidgets.QPushButton("1 hour", self.groupBoxTrackSettings)
        self.button1Day = QtWidgets.QPushButton("1 day", self.groupBoxTrackSettings)
        self.button1Week = QtWidgets.QPushButton("1 week", self.groupBoxTrackSettings)
        self.horizontalLayoutDurationButtons = QtWidgets.QHBoxLayout()
        self.horizontalLayoutDurationButtons.addWidget(self.button1Hour)
        self.horizontalLayoutDurationButtons.addWidget(self.button1Day)
        self.horizontalLayoutDurationButtons.addWidget(self.button1Week)
        self.verticalLayoutTrackSettings.addLayout(self.horizontalLayoutDurationButtons)
        
        self.button1Hour.clicked.connect(lambda: self.spinBoxDuration.setValue(1.0))
        self.button1Day.clicked.connect(lambda: self.spinBoxDuration.setValue(24.0))
        self.button1Week.clicked.connect(lambda: self.spinBoxDuration.setValue(168.0))

        # Spin box for selecting time step (in minutes)
        self.spinBoxStepMinutes = QtWidgets.QDoubleSpinBox(self.groupBoxTrackSettings)
        self.spinBoxStepMinutes.setMinimum(0.1)
        self.spinBoxStepMinutes.setMaximum(60.0)
        self.spinBoxStepMinutes.setSingleStep(5.0)
        self.spinBoxStepMinutes.setValue(0.5)
        self.verticalLayoutTrackSettings.addWidget(self.spinBoxStepMinutes)
        self.verticalLayoutMain.addWidget(self.groupBoxTrackSettings)

        # Output settings group box
        self.groupBoxOutput = QGroupBox("Output Settings", self.tabMain)
        self.verticalLayoutOutput = QtWidgets.QVBoxLayout(self.groupBoxOutput)

        # Layout for selecting output file path
        self.horizontalLayoutOutput = QtWidgets.QHBoxLayout()
        self.lineEditOutputPath = QtWidgets.QLineEdit(self.groupBoxOutput)
        self.lineEditOutputPath.setPlaceholderText("Specify the path to save file (leave empty for temporary layer)")
        self.horizontalLayoutOutput.addWidget(self.lineEditOutputPath)
        self.pushButtonBrowseOutput = QtWidgets.QPushButton("Browse", self.groupBoxOutput)
        self.horizontalLayoutOutput.addWidget(self.pushButtonBrowseOutput)
        self.verticalLayoutOutput.addLayout(self.horizontalLayoutOutput)

        # Checkboxes for additional output options
        self.checkBoxAddLayer = QtWidgets.QCheckBox("Add created layer to project", self.groupBoxOutput)
        self.checkBoxAddLayer.setChecked(True)
        self.verticalLayoutOutput.addWidget(self.checkBoxAddLayer)

        self.checkBoxCreateLineLayer = QtWidgets.QCheckBox("Create line layer", self.groupBoxOutput)
        self.checkBoxCreateLineLayer.setChecked(True)
        self.verticalLayoutOutput.addWidget(self.checkBoxCreateLineLayer)
        self.verticalLayoutMain.addWidget(self.groupBoxOutput)

        # Save data settings group box
        self.groupBoxSaveData = QGroupBox("Save Received Data", self.tabMain)
        self.verticalLayoutSaveData = QtWidgets.QVBoxLayout(self.groupBoxSaveData)

        # Checkbox for saving received data
        self.checkBoxSaveData = QtWidgets.QCheckBox("Save TLE/OMM data", self.groupBoxSaveData)
        self.checkBoxSaveData.setChecked(False)
        self.verticalLayoutSaveData.addWidget(self.checkBoxSaveData)

        # Layout for saving received data
        self.horizontalLayoutSaveData = QtWidgets.QHBoxLayout()
        self.lineEditSaveDataPath = QtWidgets.QLineEdit(self.groupBoxSaveData)
        self.lineEditSaveDataPath.setPlaceholderText("Specify the path to save received data")
        self.lineEditSaveDataPath.setEnabled(False)
        self.horizontalLayoutSaveData.addWidget(self.lineEditSaveDataPath)
        self.pushButtonBrowseSaveData = QtWidgets.QPushButton("Browse", self.groupBoxSaveData)
        self.pushButtonBrowseSaveData.setEnabled(False)
        self.horizontalLayoutSaveData.addWidget(self.pushButtonBrowseSaveData)
        self.verticalLayoutSaveData.addLayout(self.horizontalLayoutSaveData)
        self.verticalLayoutMain.addWidget(self.groupBoxSaveData)

        # Connect the checkbox to toggle the save data path
        self.checkBoxSaveData.toggled.connect(self.toggle_save_data_path)

        self.tabWidget.addTab(self.tabMain, "")

        # ======================
        # Program Log Tab
        # ======================
        self.tabLog = QtWidgets.QWidget()
        self.verticalLayoutLog = QtWidgets.QVBoxLayout(self.tabLog)

        # Text edit for displaying log messages
        self.textEditLog = QtWidgets.QTextEdit(self.tabLog)
        self.textEditLog.setReadOnly(True)
        self.verticalLayoutLog.addWidget(self.textEditLog)
        self.tabWidget.addTab(self.tabLog, "")
        
        # ========================
        # Help Tab
        # ========================
        self.tabHelp = QtWidgets.QWidget()
        self.tabHelp.setObjectName("tabHelp")
        self.verticalLayoutHelp = QtWidgets.QVBoxLayout(self.tabHelp)
        self.verticalLayoutHelp.setObjectName("verticalLayoutHelp")
        
        self.textBrowserHelp = QTextBrowser(self.tabHelp)
        self.verticalLayoutHelp.addWidget(self.textBrowserHelp)
        self.tabWidget.addTab(self.tabHelp, "")
        # ========================
        # End
        # ========================
        
        # Buttons for dialog actions
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.NoButton)
        self.verticalLayout.addWidget(self.buttonBox)

        self.pushButtonExecute = QPushButton("Execute", Dialog)
        self.buttonBox.addButton(self.pushButtonExecute, QDialogButtonBox.AcceptRole)

        self.pushButtonClose = QPushButton("Close", Dialog)
        self.buttonBox.addButton(self.pushButtonClose, QDialogButtonBox.RejectRole)

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

        self.loadHelpContent()
        
        # Connect buttons to browse file dialogs
        self.pushButtonBrowseData.clicked.connect(self.browseDataFile)
        self.pushButtonBrowseOutput.clicked.connect(self.browseOutputFile)
        self.pushButtonBrowseSaveData.clicked.connect(self.browseSaveDataFile)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("SpaceTracePluginDialogBase", "Space Trace"))
        self.groupBoxDataSource.setTitle(_translate("SpaceTracePluginDialogBase", "Data Source"))
        self.radioLocalFile.setText(_translate("SpaceTracePluginDialogBase", "Load from local file"))
        self.radioSpaceTrack.setText(_translate("SpaceTracePluginDialogBase", "Fetch from SpaceTrack API"))
        self.groupBoxLocalFile.setTitle(_translate("SpaceTracePluginDialogBase", "Local File Settings"))
        self.lineEditDataPath.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Specify the path to the TLE/OMM data file"))
        self.pushButtonBrowseData.setText(_translate("SpaceTracePluginDialogBase", "Browse"))
        self.groupBoxSpaceTrack.setTitle(_translate("SpaceTracePluginDialogBase", "SpaceTrack API Settings"))
        self.lineEditSatID.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Enter satellite's NORAD ID"))
        self.lineEditLogin.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Enter your SpaceTrack account email"))
        self.lineEditPassword.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Enter your SpaceTrack account password"))
        self.groupBoxTrackSettings.setTitle(_translate("SpaceTracePluginDialogBase", "Track Settings"))
        self.groupBoxOutput.setTitle(_translate("SpaceTracePluginDialogBase", "Output Settings"))
        self.lineEditOutputPath.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Specify the path to save file (leave empty for temporary layer)"))
        self.pushButtonBrowseOutput.setText(_translate("SpaceTracePluginDialogBase", "Browse"))
        self.checkBoxAddLayer.setText(_translate("SpaceTracePluginDialogBase", "Add created layer to project"))
        self.checkBoxCreateLineLayer.setText(_translate("SpaceTracePluginDialogBase", "Create line layer"))
        self.groupBoxSaveData.setTitle(_translate("SpaceTracePluginDialogBase", "Save Received Data"))
        self.checkBoxSaveData.setText(_translate("SpaceTracePluginDialogBase", "Save TLE/OMM data"))
        self.lineEditSaveDataPath.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Specify the path to save received data"))
        self.pushButtonBrowseSaveData.setText(_translate("SpaceTracePluginDialogBase", "Browse"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabMain), _translate("SpaceTracePluginDialogBase", "Main"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabLog), _translate("SpaceTracePluginDialogBase", "Log"))
        self.pushButtonExecute.setText(_translate("SpaceTracePluginDialogBase", "Execute"))
        self.pushButtonClose.setText(_translate("SpaceTracePluginDialogBase", "Close"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabHelp), _translate("SpaceTracePluginDialogBase", "Help"))
        self.labelDuration.setText(_translate("Dialog", "Duration (hours):"))
        self.button1Hour.setText(_translate("Dialog", "1 hour"))
        self.button1Day.setText(_translate("Dialog", "1 day"))
        self.button1Week.setText(_translate("Dialog", "1 week"))
    
    def loadHelpContent(self):
        ui_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        help_file = os.path.join(ui_dir, "readme.html")
        if os.path.exists(help_file):
            with open(help_file, "r", encoding="utf-8") as f:
                html_content = f.read()
            self.textBrowserHelp.setHtml(html_content)
        else:
            self.textBrowserHelp.setPlainText("File not found")    
    
    def toggle_save_data_path(self):
        enabled = self.checkBoxSaveData.isChecked()
        self.lineEditSaveDataPath.setEnabled(enabled)
        self.pushButtonBrowseSaveData.setEnabled(enabled)
        
    def toggle_data_source(self):
        if self.radioLocalFile.isChecked():
            self.groupBoxLocalFile.setEnabled(True)
            self.groupBoxLocalFile.show()
            self.groupBoxSpaceTrack.setEnabled(False)
            self.groupBoxSpaceTrack.hide()
        else:
            self.groupBoxLocalFile.setEnabled(False)
            self.groupBoxLocalFile.hide()
            self.groupBoxSpaceTrack.setEnabled(True)
            self.groupBoxSpaceTrack.show()

    
    def browseDataFile(self):
        """
        Opens a file dialog to select an existing data file. The file format filter is determined
        based on the selected source (TLE or JSON).
        """
        if self.radioLocalFile.isChecked():
            data_format = self.comboBoxDataFormatLocal.currentText()
        else:
            data_format = self.comboBoxDataFormatSpaceTrack.currentText()
        
        if data_format == "TLE":
            file_filter = "Text Files (*.txt)"
        else:
            file_filter = "JSON Files (*.json)"

        file, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Select Data File", "", file_filter)
        if file:
            self.lineEditDataPath.setText(file)

    def browseOutputFile(self):
        file, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Select Output File", "", "Shapefiles (*.shp);;GeoPackage (*.gpkg);;GeoJSON (*.geojson);;All Files (*)")
        if file:
            self.lineEditOutputPath.setText(file)

    def browseSaveDataFile(self):
        """
        Opens a file dialog to select a path for saving data. The file extension is automatically set
        based on the selected data format (TLE or JSON).
        """
        if self.radioLocalFile.isChecked():
            data_format = self.comboBoxDataFormatLocal.currentText()
        else:
            data_format = self.comboBoxDataFormatSpaceTrack.currentText()

        if data_format == "TLE":
            file_filter = "Text Files (*.txt)"
            extension = ".txt"
        else:
            file_filter = "JSON Files (*.json)"
            extension = ".json"

        file, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Select Save Path", "", file_filter)
        if file:
            if not file.endswith(extension):
                file += extension
            self.lineEditSaveDataPath.setText(file)

    def appendLog(self, message):
        # Append message to the log widget
        self.textEditLog.append(message)