"""
CustomQueryDialog module

This module defines the CustomQueryDialog class, which provides a dialog interface for creating
custom queries to search satellite data via the SpaceTrack API. Users can specify conditions
by selecting fields, operators, and values, which are then used to query the satellite catalog.
"""

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QComboBox, QLineEdit, QPushButton, QHeaderView

# Dictionary mapping satellite catalog fields to their data types (all lowercase)
field_types = {
    'INTLDES': 'string',        # International designation (string)
    'NORAD_CAT_ID': 'int',      # NORAD catalog ID (integer)
    'OBJECT_TYPE': 'string',    # Object type (string)
    'SATNAME': 'string',        # Satellite name (string)
    'COUNTRY': 'string',        # Country of origin (string)
    'LAUNCH': 'date',           # Launch date (date)
    'SITE': 'string',           # Launch site (string)
    'DECAY': 'date',            # Decay date (date)
    'PERIOD': 'decimal',        # Orbital period in minutes (decimal)
    'INCLINATION': 'decimal',   # Orbital inclination in degrees (decimal)
    'APOGEE': 'int',            # Apogee altitude in km (integer)
    'PERIGEE': 'int',           # Perigee altitude in km (integer)
    'COMMENT': 'string',        # Comment (string)
    'COMMENTCODE': 'int',       # Comment code (integer)
    'RCSVALUE': 'int',          # Radar cross-section value (integer)
    'RCS_SIZE': 'string',       # Radar cross-section size (string)
    'FILE': 'int',              # File number (integer)
    'LAUNCH_YEAR': 'int',       # Launch year (integer)
    'LAUNCH_NUM': 'int',        # Launch number (integer)
    'LAUNCH_PIECE': 'string',   # Launch piece (string)
    'CURRENT': 'enum',          # Current status (Y/N)
    'OBJECT_NAME': 'string',    # Object name (string)
    'OBJECT_ID': 'string',      # Object ID (string)
    'OBJECT_NUMBER': 'int'      # Object number (integer)
}

# Mapping of internal field names to human-readable labels
field_labels = {
    'INTLDES': 'International Designator',
    'NORAD_CAT_ID': 'NORAD Catalog ID',
    'OBJECT_TYPE': 'Object Type',
    'SATNAME': 'Satellite Name',
    'COUNTRY': 'Country of Origin',
    'LAUNCH': 'Launch Date',
    'SITE': 'Launch Site',
    'DECAY': 'Decay Date',
    'PERIOD': 'Orbital Period (min)',
    'INCLINATION': 'Inclination (°)',
    'APOGEE': 'Apogee (km)',
    'PERIGEE': 'Perigee (km)',
    'COMMENT': 'Comment',
    'COMMENTCODE': 'Comment Code',
    'RCSVALUE': 'Radar Cross-Section Value',
    'RCS_SIZE': 'Radar Cross-Section Size',
    'FILE': 'File Number',
    'LAUNCH_YEAR': 'Launch Year',
    'LAUNCH_NUM': 'Launch Number',
    'LAUNCH_PIECE': 'Launch Piece',
    'CURRENT': 'Active (Y/N)',
    'OBJECT_NAME': 'Object Name',
    'OBJECT_ID': 'Object ID',
    'OBJECT_NUMBER': 'Object Number'
}

class CustomQueryDialog(QDialog):
    """
    Dialog for creating custom queries to search satellite data.

    Allows users to define multiple conditions by selecting fields, operators, and values.
    The dialog supports dynamic operator selection based on field types and validates
    user input before returning conditions.

    """

    def __init__(self, parent=None, translator=None):
        """
        Initialize the CustomQueryDialog.

        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.translator = translator
        self.setWindowTitle("Custom Query")
        self.resize(600, 400)
        self.layout = QVBoxLayout(self)

        # Initialize table for conditions
        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels(["Attribute", "Field", "Operator", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        # Initialize control buttons
        self.buttonAdd = QPushButton("Add Condition", self)
        self.buttonAdd.clicked.connect(self.add_condition)
        self.layout.addWidget(self.buttonAdd)

        self.buttonRemove = QPushButton("Remove Condition", self)
        self.buttonRemove.clicked.connect(self.remove_condition)
        self.layout.addWidget(self.buttonRemove)

        self.buttonSearch = QPushButton("Search", self)
        self.buttonSearch.clicked.connect(self.accept)
        self.layout.addWidget(self.buttonSearch)

        self.buttonCancel = QPushButton("Cancel", self)
        self.buttonCancel.clicked.connect(self.reject)
        self.layout.addWidget(self.buttonCancel)
        
        self.retranslate_ui()
        
    def retranslate_ui(self):
        """
        Translate all UI strings for localization.
        """
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("CustomQueryDialog", "Custom Query"))
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

        # Update existing rows to reflect translated placeholders
        for row in range(self.table.rowCount()):
            self.update_field_related_widgets(row)
        
    def update_field_related_widgets(self, row):
        field_combo = self.table.cellWidget(row, 1)
        operator_combo = self.table.cellWidget(row, 2)
        value_edit = self.table.cellWidget(row, 3)
        label_item = self.table.item(row, 0)

        field = field_combo.currentText()
        field_type = field_types.get(field, 'string')
        label = field_labels.get(field, field)

        # Update label
        label_item.setText(label)

        # Update operator list
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

        # Update value placeholder
        _translate = QtCore.QCoreApplication.translate
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


    def add_condition(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Label: Human-readable field name
        label_item = QtWidgets.QTableWidgetItem("")
        self.table.setItem(row, 0, label_item)

        # Field selection combo box
        field_combo = QComboBox()
        field_combo.addItems(field_types.keys())
        field_combo.currentIndexChanged.connect(lambda index, r=row: self.update_field_related_widgets(r))
        self.table.setCellWidget(row, 1, field_combo)

        # Operator combo box
        operator_combo = QComboBox()
        self.table.setCellWidget(row, 2, operator_combo)

        # Value input
        value_edit = QLineEdit()
        self.table.setCellWidget(row, 3, value_edit)

        # Initialize label, operator, and placeholder
        self.update_field_related_widgets(row)

    def remove_condition(self):
        """
        Remove selected rows from the conditions table.
        """
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            _translate = QtCore.QCoreApplication.translate
            QtWidgets.QMessageBox.warning(
                self,
                _translate("CustomQueryDialog", "Warning"),
                _translate("CustomQueryDialog", "Please select a row to remove.")
            )
            return
        for index in sorted(selected_rows, reverse=True):
            self.table.removeRow(index.row())

    def update_operator_combo(self, row):
        """
        Update the operator combo box based on the selected field's data type.

        Args:
            row (int): The row index to update.

        Updates the available operators in the combo box to match the data type
        of the selected field (e.g., numeric fields get comparison operators,
        strings get LIKE, enums get equality checks).
        """
        field_combo = self.table.cellWidget(row, 0)
        operator_combo = self.table.cellWidget(row, 1)
        field = field_combo.currentText()
        if field:
            field_type = field_types.get(field, 'string')
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

    def get_conditions(self):
        """
        Retrieve the list of conditions entered by the user.

        Returns:
            list: List of tuples [(field, operator, value), ...] representing the conditions.
                  Returns an empty list if any condition is incomplete.
        """
        conditions = []
        for row in range(self.table.rowCount()):
            field_combo = self.table.cellWidget(row, 1)
            operator_combo = self.table.cellWidget(row, 2)
            value_edit = self.table.cellWidget(row, 3)
            field = field_combo.currentText()
            operator = operator_combo.currentText()
            value = value_edit.text().strip()
            if field and operator and value:
                conditions.append((field, operator, value))
            elif field or operator or value:
                _translate = QtCore.QCoreApplication.translate
                QtWidgets.QMessageBox.warning(
                    self,
                    _translate("CustomQueryDialog", "Warning"),
                    _translate("CustomQueryDialog", "Please fill all fields in each condition.")
                )
                return []
        return conditions