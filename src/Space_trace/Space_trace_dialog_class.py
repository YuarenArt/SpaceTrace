import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QDialog, QGroupBox, QRadioButton, QButtonGroup,
    QDialogButtonBox, QPushButton, QTextBrowser, QFileDialog
)

class SpaceTracePluginDialogBase(QDialog):
    """Base UI class for Space Trace Tool containing only widget setup and layout."""
    
    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.translator = translator
        self._setup_ui()
        self.tabWidget.setCurrentIndex(0)
        self._apply_styles()

    def _apply_styles(self):
        """Apply modern styling to the dialog."""
        pass

    def _setup_ui(self):
        """Create and arrange all widgets and layouts."""
        self.resize(600, 450)
        self.setObjectName("SpaceTracePluginDialog")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)  # Remove help button

        # Main layout
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)

        # Tab widget
        self.tabWidget = QtWidgets.QTabWidget(self)
        self.verticalLayout.addWidget(self.tabWidget)

        # --- Main Tab ---
        self.tabMain = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(self.tabMain)
        main_layout.setSpacing(10)

        # Data Source Group
        self.groupBoxDataSource = QGroupBox(self.tabMain)
        ds_layout = QtWidgets.QVBoxLayout(self.groupBoxDataSource)
        ds_layout.setSpacing(5)
        
        self.radioLocalFile = QRadioButton(self.groupBoxDataSource)
        self.radioSpaceTrack = QRadioButton(self.groupBoxDataSource)
        self.radioSpaceTrack.setChecked(True)
        ds_layout.addWidget(self.radioLocalFile)
        ds_layout.addWidget(self.radioSpaceTrack)
        self.buttonGroupDataSource = QButtonGroup(self.groupBoxDataSource)
        self.buttonGroupDataSource.addButton(self.radioLocalFile)
        self.buttonGroupDataSource.addButton(self.radioSpaceTrack)
        main_layout.addWidget(self.groupBoxDataSource)

        # Local File Settings
        self.groupBoxLocalFile = QGroupBox(self.tabMain)
        lf_layout = QtWidgets.QVBoxLayout(self.groupBoxLocalFile)
        lf_layout.setSpacing(5)
        
        hl_data = QtWidgets.QHBoxLayout()
        hl_data.setSpacing(5)
        self.lineEditDataPath = QtWidgets.QLineEdit(self.groupBoxLocalFile)
        self.lineEditDataPath.setPlaceholderText("Specify the path to the TLE/OMM data file(s)")
        self.pushButtonBrowseData = QPushButton("Browse", self.groupBoxLocalFile)
        self.pushButtonBrowseData.setFixedWidth(80)
        hl_data.addWidget(self.lineEditDataPath)
        hl_data.addWidget(self.pushButtonBrowseData)
        lf_layout.addLayout(hl_data)
        
        self.comboBoxDataFormatLocal = QtWidgets.QComboBox(self.groupBoxLocalFile)
        self.comboBoxDataFormatLocal.addItems(["TLE", "OMM"])
        lf_layout.addWidget(self.comboBoxDataFormatLocal)
        main_layout.addWidget(self.groupBoxLocalFile)
        self.groupBoxLocalFile.setEnabled(False)
        self.groupBoxLocalFile.hide()

        # SpaceTrack API Settings
        self.groupBoxSpaceTrack = QGroupBox(self.tabMain)
        st_layout = QtWidgets.QVBoxLayout(self.groupBoxSpaceTrack)
        st_layout.setSpacing(5)
        
        hl_norad = QtWidgets.QHBoxLayout()
        hl_norad.setSpacing(5)
        self.lineEditSatID = QtWidgets.QLineEdit(self.groupBoxSpaceTrack)
        self.lineEditSatID.setPlaceholderText("Enter satellite's NORAD ID")
        self.pushButtonSearchSatellites = QPushButton("Search", self.groupBoxSpaceTrack)
        self.pushButtonSearchSatellites.setFixedWidth(80)
        hl_norad.addWidget(self.lineEditSatID)
        hl_norad.addWidget(self.pushButtonSearchSatellites)
        st_layout.addLayout(hl_norad)
        
        self.lineEditLogin = QtWidgets.QLineEdit(self.groupBoxSpaceTrack)
        self.lineEditLogin.setPlaceholderText("Enter your SpaceTrack account email")
        st_layout.addWidget(self.lineEditLogin)
        
        self.lineEditPassword = QtWidgets.QLineEdit(self.groupBoxSpaceTrack)
        self.lineEditPassword.setPlaceholderText("Enter your SpaceTrack account password")
        self.lineEditPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        st_layout.addWidget(self.lineEditPassword)
        
        self.comboBoxDataFormatSpaceTrack = QtWidgets.QComboBox(self.groupBoxSpaceTrack)
        self.comboBoxDataFormatSpaceTrack.addItems(["TLE", "OMM"])
        st_layout.addWidget(self.comboBoxDataFormatSpaceTrack)
        main_layout.addWidget(self.groupBoxSpaceTrack)

        # Track Settings
        self.groupBoxTrackSettings = QGroupBox(self.tabMain)
        ts_layout = QtWidgets.QVBoxLayout(self.groupBoxTrackSettings)
        self.dateTimeEdit = QtWidgets.QDateTimeEdit(self.groupBoxTrackSettings)
        self.dateTimeEdit.setCalendarPopup(True)
        self.dateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime())
        ts_layout.addWidget(self.dateTimeEdit)
        self.labelDuration = QtWidgets.QLabel("Duration (hours):", self.groupBoxTrackSettings)
        ts_layout.addWidget(self.labelDuration)
        self.spinBoxDuration = QtWidgets.QDoubleSpinBox(self.groupBoxTrackSettings)
        self.spinBoxDuration.setRange(0.1, 168.0)
        self.spinBoxDuration.setValue(24.0)
        ts_layout.addWidget(self.spinBoxDuration)
        btn_layout = QtWidgets.QHBoxLayout()
        for text, hrs in [("1 hour", 1.0), ("1 day", 24.0), ("1 week", 168.0)]:
            btn = QPushButton(text, self.groupBoxTrackSettings)
            btn_layout.addWidget(btn)
            self.__setattr__(f"quickButton_{text.replace(' ', '_')}", btn)
        ts_layout.addLayout(btn_layout)
        self.spinBoxStepMinutes = QtWidgets.QDoubleSpinBox(self.groupBoxTrackSettings)
        self.spinBoxStepMinutes.setRange(0.01, 60.0)
        self.spinBoxStepMinutes.setSingleStep(0.1)
        self.spinBoxStepMinutes.setValue(0.5)
        ts_layout.addWidget(self.spinBoxStepMinutes)
        main_layout.addWidget(self.groupBoxTrackSettings)

        # Output Settings
        self.groupBoxOutput = QGroupBox(self.tabMain)
        out_layout = QtWidgets.QVBoxLayout(self.groupBoxOutput)
        out_layout.setSpacing(5)
        
        hl_out = QtWidgets.QHBoxLayout()
        hl_out.setSpacing(5)
        self.lineEditOutputPath = QtWidgets.QLineEdit(self.groupBoxOutput)
        self.lineEditOutputPath.setPlaceholderText("Specify the path to save file (leave empty for temporary layer)")
        self.pushButtonBrowseOutput = QPushButton("Browse", self.groupBoxOutput)
        self.pushButtonBrowseOutput.setFixedWidth(80)
        hl_out.addWidget(self.lineEditOutputPath)
        hl_out.addWidget(self.pushButtonBrowseOutput)
        out_layout.addLayout(hl_out)
        
        self.checkBoxAddLayer = QtWidgets.QCheckBox("Add created layer to project", self.groupBoxOutput)
        self.checkBoxAddLayer.setChecked(True)
        out_layout.addWidget(self.checkBoxAddLayer)
        
        self.checkBoxCreateLineLayer = QtWidgets.QCheckBox("Create line layer", self.groupBoxOutput)
        self.checkBoxCreateLineLayer.setChecked(True)
        out_layout.addWidget(self.checkBoxCreateLineLayer)
        
        main_layout.addWidget(self.groupBoxOutput)

        # Save Data Settings
        self.groupBoxSaveData = QGroupBox(self.tabMain)
        sd_layout = QtWidgets.QVBoxLayout(self.groupBoxSaveData)
        sd_layout.setSpacing(5)
        
        self.checkBoxSaveData = QtWidgets.QCheckBox("Save TLE/OMM data", self.groupBoxSaveData)
        sd_layout.addWidget(self.checkBoxSaveData)
        
        hl_save = QtWidgets.QHBoxLayout()
        hl_save.setSpacing(5)
        self.lineEditSaveDataPath = QtWidgets.QLineEdit(self.groupBoxSaveData)
        self.lineEditSaveDataPath.setPlaceholderText("Specify the path to save received data")
        self.lineEditSaveDataPath.setEnabled(False)
        self.pushButtonBrowseSaveData = QPushButton("Browse", self.groupBoxSaveData)
        self.pushButtonBrowseSaveData.setEnabled(False)
        self.pushButtonBrowseSaveData.setFixedWidth(80)
        hl_save.addWidget(self.lineEditSaveDataPath)
        hl_save.addWidget(self.pushButtonBrowseSaveData)
        sd_layout.addLayout(hl_save)
        
        main_layout.addWidget(self.groupBoxSaveData)

        self.tabWidget.addTab(self.tabMain, "")

        # --- Log Tab ---
        self.tabLog = QtWidgets.QWidget()
        log_layout = QtWidgets.QVBoxLayout(self.tabLog)
        log_layout.setContentsMargins(0, 0, 0, 0)
        self.textEditLog = QtWidgets.QTextEdit(self.tabLog)
        self.textEditLog.setReadOnly(True)
        log_layout.addWidget(self.textEditLog)
        self.tabWidget.addTab(self.tabLog, "")

        # --- Help Tab ---
        self.tabHelp = QtWidgets.QWidget()
        help_layout = QtWidgets.QVBoxLayout(self.tabHelp)
        help_layout.setContentsMargins(0, 0, 0, 0)
        self.textBrowserHelp = QTextBrowser(self.tabHelp)
        self.textBrowserHelp.setOpenExternalLinks(False) 
        self.textBrowserHelp.anchorClicked.connect(self._open_link_in_browser)
        help_layout.addWidget(self.textBrowserHelp)
        self.tabWidget.addTab(self.tabHelp, "")

        # Dialog buttons
        self.buttonBox = QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.pushButtonExecute = QPushButton("Execute", self)
        self.pushButtonClose = QPushButton("Close", self)
        self.buttonBox.addButton(self.pushButtonExecute, QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(self.pushButtonClose, QDialogButtonBox.RejectRole)
        self.verticalLayout.addWidget(self.buttonBox)

    def retranslate_ui(self):
        """Apply translations and set tab titles."""
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("SpaceTracePluginDialog", "Space Trace"))
        self.groupBoxDataSource.setTitle(_translate("SpaceTracePluginDialog", "Data Source"))
        self.radioLocalFile.setText(_translate("SpaceTracePluginDialog", "Load from local file"))
        self.radioSpaceTrack.setText(_translate("SpaceTracePluginDialog", "Fetch from SpaceTrack API"))
        self.groupBoxLocalFile.setTitle(_translate("SpaceTracePluginDialog", "Local File Settings"))
        self.pushButtonBrowseData.setText(_translate("SpaceTracePluginDialog", "Browse"))
        self.groupBoxSpaceTrack.setTitle(_translate("SpaceTracePluginDialog", "SpaceTrack API Settings"))
        self.pushButtonSearchSatellites.setText(_translate("SpaceTracePluginDialog", "Search"))
        self.lineEditSatID.setPlaceholderText(_translate("SpaceTracePluginDialog", "Enter NORAD IDs (e.g. 25544, 1000-1003)"))
        self.lineEditLogin.setPlaceholderText(_translate("SpaceTracePluginDialog", "Enter your SpaceTrack account email"))
        self.lineEditPassword.setPlaceholderText(_translate("SpaceTracePluginDialog", "Enter your SpaceTrack account password"))
        self.groupBoxTrackSettings.setTitle(_translate("SpaceTracePluginDialog", "Track Settings"))
        self.groupBoxOutput.setTitle(_translate("SpaceTracePluginDialog", "Output Settings"))
        self.pushButtonBrowseOutput.setText(_translate("SpaceTracePluginDialog", "Browse"))
        self.checkBoxAddLayer.setText(_translate("SpaceTracePluginDialog", "Add created layer to project"))
        self.checkBoxCreateLineLayer.setText(_translate("SpaceTracePluginDialog", "Create line layer"))
        self.groupBoxSaveData.setTitle(_translate("SpaceTracePluginDialog", "Save Received Data"))
        self.checkBoxSaveData.setText(_translate("SpaceTracePluginDialog", "Save TLE/OMM data"))
        self.pushButtonBrowseSaveData.setText(_translate("SpaceTracePluginDialog", "Browse"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabMain), _translate("SpaceTracePluginDialog", "Main"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabLog), _translate("SpaceTracePluginDialog", "Log"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabHelp), _translate("SpaceTracePluginDialog", "Help"))
        self.pushButtonExecute.setText(_translate("SpaceTracePluginDialog", "Execute"))
        self.pushButtonClose.setText(_translate("SpaceTracePluginDialog", "Close"))
        self.quickButton_1_hour.setText(_translate("SpaceTracePluginDialog", "1 hour"))
        self.quickButton_1_day.setText(_translate("SpaceTracePluginDialog", "1 day"))
        self.quickButton_1_week.setText(_translate("SpaceTracePluginDialog", "1 week"))
        self.lineEditDataPath.setPlaceholderText(_translate("SpaceTracePluginDialog", "Specify the path to the TLE/OMM data file(s)"))
        self.lineEditOutputPath.setPlaceholderText(_translate("SpaceTracePluginDialog", "Specify the path to save file (leave empty for temporary layer)"))
        self.lineEditSaveDataPath.setPlaceholderText(_translate("SpaceTracePluginDialog", "Specify the path to save received data"))
        self.labelDuration.setText(_translate("SpaceTracePluginDialog", "Duration (hours):"))