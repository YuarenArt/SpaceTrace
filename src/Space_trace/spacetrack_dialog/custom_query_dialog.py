from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QTableWidget, QLineEdit, QPushButton, QHeaderView
from PyQt5.QtWidgets import QDialog, QComboBox, QMessageBox, QTableWidgetItem
from PyQt5.QtCore import QCoreApplication

# Dictionary mapping satellite catalog fields to their data types
field_types = {
    'INTLDES': 'string', 'NORAD_CAT_ID': 'int', 'OBJECT_TYPE': 'string', 'SATNAME': 'string',
    'COUNTRY': 'string', 'LAUNCH': 'date', 'SITE': 'string', 'DECAY': 'date',
    'PERIOD': 'decimal', 'INCLINATION': 'decimal', 'APOGEE': 'int', 'PERIGEE': 'int',
    'COMMENT': 'string', 'COMMENTCODE': 'int', 'RCSVALUE': 'int', 'RCS_SIZE': 'string',
    'FILE': 'int', 'LAUNCH_YEAR': 'int', 'LAUNCH_NUM': 'int', 'LAUNCH_PIECE': 'string',
    'CURRENT': 'enum', 'OBJECT_NAME': 'string', 'OBJECT_ID': 'string', 'OBJECT_NUMBER': 'int'
}

# Dictionary mapping field names to translatable keys
field_labels = {
    'INTLDES': QCoreApplication.translate("CustomQueryDialog", "International Designator"),
    'NORAD_CAT_ID': QCoreApplication.translate("CustomQueryDialog", "NORAD Catalog ID"),
    'OBJECT_TYPE': QCoreApplication.translate("CustomQueryDialog", "Object Type"),
    'SATNAME': QCoreApplication.translate("CustomQueryDialog", "Satellite Name"),
    'COUNTRY': QCoreApplication.translate("CustomQueryDialog", "Country of Origin"),
    'LAUNCH': QCoreApplication.translate("CustomQueryDialog", "Launch Date"),
    'SITE': QCoreApplication.translate("CustomQueryDialog", "Launch Site"),
    'DECAY': QCoreApplication.translate("CustomQueryDialog", "Decay Date"),
    'PERIOD': QCoreApplication.translate("CustomQueryDialog", "Orbital Period (min)"),
    'INCLINATION': QCoreApplication.translate("CustomQueryDialog", "Inclination (°)"),
    'APOGEE': QCoreApplication.translate("CustomQueryDialog", "Apogee (km)"),
    'PERIGEE': QCoreApplication.translate("CustomQueryDialog", "Perigee (km)"),
    'COMMENT': QCoreApplication.translate("CustomQueryDialog", "Comment"),
    'COMMENTCODE': QCoreApplication.translate("CustomQueryDialog", "Comment Code"),
    'RCSVALUE': QCoreApplication.translate("CustomQueryDialog", "Radar Cross-Section Value"),
    'RCS_SIZE': QCoreApplication.translate("CustomQueryDialog", "Radar Cross-Section Size"),
    'FILE': QCoreApplication.translate("CustomQueryDialog", "File Number"),
    'LAUNCH_YEAR': QCoreApplication.translate("CustomQueryDialog", "Launch Year"),
    'LAUNCH_NUM': QCoreApplication.translate("CustomQueryDialog", "Launch Number"),
    'LAUNCH_PIECE': QCoreApplication.translate("CustomQueryDialog", "Launch Piece"),
    'CURRENT': QCoreApplication.translate("CustomQueryDialog", "Active (Y/N)"),
    'OBJECT_NAME': QCoreApplication.translate("CustomQueryDialog", "Object Name"),
    'OBJECT_ID': QCoreApplication.translate("CustomQueryDialog", "Object ID"),
    'OBJECT_NUMBER': QCoreApplication.translate("CustomQueryDialog", "Object Number")
}


class Ui_CustomQueryDialog:
    def setup_ui(self, Dialog):
        Dialog.setWindowTitle("Custom Query")
        Dialog.resize(600, 400)
        self.layout = QVBoxLayout(Dialog)

        self.table = QTableWidget(0, 4, Dialog)
        self.table.setHorizontalHeaderLabels(["Attribute", "Field", "Operator", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        self.buttonAdd = QPushButton("Add Condition", Dialog)
        self.layout.addWidget(self.buttonAdd)

        self.buttonRemove = QPushButton("Remove Condition", Dialog)
        self.layout.addWidget(self.buttonRemove)

        self.buttonSearch = QPushButton("Search", Dialog)
        self.layout.addWidget(self.buttonSearch)

        self.buttonCancel = QPushButton("Cancel", Dialog)
        self.layout.addWidget(self.buttonCancel)

    def retranslate_ui(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("CustomQueryDialog", "Custom Query"))
        self.table.setHorizontalHeaderLabels([
            _translate("CustomQueryDialog", "Attribute"),
            _translate("CustomQueryDialog", "Field"),
            _translate("CustomQueryDialog", "Operator"),
            _translate("CustomQueryDialog", "Value")
        ])
        self.buttonAdd.setText(_translate("CustomQueryDialog", "Add Condition"))
        self.buttonRemove.setText(_translate("CustomQueryDialog", "Remove Condition"))
        self.buttonSearch.setText(_translate("CustomQueryDialog", "Search"))
        self.buttonCancel.setText(_translate("CustomQueryDialog", "Cancel"))

class CustomQueryDialog(QDialog):
    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.translator = translator
        self.ui = Ui_CustomQueryDialog()
        self.ui.setup_ui(self)
        self.ui.retranslate_ui(self)

        self.saved_conditions = []

        self.ui.buttonAdd.clicked.connect(self.add_condition)
        self.ui.buttonRemove.clicked.connect(self.remove_condition)
        self.ui.buttonSearch.clicked.connect(self.accept)
        self.ui.buttonCancel.clicked.connect(self.reject)

    def set_saved_conditions(self, conditions):
        """Set saved conditions before showing the dialog."""
        self.saved_conditions = conditions.copy()
        self.restore_conditions()

    def get_saved_conditions(self):
        """Get conditions after dialog is closed."""
        return self.saved_conditions

    def add_condition(self):
        row = self.ui.table.rowCount()
        self.ui.table.insertRow(row)

        label_item = QTableWidgetItem("")
        self.ui.table.setItem(row, 0, label_item)

        field_combo = QComboBox()
        field_combo.addItems(field_types.keys())
        field_combo.currentIndexChanged.connect(lambda index, r=row: self.update_field_related_widgets(r))
        self.ui.table.setCellWidget(row, 1, field_combo)

        operator_combo = QComboBox()
        self.ui.table.setCellWidget(row, 2, operator_combo)

        value_edit = QLineEdit()
        self.ui.table.setCellWidget(row, 3, value_edit)

        self.update_field_related_widgets(row)

    def update_field_related_widgets(self, row):
        table = self.ui.table
        field_combo = table.cellWidget(row, 1)
        operator_combo = table.cellWidget(row, 2)
        value_edit = table.cellWidget(row, 3)
        label_item = table.item(row, 0)

        field = field_combo.currentText()
        field_type = field_types.get(field, 'string')
        label = field_labels.get(field, field)
        
        _translate = QCoreApplication.translate
        translated_label = _translate("CustomQueryDialog", label)
        label_item.setText(translated_label)

        if field_type in ['int', 'decimal', 'date']:
            operators = ['=', '!=', '<', '>']
        elif field_type == 'string':
            operators = ['=', '!=', 'LIKE']
        elif field_type == 'enum':
            operators = ['=', '!=']
        else:
            operators = []

        operator_combo.clear()
        operator_combo.addItems(operators)

        _translate = QCoreApplication.translate
        if field_type == 'int':
            value_edit.setPlaceholderText(_translate("CustomQueryDialog", "Enter an integer (e.g., 25544)"))
        elif field_type == 'decimal':
            value_edit.setPlaceholderText(_translate("CustomQueryDialog", "Enter a decimal (e.g., 90.5)"))
        elif field_type == 'date':
            value_edit.setPlaceholderText(_translate("CustomQueryDialog", "Enter date as YYYY-MM-DD (e.g., 2023-01-01)"))
        elif field_type == 'enum':
            value_edit.setPlaceholderText(_translate("CustomQueryDialog", "Enter Y or N"))
        else:
            value_edit.setPlaceholderText(_translate("CustomQueryDialog", "Enter a string (e.g., STARLINK)"))

    def remove_condition(self):
        selected_rows = self.ui.table.selectionModel().selectedRows()
        if selected_rows:
            # Remove selected rows in reverse order to avoid index shifting
            for index in sorted(selected_rows, reverse=True):
                self.ui.table.removeRow(index.row())
        else:
            # If no row is selected, remove the last row if there are any
            if self.ui.table.rowCount() > 0:
                self.ui.table.removeRow(self.ui.table.rowCount() - 1)
            else:
                _translate = QCoreApplication.translate
                QMessageBox.warning(
                    self,
                    _translate("CustomQueryDialog", "Warning"),
                    _translate("CustomQueryDialog", "No conditions to remove.")
                )
        # Update saved conditions without triggering validation
        self._update_saved_conditions_silent()

    def get_conditions(self, silent=False):
        conditions = []
        table = self.ui.table
        for row in range(table.rowCount()):
            field_combo = table.cellWidget(row, 1)
            operator_combo = table.cellWidget(row, 2)
            value_edit = table.cellWidget(row, 3)
            field = field_combo.currentText()
            operator = operator_combo.currentText()
            value = value_edit.text().strip()
            if field and operator and value:
                conditions.append((field, operator, value))
            elif (field or operator or value) and not silent:
                _translate = QCoreApplication.translate
                QMessageBox.warning(
                    self,
                    _translate("CustomQueryDialog", "Warning"),
                    _translate("CustomQueryDialog", "Please fill all fields in each condition.")
                )
                return []
        return conditions


    def restore_conditions(self):
        self.ui.table.setRowCount(0)
        if not self.saved_conditions:
            return
        for field, operator, value in self.saved_conditions:
            row = self.ui.table.rowCount()
            self.ui.table.insertRow(row)

            label_item = QTableWidgetItem("")
            self.ui.table.setItem(row, 0, label_item)

            field_combo = QComboBox()
            field_combo.addItems(field_types.keys())
            field_combo.setCurrentText(field)
            field_combo.currentIndexChanged.connect(lambda index, r=row: self.update_field_related_widgets(r))
            self.ui.table.setCellWidget(row, 1, field_combo)

            operator_combo = QComboBox()
            self.ui.table.setCellWidget(row, 2, operator_combo)

            value_edit = QLineEdit()
            value_edit.setText(value)
            self.ui.table.setCellWidget(row, 3, value_edit)

            self.update_field_related_widgets(row)
            operator_combo.setCurrentText(operator)
    
    def _update_saved_conditions_silent(self):
        self.saved_conditions = self.get_conditions(silent=True)

    def accept(self):
        conditions = self.get_conditions()
        if conditions or not self.ui.table.rowCount():
            self.saved_conditions = conditions
            super().accept()

    def reject(self):
        self._update_saved_conditions_silent()
        super().reject()