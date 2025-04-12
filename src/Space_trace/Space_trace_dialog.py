# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Space_trace_dialog_base.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets
from .Space_trace_dialog_class import Ui_SpaceTracePluginDialogBase

class SpaceTracePluginDialog(QtWidgets.QDialog, Ui_SpaceTracePluginDialogBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.lineEditSatID.setValidator(QtGui.QIntValidator(1, 999999, self))
        
        
    def appendLog(self, message):
        self.textEditLog.append(message)
        
    def switch_to_log_tab(self):
        """
        Switch the tab widget to the Log tab.
        """
        self.tabWidget.setCurrentIndex(1)
        
    def get_inputs(self):
        """
        Retrieve all user inputs from the dialog.

        Returns:
            dict: Dictionary containing all input values.
        """
        return {
            "data_file_path": self.lineEditDataPath.text().strip() if self.radioLocalFile.isChecked() else "",
            "sat_id_text": self.lineEditSatID.text().strip(),
            "start_datetime": self.dateTimeEdit.dateTime().toPyDateTime(),
            "duration_hours": self.spinBoxDuration.value(),
            "step_minutes": self.spinBoxStepMinutes.value(),
            "output_path": self.lineEditOutputPath.text().strip(),
            "add_layer": self.checkBoxAddLayer.isChecked(),
            "login": self.lineEditLogin.text().strip() if not self.radioLocalFile.isChecked() else "",
            "password": self.lineEditPassword.text().strip() if not self.radioLocalFile.isChecked() else "",
            "data_format": (self.comboBoxDataFormatLocal.currentText() if self.radioLocalFile.isChecked()
                           else self.comboBoxDataFormatSpaceTrack.currentText()),
            "create_line_layer": self.checkBoxCreateLineLayer.isChecked(),
            "save_data": self.checkBoxSaveData.isChecked(),
            "save_data_path": self.lineEditSaveDataPath.text().strip() if self.checkBoxSaveData.isChecked() else ""
        }