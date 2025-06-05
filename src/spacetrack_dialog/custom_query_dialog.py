from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QVBoxLayout, QTableWidget, QLineEdit, QPushButton, QHeaderView,
    QDialog, QComboBox, QMessageBox, QTableWidgetItem
)
from PyQt5.QtCore import QCoreApplication

from datetime import datetime

# Dictionary mapping satellite catalog fields to their data types
field_types = {
    'INTLDES': 'string', 'NORAD_CAT_ID': 'int', 'OBJECT_TYPE': 'string', 'SATNAME': 'string',
    'COUNTRY': 'string', 'LAUNCH': 'date', 'SITE': 'string', 'DECAY': 'date',
    'PERIOD': 'decimal', 'INCLINATION': 'decimal', 'APOGEE': 'int', 'PERIGEE': 'int',
    'COMMENT': 'string', 'COMMENTCODE': 'int', 'RCSVALUE': 'int', 'RCS_SIZE': 'string',
    'FILE': 'int', 'LAUNCH_YEAR': 'int', 'LAUNCH_NUM': 'int', 'LAUNCH_PIECE': 'string',
    'CURRENT': 'enum', 'OBJECT_NAME': 'string', 'OBJECT_ID': 'string', 'OBJECT_NUMBER': 'int'
}

# Dictionary mapping field names to translatable labels
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
    """UI setup class for CustomQueryDialog."""

    def setup_ui(self, dialog):
        """Set up UI components for the custom query dialog."""
        dialog.setWindowTitle(QtCore.QCoreApplication.translate("CustomQueryDialog", "Custom Query"))
        dialog.resize(600, 400)
        self.layout = QVBoxLayout(dialog)

        self.table = QTableWidget(0, 4, dialog)
        self.table.setHorizontalHeaderLabels([
            QtCore.QCoreApplication.translate("CustomQueryDialog", "Attribute"),
            QtCore.QCoreApplication.translate("CustomQueryDialog", "Field"),
            QtCore.QCoreApplication.translate("CustomQueryDialog", "Operator"),
            QtCore.QCoreApplication.translate("CustomQueryDialog", "Value")
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        self.button_add = QPushButton(QtCore.QCoreApplication.translate("CustomQueryDialog", "Add Condition"), dialog)
        self.button_remove = QPushButton(QtCore.QCoreApplication.translate("CustomQueryDialog", "Remove Condition"), dialog)
        self.button_search = QPushButton(QtCore.QCoreApplication.translate("CustomQueryDialog", "Search"), dialog)
        self.button_cancel = QPushButton(QtCore.QCoreApplication.translate("CustomQueryDialog", "Cancel"), dialog)

        for button in (self.button_add, self.button_remove, self.button_search, self.button_cancel):
            self.layout.addWidget(button)

    def retranslate_ui(self, dialog):
        """Translate all UI strings for localization."""
        _translate = QtCore.QCoreApplication.translate
        dialog.setWindowTitle(_translate("CustomQueryDialog", "Custom Query"))
        self.table.setHorizontalHeaderLabels([
            _translate("CustomQueryDialog", "Attribute"),
            _translate("CustomQueryDialog", "Field"),
            _translate("CustomQueryDialog", "Operator"),
            _translate("CustomQueryDialog", "Value")
        ])
        self.button_add.setText(_translate("CustomQueryDialog", "Add Condition"))
        self.button_remove.setText(_translate("CustomQueryDialog", "Remove Condition"))
        self.button_search.setText(_translate("CustomQueryDialog", "Search"))
        self.button_cancel.setText(_translate("CustomQueryDialog", "Cancel"))

class CustomQueryDialog(QDialog):
    """Dialog for building custom queries with multiple conditions."""

    def __init__(self, parent=None, translator=None):
        """Initialize the custom query dialog."""
        super().__init__(parent)
        self.translator = translator
        self.ui = Ui_CustomQueryDialog()
        self.ui.setup_ui(self)
        self.ui.retranslate_ui(self)
        self.saved_conditions = []

        self._setup_connections()

    def _setup_connections(self):
        """Set up signal-slot connections for UI elements."""
        self.ui.button_add.clicked.connect(self.add_condition)
        self.ui.button_remove.clicked.connect(self.remove_condition)
        self.ui.button_search.clicked.connect(self.accept)
        self.ui.button_cancel.clicked.connect(self.reject)

    def set_saved_conditions(self, conditions):
        """Set saved conditions before showing the dialog."""
        self.saved_conditions = conditions.copy()
        self._restore_conditions()

    def get_saved_conditions(self):
        """Return the list of saved conditions."""
        return self.saved_conditions

    def add_condition(self):
        """Add a new condition row to the table."""
        row = self.ui.table.rowCount()
        self.ui.table.insertRow(row)

        label_item = QTableWidgetItem("")
        label_item.setFlags(label_item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.ui.table.setItem(row, 0, label_item)

        field_combo = QComboBox()
        field_combo.addItems(field_types.keys())
        field_combo.currentIndexChanged.connect(lambda index, r=row: self._update_field_related_widgets(r))
        self.ui.table.setCellWidget(row, 1, field_combo)

        operator_combo = QComboBox()
        self.ui.table.setCellWidget(row, 2, operator_combo)

        value_edit = QLineEdit()
        self.ui.table.setCellWidget(row, 3, value_edit)

        self._update_field_related_widgets(row)

    def _update_field_related_widgets(self, row):
        """Update operator options and value placeholder based on selected field."""
        field_combo = self.ui.table.cellWidget(row, 1)
        operator_combo = self.ui.table.cellWidget(row, 2)
        value_edit = self.ui.table.cellWidget(row, 3)
        label_item = self.ui.table.item(row, 0)

        field = field_combo.currentText()
        field_type = field_types.get(field, 'string')
        label = field_labels.get(field, field)
        label_item.setText(self._translate("CustomQueryDialog", label))

        operators = {
            'int': ['=', '!=', '<', '>'],
            'decimal': ['=', '!=', '<', '>'],
            'date': ['=', '!=', '<', '>', 'IS NULL', 'IS NOT NULL'],
            'string': ['=', '!=', 'LIKE'],
            'enum': ['=', '!='],
        }.get(field_type, [])
        operator_combo.clear()
        operator_combo.addItems(operators)

        placeholders = {
            'int': self._translate("CustomQueryDialog", "Enter an integer (e.g., 25544)"),
            'decimal': self._translate("CustomQueryDialog", "Enter a decimal (e.g., 90.5)"),
            'date': self._translate("CustomQueryDialog", "Enter date as YYYY-MM-DD (e.g., 2023-01-01) or NULL"),
            'enum': self._translate("CustomQueryDialog", "Enter Y or N"),
            'string': self._translate("CustomQueryDialog", "Enter a string (e.g., STARLINK)")
        }
        value_edit.setPlaceholderText(placeholders.get(field_type, ""))

        if operator_combo.currentText() in ('IS NULL', 'IS NOT NULL'):
            value_edit.setText("")
            value_edit.setDisabled(True)
        else:
            value_edit.setDisabled(False)

    def remove_condition(self):
        """Remove the selected condition row or the last one if none selected."""
        selected_rows = sorted([index.row() for index in self.ui.table.selectionModel().selectedRows()], reverse=True)
        if selected_rows:
            for row in selected_rows:
                self.ui.table.removeRow(row)
        elif self.ui.table.rowCount() > 0:
            self.ui.table.removeRow(self.ui.table.rowCount() - 1)
        else:
            self._warn("No conditions to remove.")
        self._update_saved_conditions_silent()

    def get_conditions(self, silent=False):
        """Retrieve and validate conditions from the table."""
        conditions = []
        for row in range(self.ui.table.rowCount()):
            field_combo = self.ui.table.cellWidget(row, 1)
            operator_combo = self.ui.table.cellWidget(row, 2)
            value_edit = self.ui.table.cellWidget(row, 3)
            field = field_combo.currentText()
            operator = operator_combo.currentText()
            value = value_edit.text().strip()

            field_type = field_types.get(field, 'string')

            if operator in ('IS NULL', 'IS NOT NULL'):
                conditions.append((field, operator, None))
                continue

            if not (field and operator and value):
                if not silent:
                    self._warn("Please fill all fields in each condition.")
                return []

            if field_type == 'int':
                if not self._is_valid_int(value):
                    if not silent:
                        self._warn(f"Invalid integer value for {field}: {value}")
                    return []
            elif field_type == 'decimal':
                if not self._is_valid_decimal(value):
                    if not silent:
                        self._warn(f"Invalid decimal value for {field}: {value}")
                    return []
            elif field_type == 'date':
                if value.upper() != 'NULL' and not self._is_valid_date(value):
                    if not silent:
                        self._warn(f"Invalid date format for {field}: {value} (expected YYYY-MM-DD or NULL)")
                    return []

            elif field_type == 'enum':
                if value not in ['Y', 'N']:
                    if not silent:
                        self._warn(f"Invalid value for {field}: {value}. Must be 'Y' or 'N'.")
                    return []

            conditions.append((field, operator, value))
        return conditions

    def _is_valid_int(self, value):
        """Check if the value is a valid integer."""
        try:
            int(value)
            return True
        except ValueError:
            return False

    def _is_valid_decimal(self, value):
        """Check if the value is a valid decimal."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _is_valid_date(self, value):
        """Check if the value is a valid date in YYYY-MM-DD format."""
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _restore_conditions(self):
        """Restore saved conditions into the table."""
        self.ui.table.setRowCount(0)
        for field, operator, value in self.saved_conditions:
            row = self.ui.table.rowCount()
            self.ui.table.insertRow(row)
            label_item = QTableWidgetItem(self._translate("CustomQueryDialog", field_labels.get(field, field)))
            label_item.setFlags(label_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.ui.table.setItem(row, 0, label_item)

            field_combo = QComboBox()
            field_combo.addItems(field_types.keys())
            field_combo.setCurrentText(field)
            field_combo.currentIndexChanged.connect(lambda index, r=row: self._update_field_related_widgets(r))
            self.ui.table.setCellWidget(row, 1, field_combo)

            operator_combo = QComboBox()
            self.ui.table.setCellWidget(row, 2, operator_combo)

            value_edit = QLineEdit()
            if value is not None:
                value_edit.setText(value)
            self.ui.table.setCellWidget(row, 3, value_edit)

            self._update_field_related_widgets(row)
            operator_combo.setCurrentText(operator)

    def _update_saved_conditions_silent(self):
        """Update saved conditions without triggering validation."""
        self.saved_conditions = self.get_conditions(silent=True)

    def accept(self):
        """Accept the dialog if conditions are valid."""
        conditions = self.get_conditions()
        if conditions or not self.ui.table.rowCount():
            self.saved_conditions = conditions
            super().accept()

    def reject(self):
        """Reject the dialog and update saved conditions."""
        self._update_saved_conditions_silent()
        super().reject()

    def _translate(self, context, text):
        """Translate text using Qt's translation system."""
        return QtCore.QCoreApplication.translate(context, text)

    def _warn(self, message):
        """Display a warning message."""
        QtWidgets.QMessageBox.warning(self, self._translate("CustomQueryDialog", "Warning"),
                                      self._translate("CustomQueryDialog", message))
