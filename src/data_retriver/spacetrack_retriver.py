from .data_retriver import DataRetriever
from ..spacetrack_client.spacetrack_client import SpacetrackClientWrapper

class SpaceTrackRetriever(DataRetriever):
    """
    Retrieves orbital data from the SpaceTrack API.
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

    def retrieve_data(self, config):
        """
        Retrieve data from SpaceTrack API.

        :param config: OrbitalConfig instance with settings.
        :return: Retrieved TLE or OMM data, or None if retrieval fails.
        :raises ValueError: If the data format is unsupported.
        """
        data_format = config.data_format
        sat_id = config.sat_id
        start_datetime = config.start_datetime
        if data_format == 'TLE':
            data = self.client.get_tle(sat_id, start_datetime)
        elif data_format == 'OMM':
            data = self.client.get_omm(sat_id, start_datetime)
        else:
            raise ValueError("Unsupported data format. Use 'TLE' or 'OMM'.")

        if not data:
            self._log(f"No data received for format: {data_format}", "ERROR")
            return None
        return data

