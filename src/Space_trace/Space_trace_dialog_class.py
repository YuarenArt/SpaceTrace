from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialogButtonBox, QPushButton
from PyQt5.QtCore import Qt

class Ui_SpaceTracePluginDialogBase(object):
    def setupUi(self, Dialog):
        # Set up the dialog window properties
        Dialog.setObjectName("SpaceTracePluginDialogBase")
        Dialog.resize(600, 450)

        # Create main vertical layout for the dialog
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")

        # Create tab widget with two tabs: Main and Log
        self.tabWidget = QtWidgets.QTabWidget(Dialog)
        self.tabWidget.setObjectName("tabWidget")
        self.verticalLayout.addWidget(self.tabWidget)

        # ========================
        # First Tab: Main Settings
        # ========================
        self.tabMain = QtWidgets.QWidget()
        self.tabMain.setObjectName("tabMain")
        self.verticalLayoutMain = QtWidgets.QVBoxLayout(self.tabMain)
        self.verticalLayoutMain.setObjectName("verticalLayoutMain")

        # Add input field for satellite NORAD ID
        self.lineEditSatID = QtWidgets.QLineEdit(self.tabMain)
        self.lineEditSatID.setObjectName("lineEditSatID")
        self.verticalLayoutMain.addWidget(self.lineEditSatID)

        # Add input field for SpaceTrack login
        self.lineEditLogin = QtWidgets.QLineEdit(self.tabMain)
        self.lineEditLogin.setObjectName("lineEditLogin")
        self.lineEditLogin.setPlaceholderText("Enter your SpaceTrack account email")
        self.verticalLayoutMain.addWidget(self.lineEditLogin)

        # Add input field for SpaceTrack password
        self.lineEditPassword = QtWidgets.QLineEdit(self.tabMain)
        self.lineEditPassword.setObjectName("lineEditPassword")
        self.lineEditPassword.setPlaceholderText("Enter your SpaceTrack account password")
        self.lineEditPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.verticalLayoutMain.addWidget(self.lineEditPassword)
        
        self.horizontalLayoutData = QtWidgets.QHBoxLayout()
        self.horizontalLayoutData.setObjectName("horizontalLayoutData")
        self.lineEditDataPath = QtWidgets.QLineEdit(self.tabMain)
        self.lineEditDataPath.setObjectName("lineEditDataPath")
        self.lineEditDataPath.setPlaceholderText("Specify the path to the TLE/OMM data file")
        self.horizontalLayoutData.addWidget(self.lineEditDataPath)
        self.pushButtonBrowseData = QtWidgets.QPushButton(self.tabMain)
        self.pushButtonBrowseData.setObjectName("pushButtonBrowseData")
        self.pushButtonBrowseData.setText("Browse")
        self.horizontalLayoutData.addWidget(self.pushButtonBrowseData)
        self.verticalLayoutMain.addLayout(self.horizontalLayoutData)

        self.pushButtonBrowseData.clicked.connect(self.browseDataFile)
        
        # Add date picker for selecting the track day
        self.dateEdit = QtWidgets.QDateEdit(self.tabMain)
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setObjectName("dateEdit")
        self.dateEdit.setDate(QtCore.QDate.currentDate())
        self.verticalLayoutMain.addWidget(self.dateEdit)

        # Add spinner for time step (in minutes)
        self.spinBoxStepMinutes = QtWidgets.QDoubleSpinBox(self.tabMain)
        self.spinBoxStepMinutes.setMinimum(0.1)
        self.spinBoxStepMinutes.setMaximum(60.0)
        self.spinBoxStepMinutes.setSingleStep(5.0)
        self.spinBoxStepMinutes.setValue(0.5)
        self.spinBoxStepMinutes.setObjectName("spinBoxStepMinutes")
        self.verticalLayoutMain.addWidget(self.spinBoxStepMinutes)

        # Create horizontal layout for file path input and Browse button
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEditOutputPath = QtWidgets.QLineEdit(self.tabMain)
        self.lineEditOutputPath.setObjectName("lineEditOutputPath")
        self.horizontalLayout.addWidget(self.lineEditOutputPath)
        self.pushButtonBrowse = QtWidgets.QPushButton(self.tabMain)
        self.pushButtonBrowse.setObjectName("pushButtonBrowse")
        self.horizontalLayout.addWidget(self.pushButtonBrowse)
        self.verticalLayoutMain.addLayout(self.horizontalLayout)

        # Add checkbox for adding the created layer to the project
        self.checkBoxAddLayer = QtWidgets.QCheckBox(self.tabMain)
        self.checkBoxAddLayer.setObjectName("checkBoxAddLayer")
        self.checkBoxAddLayer.setChecked(True)
        self.verticalLayoutMain.addWidget(self.checkBoxAddLayer)
        
        self.checkBoxCreateLineLayer = QtWidgets.QCheckBox(self.tabMain)
        self.checkBoxCreateLineLayer.setObjectName("checkBoxCreateLineLayer")
        self.checkBoxCreateLineLayer.setText("Create line layer")
        self.checkBoxCreateLineLayer.setChecked(True)  
        self.verticalLayoutMain.addWidget(self.checkBoxCreateLineLayer)
        
        # Add checkbox for saving TLE/OMM data
        self.checkBoxSaveData = QtWidgets.QCheckBox(self.tabMain)
        self.checkBoxSaveData.setObjectName("checkBoxSaveData")
        self.checkBoxSaveData.setText("Save TLE/OMM data")
        self.checkBoxSaveData.setChecked(False)  # По умолчанию выключен
        self.verticalLayoutMain.addWidget(self.checkBoxSaveData)

        # Add combo box for selecting data format (TLE or OMM)
        self.comboBoxDataFormat = QtWidgets.QComboBox(self.tabMain)
        self.comboBoxDataFormat.addItems(["TLE", "OMM"])
        self.comboBoxDataFormat.setObjectName("comboBoxDataFormat")
        self.verticalLayoutMain.addWidget(self.comboBoxDataFormat)
        
        # Add the Main tab to the tab widget
        self.tabWidget.addTab(self.tabMain, "")
    
        # ======================
        # Second Tab: Program Log
        # ======================
        self.tabLog = QtWidgets.QWidget()
        self.tabLog.setObjectName("tabLog")
        self.verticalLayoutLog = QtWidgets.QVBoxLayout(self.tabLog)
        self.verticalLayoutLog.setObjectName("verticalLayoutLog")

        # Add read-only text edit widget for displaying logs
        self.textEditLog = QtWidgets.QTextEdit(self.tabLog)
        self.textEditLog.setObjectName("textEditLog")
        self.textEditLog.setReadOnly(True)
        self.verticalLayoutLog.addWidget(self.textEditLog)

        # Add the Log tab to the tab widget
        self.tabWidget.addTab(self.tabLog, "")

        # =========================
        # Custom Dialog Button Box
        # =========================
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.NoButton)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        # Add custom "Execute" button: triggers all main operations
        self.pushButtonExecute = QPushButton(Dialog)
        self.pushButtonExecute.setObjectName("pushButtonExecute")
        self.buttonBox.addButton(self.pushButtonExecute, QDialogButtonBox.AcceptRole)

        self.pushButtonClose = QPushButton(Dialog)
        self.pushButtonClose.setObjectName("pushButtonClose")
        self.buttonBox.addButton(self.pushButtonClose, QDialogButtonBox.RejectRole)

        # Set up translations and connections
        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

        # Connect the "Browse" button to open the file dialog
        self.pushButtonBrowse.clicked.connect(self.browseFile)

    def retranslateUi(self, Dialog):
        # Set up translations for UI elements
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("SpaceTracePluginDialogBase", "Space Trace"))
        self.lineEditSatID.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Enter satellite's NORAD ID"))
        self.lineEditLogin.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Enter your SpaceTrack account email"))
        self.lineEditPassword.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Enter your SpaceTrack account password"))
        self.lineEditOutputPath.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Specify the path to save file (leave empty for temporary layer)"))
        self.pushButtonBrowse.setText(_translate("SpaceTracePluginDialogBase", "Browse"))
        self.checkBoxAddLayer.setText(_translate("SpaceTracePluginDialogBase", "Add created layer to project"))
        self.comboBoxDataFormat.setToolTip(_translate("SpaceTracePluginDialogBase", "Select data format: TLE or OMM"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabMain), _translate("SpaceTracePluginDialogBase", "Main"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabLog), _translate("SpaceTracePluginDialogBase", "Log"))
        self.pushButtonExecute.setText(_translate("SpaceTracePluginDialogBase", "Execute"))
        self.pushButtonClose.setText(_translate("SpaceTracePluginDialogBase", "Close"))
        self.checkBoxCreateLineLayer.setText(_translate("SpaceTracePluginDialogBase", "Create line layer"))
        self.checkBoxSaveData.setText(_translate("SpaceTracePluginDialogBase", "Save received data"))
        self.lineEditDataPath.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Specify the path to the TLE/OMM data file"))

    def browseFile(self):
        file, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Select File", "", "Shapefiles (*.shp);;GeoPackage (*.gpkg);;GeoJSON (*.geojson);;All Files (*)")
        if file:
            self.lineEditOutputPath.setText(file)
            
    def browseDataFile(self):
        file, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Select File", "", "Text Files (*.txt);;JSON Files (*.json);;All Files (*)")
        if file:
            self.lineEditDataPath.setText(file)

    def appendLog(self, message):
        # Append message to the log widget
        self.textEditLog.append(message)