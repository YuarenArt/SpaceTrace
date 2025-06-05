"""
This module contains the OrbitalTrackFacade class that orchestrates the process
of retrieving TLE/OMM data and generating orbital track layers.
"""
import os
import json

from .handler import OrbitalLogicHandler

class OrbitalTrackFacade:
    """
    Orchestrates the process of retrieving TLE/OMM data and generating orbital tracks.
    """

    def __init__(self, retriever, log_callback=None):
        """
        Initialize with a data retriever and computation engine.

        :param retriever: Instance of DataRetriever.
        :param engine: Instance of ComputationEngine.
        :param log_callback: Function to handle logging.
        """
        self.retriever = retriever
        self.logic_handler = OrbitalLogicHandler(log_callback=log_callback)
        self.log_callback = log_callback

    def _log(self, message, level="INFO"):
        """
        Log a message to both the file and the UI log window via the callback, if available.

        :param message: The log message.
        :param level: Log level ("INFO", "DEBUG", "WARNING", "ERROR").
        """
        if self.log_callback:
            self.log_callback(message, level)

    def _retrieve_data(self, config):
        """
        Retrieve data using the provided retriever and configuration.

        :param config: OrbitalConfig instance with settings.
        :return: Retrieved TLE or OMM data.
        :raises Exception: If data retrieval fails.
        """
        data_format = config.data_format
        source = config.data_file_path if config.data_file_path else "SpaceTrack API"
        self._log(f"Retrieving data from {source} for SatID: {config.sat_id or 'local'}, "
                f"Start: {config.start_datetime}, Format: {data_format}", "INFO")
        
        try:
            data = self.retriever.retrieve_data(config)
            if not self._verify_data(data, data_format):
                raise Exception(f"No data received for format: {data_format}")
            
            # Save data if specified in config
            if config.save_data and config.save_data_path:
                if data_format == "TLE":
                    self._save_tle_data(data, config.save_data_path)
                elif data_format == "OMM":
                    self._save_omm_data(data, config.save_data_path)
            
            return data
        except Exception as e:
            self._log(f"Error retrieving or processing data: {str(e)}", "ERROR")
            raise
    
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
        
        data = self._retrieve_data(config)
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
        :raises Exception: If data folder creation or data retrieval fails.
        """
        self._log(f"Processing in-memory track for SatID: {config.sat_id}, Start: {config.start_datetime}, "
                f"Duration: {config.duration_hours} hours, Format: {config.data_format}", "INFO")
        plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_folder = os.path.join(plugin_dir, "data")
        
        try:
            if not os.path.exists(data_folder):
                os.makedirs(data_folder)
                self._log(f"Created data folder at: {data_folder}", "INFO")
            elif not os.access(data_folder, os.W_OK):
                raise Exception(f"Data folder {data_folder} is not writable")
        except Exception as e:
            self._log(f"Failed to create or access data folder: {str(e)}", "ERROR")
            raise
        
        default_output_path = os.path.join(data_folder, f"{config.sat_id or 'local'}_{config.start_datetime.strftime('%Y%m%d%H%M')}")
        config.save_data_path = config.save_data_path or default_output_path
        
        data = self._retrieve_data(config)
        return self.logic_handler.create_in_memory_layers(
            data, config.data_format, config.start_datetime, config.duration_hours, config.step_minutes, config.create_line_layer
        )
