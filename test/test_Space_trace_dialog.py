# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'yuaren@yandex.ru'
__date__ = '2025-02-14'
__copyright__ = 'Copyright 2025, Yuriy Malyshev'

import os
import unittest
from unittest.mock import Mock, patch

from qgis.PyQt.QtWidgets import QDialogButtonBox, QDialog
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProject

from src.Space_trace.Space_trace import SpaceTracePlugin
from test.utilities import get_qgis_app

QGIS_APP = get_qgis_app()

class SpaceTracePluginDialogTest(unittest.TestCase):
    """Test dialog works."""

    def setUp(self):
        """Runs before each test."""
        self.iface = Mock()
        self.iface.mainWindow.return_value = Mock()
        self.plugin = SpaceTracePlugin(self.iface)
        with patch('qgis.PyQt.QtCore.QSettings') as mock_settings:
            mock_settings.return_value.value.return_value = "en_US"
            self.plugin = SpaceTracePlugin(self.iface)
            
        self.plugin.dlg = Mock()

    def tearDown(self):
        """Runs after each test."""
        self.plugin = None
        
    def test_init(self):
        """Test plugin initialization."""
        self.assertIsNotNone(self.plugin.iface)
        self.assertTrue(os.path.exists(self.plugin.plugin_dir))
        self.assertEqual(self.plugin.menu, self.plugin.tr('Space trace'))
        self.assertTrue(hasattr(self.plugin, 'logger'))
        self.assertIsInstance(self.plugin.actions, list)
        self.assertEqual(len(self.plugin.actions), 0)
        
    def test_init_logger(self):
        """Test logger initialization."""
        self.plugin._init_logger()
        self.assertEqual(self.plugin.logger.name, "SpaceTracePlugin")
        self.assertEqual(self.plugin.logger.level, 10)  
        self.assertTrue(len(self.plugin.logger.handlers) > 0)
        log_file = os.path.join(self.plugin.plugin_dir, "SpaceTracePlugin.log")
        self.assertTrue(os.path.exists(os.path.dirname(log_file)))

    def test_init_localization(self):
        """Test localization initialization."""
        with patch('qgis.PyQt.QtCore.QSettings') as mock_settings:
            mock_settings.return_value.value.return_value = "en_US"
            self.plugin._init_localization()
            self.assertTrue(hasattr(self.plugin, 'translator'))
            
    def test_unload(self):
        """Test unloading the plugin."""
        self.plugin.add_action(
            icon_path=':/plugins/Space_trace/icon.png',
            text="Test Action",
            callback=lambda: None,
            parent=self.iface.mainWindow()
        )
        self.plugin.unload()
        self.iface.removePluginVectorMenu.assert_called_once()
        self.iface.removeToolBarIcon.assert_called_once()
        self.assertEqual(len(self.plugin.actions), 1)
        
    def test_validate_inputs_valid(self):
        """Test input validation with valid inputs."""
        inputs = {
            'data_file_path': '',
            'sat_id_text': '25544', 
            'track_day': '2025-03-28',
            'step_minutes': 1,
            'output_path': 'test.shp',
            'add_layer': True,
            'login': 'test@example.com',
            'password': 'password',
            'data_format': 'TLE',
            'create_line_layer': True,
            'save_data': False,
            'save_data_path': None
        }
        sat_id, file_format = self.plugin._validate_inputs(inputs)
        self.assertEqual(sat_id, 25544)
        self.assertEqual(file_format, 'shp')
        
    def test_validate_inputs_invalid_sat_id(self):
        """Test input validation with invalid satellite ID."""
        inputs = {
            'data_file_path': '',
            'sat_id_text': 'invalid',
            'track_day': '2025-03-28',
            'step_minutes': 1,
            'output_path': 'test.shp',
            'add_layer': True,
            'login': 'test@example.com',
            'password': 'password',
            'data_format': 'TLE',
            'create_line_layer': True,
            'save_data': False,
            'save_data_path': None
        }
        with self.assertRaises(Exception) as context:
            self.plugin._validate_inputs(inputs)
        self.assertIn("Invalid NORAD ID", str(context.exception))

    def test_load_and_add_layer(self):
        """Test loading and adding a layer."""
        with patch('qgis.core.QgsVectorLayer') as mock_layer:
            mock_layer_instance = mock_layer.return_value
            mock_layer_instance.isValid.return_value = True
            mock_layer_instance.featureCount.return_value = 10
            self.plugin._load_and_add_layer('test.shp', 'point')
            QgsProject.instance().addMapLayer.assert_called_once()
            self.plugin.log_message.assert_called_with("Point layer loaded with 10 features.", "INFO")

if __name__ == "__main__":
    suite = unittest.makeSuite(SpaceTracePluginDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

