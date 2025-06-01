import os
import json
from .data_retriver import DataRetriever
from ..spacetrack_client.spacetrack_client import SpacetrackClientWrapper

class SpaceTrackRetriever(DataRetriever):
    """
    Retrieves orbital data from the SpaceTrack API and saves it if specified.
    """
    def __init__(self, username, password, log_callback=None):
        """
        Initialize with SpaceTrack credentials and optional logging callback.

        :param username: SpaceTrack login username.
        :param password: SpaceTrack password.
        :param log_callback: Function to handle logging.
        """
        self.client = SpacetrackClientWrapper(username, password)
        self.log_callback = log_callback

    def _log(self, message, level="INFO"):
        """
        Log a message using the provided callback, if available.

        :param message: The message to log.
        :param level: Log level ("INFO", "DEBUG", "WARNING", "ERROR").
        """
        if self.log_callback:
            self.log_callback(message, level)

    def _save_tle_data(self, tle_data, output_path):
        """
        Save TLE data to a file.

        :param tle_data: Tuple containing TLE lines (tle_line1, tle_line2, orb_incl).
        :param output_path: Path to save the TLE file.
        """
        output_path = os.path.splitext(output_path)[0]
        tle_filename = f"{output_path}_tle.txt"
        with open(tle_filename, 'w') as f:
            f.write(f"{tle_data[0]}\n{tle_data[1]}\n")
        self._log(f"TLE data saved to {tle_filename}", "INFO")

    def _save_omm_data(self, omm_data, output_path):
        """
        Save OMM data to a JSON file.

        :param omm_data: OMM data to save.
        :param output_path: Path to save the OMM JSON file.
        """
        output_path = os.path.splitext(output_path)[0]
        json_filename = f"{output_path}_omm.json"
        with open(json_filename, "w") as f:
            json.dump(omm_data, f, indent=4)
        self._log(f"OMM data saved to {json_filename}", "INFO")

    def retrieve_data(self, config):
        """
        Retrieve data from SpaceTrack API and save it if specified.

        :param config: OrbitalConfig instance with settings.
        :return: Retrieved TLE or OMM data, or None if retrieval fails.
        :raises ValueError: If the data format is unsupported.
        """
        data_format = config.data_format
        sat_id = config.sat_id
        start_datetime = config.start_datetime
        save_data = config.save_data
        save_data_path = config.save_data_path

        if data_format == 'TLE':
            data = self.client.get_tle(sat_id, start_datetime)
            if save_data and data and save_data_path:
                self._save_tle_data(data, save_data_path)
        elif data_format == 'OMM':
            data = self.client.get_omm(sat_id, start_datetime)
            if save_data and data and save_data_path:
                self._save_omm_data(data, save_data_path)
        else:
            raise ValueError("Unsupported data format. Use 'TLE' or 'OMM'.")

        if not data:
            self._log(f"No data received for format: {data_format}", "ERROR")
            return None
        return data
        