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
            
    def _load_local_data(self, file_path, data_format):
        try:
            if data_format == 'TLE':
                # Read TLE data from file
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    if len(lines) < 2:
                        raise ValueError("TLE file must contain at least two lines.")
                    tle_line1 = lines[0].strip()
                    tle_line2 = lines[1].strip()
                    orb_incl = float(tle_line2[8:16])
                    return (tle_line1, tle_line2, orb_incl)
            elif data_format == 'OMM':
                # Read OMM data from JSON file
                with open(file_path, 'r') as f:
                    omm_data = json.load(f)
                return omm_data
            else:
                raise ValueError("Invalid data format.")
        except Exception as e:
            # Log error if loading fails
            self._log(f"Error loading local data: {str(e)}", "ERROR")
            return None

    def _retrieve_data(self, sat_id, start_datetime, data_format, save_data, output_path, local_file_path=None):
        if local_file_path:
            self._log(f"Loading data from local file: {local_file_path}", "INFO")
            data = self._load_local_data(local_file_path, data_format)
            if data and save_data:
                if data_format == 'TLE':
                    self._save_tle_data(data, output_path)
                elif data_format == 'OMM':
                    self._save_omm_data(data, output_path)
        else:
            self._log(f"Fetching data from SpaceTrack API for SatID: {sat_id}, Start: {start_datetime}", "INFO")
            if data_format == 'TLE':
                data = self.client.get_tle(sat_id, start_datetime)
                if save_data and data:
                    self._save_tle_data(data, output_path)
            elif data_format == 'OMM':
                data = self.client.get_omm(sat_id, start_datetime)
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

    def process_persistent_track(self, config):
        """
        Generate persistent orbital track shapefiles using configuration settings.

        :param config: An OrbitalConfig instance containing all settings.
        :return: Tuple (points_file, line_file).
        """
        self._log(f"Processing persistent track for SatID: {config.sat_id}, Start: {config.start_datetime}, "
                f"Duration: {config.duration_hours} hours, Format: {config.data_format}", "INFO")
        data = self._retrieve_data(config.sat_id, config.start_datetime, config.data_format, 
                                config.save_data, config.save_data_path, config.data_file_path)
        if not data:
            return None
        return self.logic_handler.create_persistent_orbital_track(
            data, config.data_format, config.start_datetime, config.duration_hours, config.step_minutes,
            config.output_path, config.file_format, config.create_line_layer
        )

    def process_in_memory_track(self, config):
        """
        Generate temporary in-memory QGIS layers.

        :param config: An OrbitalConfig instance containing all settings.
        :return: Tuple (point_layer, line_layer).
        """
        self._log(f"Processing in-memory track for SatID: {config.sat_id}, Start: {config.start_datetime}, "
                f"Duration: {config.duration_hours} hours, Format: {config.data_format}", "INFO")
        plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_folder = os.path.join(plugin_dir, "data")
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
            self._log(f"Created data folder at: {data_folder}", "INFO")
        
        default_output_path = os.path.join(data_folder, f"{config.sat_id or 'local'}_{config.start_datetime.strftime('%Y%m%d%H%M')}")
        data = self._retrieve_data(config.sat_id, config.start_datetime, config.data_format, 
                                config.save_data, config.save_data_path or default_output_path, config.data_file_path)
        if not data:
            return None
        return self.logic_handler.create_in_memory_layers(
            data, config.data_format, config.start_datetime, config.duration_hours, config.step_minutes, config.create_line_layer
        )
