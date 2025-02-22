from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SpaceTracePluginDialogBase(object):
    def setupUi(self, SpaceTracePluginDialogBase):
        SpaceTracePluginDialogBase.setObjectName("SpaceTracePluginDialogBase")
        SpaceTracePluginDialogBase.resize(855, 565)
        self.verticalLayout = QtWidgets.QVBoxLayout(SpaceTracePluginDialogBase)
        self.verticalLayout.setObjectName("verticalLayout")
        
        # Input field for the satellite NORAD ID
        self.lineEditSatID = QtWidgets.QLineEdit(SpaceTracePluginDialogBase)
        self.lineEditSatID.setObjectName("lineEditSatID")
        self.verticalLayout.addWidget(self.lineEditSatID)
        
        # Input field for SpaceTrack account email (login)
        self.lineEditLogin = QtWidgets.QLineEdit(SpaceTracePluginDialogBase)
        self.lineEditLogin.setObjectName("lineEditLogin")
        self.lineEditLogin.setPlaceholderText("Enter your SpaceTrack account email")
        self.verticalLayout.addWidget(self.lineEditLogin)
        
        # Input field for SpaceTrack account password
        self.lineEditPassword = QtWidgets.QLineEdit(SpaceTracePluginDialogBase)
        self.lineEditPassword.setObjectName("lineEditPassword")
        self.lineEditPassword.setPlaceholderText("Enter your SpaceTrack account password")
        self.lineEditPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.verticalLayout.addWidget(self.lineEditPassword)
        
        # Date picker with calendar popup; defaults to current system date
        self.dateEdit = QtWidgets.QDateEdit(SpaceTracePluginDialogBase)
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setObjectName("dateEdit")
        self.dateEdit.setDate(QtCore.QDate.currentDate())
        self.verticalLayout.addWidget(self.dateEdit)
        
        # Input field for selecting the time step (in minutes)
        self.spinBoxStepMinutes = QtWidgets.QDoubleSpinBox(SpaceTracePluginDialogBase)
        self.spinBoxStepMinutes.setMinimum(0.1)
        self.spinBoxStepMinutes.setMaximum(60.0)
        self.spinBoxStepMinutes.setSingleStep(5.0)
        self.spinBoxStepMinutes.setProperty("value", 0.5)
        self.spinBoxStepMinutes.setObjectName("spinBoxStepMinutes")
        self.verticalLayout.addWidget(self.spinBoxStepMinutes)
        
        # Horizontal layout for the file path input and "Browse" button
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        
        # Input field for specifying the path to save the shapefile
        self.lineEditOutputPath = QtWidgets.QLineEdit(SpaceTracePluginDialogBase)
        self.lineEditOutputPath.setObjectName("lineEditOutputPath")
        self.horizontalLayout.addWidget(self.lineEditOutputPath)
        
        # "Browse" button to open a file dialog for file selection
        self.pushButtonBrowse = QtWidgets.QPushButton(SpaceTracePluginDialogBase)
        self.pushButtonBrowse.setObjectName("pushButtonBrowse")
        self.horizontalLayout.addWidget(self.pushButtonBrowse)
        
        # Add the horizontal layout to the main vertical layout
        self.verticalLayout.addLayout(self.horizontalLayout)
        
        # Checkbox for automatically adding the created layer to the project (default enabled)
        self.checkBoxAddLayer = QtWidgets.QCheckBox(SpaceTracePluginDialogBase)
        self.checkBoxAddLayer.setObjectName("checkBoxAddLayer")
        self.checkBoxAddLayer.setChecked(True)
        self.verticalLayout.addWidget(self.checkBoxAddLayer)
        
        # Standard dialog buttons (OK/Cancel)
        self.buttonBox = QtWidgets.QDialogButtonBox(SpaceTracePluginDialogBase)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(SpaceTracePluginDialogBase)
        self.buttonBox.accepted.connect(SpaceTracePluginDialogBase.accept)  # type: ignore
        self.buttonBox.rejected.connect(SpaceTracePluginDialogBase.reject)  # type: ignore
        QtCore.QMetaObject.connectSlotsByName(SpaceTracePluginDialogBase)
        
        # Connect the "Browse" button signal to the slot for opening the file dialog
        self.pushButtonBrowse.clicked.connect(self.browseFile)

    def retranslateUi(self, SpaceTracePluginDialogBase):
        _translate = QtCore.QCoreApplication.translate
        SpaceTracePluginDialogBase.setWindowTitle(_translate("SpaceTracePluginDialogBase", "Space Trace"))
        self.lineEditSatID.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Enter satellite's NORAD ID"))
        self.lineEditOutputPath.setPlaceholderText(_translate("SpaceTracePluginDialogBase", "Specify the path to save the shapefile."))
        self.pushButtonBrowse.setText(_translate("SpaceTracePluginDialogBase", "Browse (leave empty for temporary layer)"))
        self.checkBoxAddLayer.setText(_translate("SpaceTracePluginDialogBase", "Add created layer to project"))
    
    def browseFile(self):
        file, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Select File", "", "Shapefiles (*.shp);;All Files (*)")
        if file:
            self.lineEditOutputPath.setText(file)
