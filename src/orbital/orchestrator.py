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
from .handler import OrbitalLogicHandler


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
        self._log("OrbitalOrchestrator initialized", "DEBUG")

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
        getattr(self.logger, level.lower(), self.logger.info)(message)
        if self.log_callback:
            self.log_callback(message, level)

    def _retrieve_data(self, sat_id, track_day, data_format, save_data, output_path):
        """
        Retrieve TLE or OMM data from SpaceTrack and optionally save it.
        
        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for track computation.
        :param data_format: 'TLE' or 'OMM'.
        :param save_data: Whether to save the retrieved data.
        :param output_path: Path to save the data.
        :return: Retrieved data or None if invalid.
        """
        use_latest = track_day > date.today()
        
        if data_format == 'TLE':
            data = self.client.get_tle(sat_id, track_day, latest=use_latest)
            if save_data and data:
                self._save_tle_data(data, output_path)
        elif data_format == 'OMM':
            data = self.client.get_omm(sat_id, track_day, latest=use_latest)
            if isinstance(data, str):
                data = json.loads(data)
            if save_data and data:
                self._save_omm_data(data, output_path)
        else:
            raise ValueError("Invalid data format. Choose 'TLE' or 'OMM'.")
        
        return data if self._verify_data(data, data_format) else None
    
    def _verify_data(self, data, data_format):
        """
        Verify that data was retrieved successfully and log the result.

        :param data: Retrieved TLE or OMM data.
        :param data_format: Data format ("TLE" or "OMM").
        :return: True if data is valid, False otherwise.
        """
        if not data:
            self._log(f"No data received for format: {data_format}", "ERROR")
            return False
        self._log(f"Successfully received data for format: {data_format}", "INFO")
        return True

    def _save_tle_data(self, tle_data, output_path):
        """
        Save TLE data to a file.
        """
        output_path = os.path.splitext(output_path)[0]
        tle_filename = f"{output_path}_tle.txt"
        with open(tle_filename, 'w') as f:
            f.write(f"{tle_data[0]}\n{tle_data[1]}\n")
        self._log(f"TLE data saved to {tle_filename}", "INFO")

    def _save_omm_data(self, omm_data, output_path):
        """
        Save OMM data to a JSON file.
        """
        output_path = os.path.splitext(output_path)[0]
        json_filename = f"{output_path}_omm.json"
        with open(json_filename, "w") as f:
            json.dump(omm_data, f, indent=4)
        self._log(f"OMM data saved to {json_filename}", "INFO")

    def process_persistent_track(self, sat_id, track_day, step_minutes, output_path, data_format, file_format, create_line_layer, save_data):
        """
        Generate persistent orbital track shapefiles.
        """
        self._log(f"Processing persistent track for SatID: {sat_id}, Date: {track_day}, Format: {data_format}", "INFO")
        data = self._retrieve_data(sat_id, track_day, data_format, save_data, output_path)
        if not data:
            return None
        return self.logic_handler.create_persistent_orbital_track(
            data, data_format, track_day, step_minutes, output_path, file_format, create_line_layer)

    def process_in_memory_track(self, sat_id, track_day, step_minutes, data_format, create_line_layer, save_data):
        """
        Generate temporary in-memory QGIS layers.
        """
        self._log(f"Processing in-memory track for SatID: {sat_id}, Date: {track_day}, Format: {data_format}", "INFO")
        output_path = f"{sat_id}_{track_day.strftime('%Y%m%d')}"
        data = self._retrieve_data(sat_id, track_day, data_format, save_data, output_path)
        if not data:
            return None
        return self.logic_handler.create_in_memory_layers(data, data_format, track_day, step_minutes, create_line_layer)
