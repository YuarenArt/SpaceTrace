from abc import ABC, abstractmethod
import json
from ..orbital_data_processor.tle_validation import validate_tle_lines

class DataRetriever(ABC):
    @abstractmethod
    def retrieve_data(self, config):
        pass

class LocalFileRetriever(DataRetriever):
    """
    Retrieves orbital data from local files.
    """
    def __init__(self, log_callback=None):
        """
        Initialize with optional logging callback.

        :param log_callback: Function to handle logging.
        """
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
        Retrieve data from a local file.

        :param config: OrbitalConfig instance with settings.
        :return: Retrieved TLE or OMM data.
        :raises Exception: If loading or parsing the file fails.
        """
        file_path = config.data_file_path
        data_format = config.data_format
        try:
            if data_format == 'TLE':
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    if len(lines) < 2:
                        raise ValueError("The TLE file must contain at least two lines.")
                    nonempty = [line.strip() for line in lines if line.strip()]
                    if nonempty and not nonempty[0].startswith("1 "):
                        nonempty = nonempty[1:]
                    if len(nonempty) < 2:
                        raise ValueError("The TLE file must contain two element lines.")
                    tle_line1, tle_line2 = validate_tle_lines(nonempty[0], nonempty[1])
                    orb_incl = float(tle_line2[8:16])
                    data = (tle_line1, tle_line2, orb_incl)
                    return data
            elif data_format == 'OMM':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
                        raise ValueError("OMM data must be a non-empty list of records.")
                    validate_tle_lines(data[0].get("TLE_LINE1"), data[0].get("TLE_LINE2"))
                    return data
            else:
                raise ValueError("Unsupported data format.")
        except Exception as e:
            self._log(f"Error loading local data: {str(e)}", "ERROR")
            raise Exception(f"Error loading local data: {str(e)}")
