# coding=utf-8
"""Common functionality used by regression tests."""

import sys
import logging

LOGGER = logging.getLogger('QGIS')
QGIS_APP = None  # Static variable used to hold hand to running QGIS app
CANVAS = None
PARENT = None
IFACE = None

def get_qgis_app():
    """ Start one QGIS application to test against.

    :returns: Handle to QGIS app, canvas, iface, and parent. If there are any
        errors, the tuple members will be returned as None.
    :rtype: (QgsApplication, CANVAS, IFACE, PARENT)

    If QGIS is already running the handle to that app will be returned.
    """
    
    try:
        from qgis.PyQt import QtGui, QtCore
        from qgis.core import QgsApplication
        from qgis.gui import QgsMapCanvas
        from .qgis_interface import QgisInterface
    except ImportError:
        return None, None, None, None

    global QGIS_APP  # pylint: disable=W0603

    # Create QApplication if it's not already running
    if QGIS_APP is None:
        app = QtGui.QApplication(sys.argv)  # Ensure QApplication is created
        gui_flag = True  # All tests will run QGIS in GUI mode
        QGIS_APP = QgsApplication(sys.argv, gui_flag)
        QGIS_APP.initQgis()
        s = QGIS_APP.showSettings()
        LOGGER.debug(s)

    global PARENT  # pylint: disable=W0603
    if PARENT is None:
        PARENT = QtGui.QWidget()

    global CANVAS  # pylint: disable=W0603
    if CANVAS is None:
        CANVAS = QgsMapCanvas(PARENT)
        CANVAS.resize(QtCore.QSize(400, 400))

    global IFACE  # pylint: disable=W0603
    if IFACE is None:
        IFACE = QgisInterface(CANVAS)

    return QGIS_APP, CANVAS, IFACE, PARENT
