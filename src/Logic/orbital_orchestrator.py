"""
This module contains the OrbitalOrchestrator class that orchestrates the process
of retrieving TLE/OMM data and generating orbital track layers.
"""
import datetime
from datetime import date
import os
import json
import logging


from .spacetrack_client import SpacetrackClientWrapper
from .orbital_handler import OrbitalLogicHandler

class OrbitalOrchestrator:
    """
    Orchestrates the process of retrieving TLE/OMM data and generating orbital tracks.
    """

    def __init__(self, username, password, log_callback=None):
        """
        Initialize with SpaceTrack credentials.
        
        :param username: SpaceTrack login.
        :param password: SpaceTrack password.
        """
        self.client = SpacetrackClientWrapper(username, password)
        self.logic_handler = OrbitalLogicHandler()
        
        self.log_callback = log_callback
        self._init_logger()
        self._log("OrbitalOrchestrator initialized with provided credentials.", "INFO")
        
    def _init_logger(self):
        """
        Initialize the file logger for the orchestrator.
        """
        self.logger = logging.getLogger("OrbitalOrchestrator")
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            log_file = os.path.join(os.path.dirname(__file__), "OrbitalOrchestrator.log")
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s",
                                          datefmt="%Y-%m-%d %H:%M:%S")
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
            
    def _log(self, message, level="INFO"):
        """
        Log a message to both the file and the UI log window via the callback, if available.

        :param message: The log message.
        :param level: Log level ("INFO", "DEBUG", "WARNING", "ERROR").
        """
        if level.upper() == "DEBUG":
            self.logger.debug(message)
        elif level.upper() == "WARNING":
            self.logger.warning(message)
        elif level.upper() == "ERROR":
            self.logger.error(message)
        else:
            self.logger.info(message)
        if self.log_callback:
            self.log_callback(message, level)

    def _verify_data(self, data, data_format):
        """
        Verify that data was successfully retrieved and log the result.

        :param data: The data retrieved from SpaceTrack.
        :param data_format: The format of the data (TLE or OMM).
        :return: Boolean indicating data validity.
        """
        if not data:
            self._log(f"No data received for format: {data_format}", "ERROR")
            return False

        self._log(f"Successfully received data for format: {data_format}", "INFO")
        return True

    def process_persistent_track(self, sat_id, track_day, step_minutes, output_path, data_format='TLE', file_format='shp'):
        """
        Generate persistent orbital track shapefiles.
        
        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :param output_shapefile: Output point shapefile path.
        :param data_format: 'TLE' or 'OMM'.
        :return: Tuple (point_shapefile, line_shapefile).
        :raises ValueError: If data format is invalid.
        """
        self._log(f"Starting persistent track processing for SatID: {sat_id}, Date: {track_day}, Format: {data_format}", "INFO")
        use_latest = track_day > date.today()
        
        if data_format == 'TLE':
            data = self.client.get_tle(sat_id, track_day, latest=use_latest)
        elif data_format == 'OMM':
            data = self.client.get_omm(sat_id, track_day, latest=use_latest)
            if isinstance(data, str):
                data = json.loads(data)
            json_filename = os.path.splitext(output_path)[0] + '.json'
            self.client.save_omm_json(data, json_filename)
        else:
            raise ValueError("Invalid data format. Choose 'TLE' or 'OMM'.")
        
        if not self._verify_data(data, data_format):
            return None
        
        return self.logic_handler.create_persistent_orbital_track(
        data, data_format, track_day, step_minutes, output_path, file_format)

    def process_in_memory_track(self, sat_id, track_day, step_minutes, data_format='TLE'):
        """
        Generate temporary in-memory QGIS layers.
        
        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :param data_format: 'TLE' or 'OMM'.
        :return: Tuple (point_layer, line_layer).
        :raises ValueError: If data format is invalid.
        """
        self._log(f"Starting in-memory track processing for SatID: {sat_id}, Date: {track_day}, Format: {data_format}", "INFO")
        
        use_latest = track_day > date.today()
        if data_format == 'TLE':
            data = self.client.get_tle(sat_id, track_day, latest=use_latest)
        elif data_format == 'OMM':
            data = self.client.get_omm(sat_id, track_day, latest=use_latest)
            if isinstance(data, str):
                data = json.loads(data)
        else:
            raise ValueError("Invalid data format. Choose 'TLE' or 'OMM'.")
        
        if not self._verify_data(data, data_format):
            return None
        
        return self.logic_handler.create_in_memory_layers(data, data_format, track_day, step_minutes)
