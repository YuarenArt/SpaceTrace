from abc import ABC, abstractmethod
import os
import json

class DataRetriever(ABC):
    @abstractmethod
    def retrieve_data(self, config):
        pass

class LocalFileRetriever(DataRetriever):
    """
    Retrieves orbital data from local files and saves it if specified.
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
        Retrieve data from a local file and save it if specified.

        :param config: OrbitalConfig instance with settings.
        :return: Retrieved TLE or OMM data.
        :raises Exception: If loading or parsing the file fails.
        """
        file_path = config.data_file_path
        data_format = config.data_format
        save_data = config.save_data
        save_data_path = config.save_data_path

        try:
            if data_format == 'TLE':
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    if len(lines) < 2:
                        raise ValueError("The TLE file must contain at least two lines.")
                    tle_line1 = lines[0].strip()
                    tle_line2 = lines[1].strip()
                    orb_incl = float(tle_line2[8:16])
                    data = (tle_line1, tle_line2, orb_incl)
                    if save_data and save_data_path:
                        self._save_tle_data(data, save_data_path)
                    return data
            elif data_format == 'OMM':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if save_data and save_data_path:
                        self._save_omm_data(data, save_data_path)
                    return data
            else:
                raise ValueError("Unsupported data format.")
        except Exception as e:
            self._log(f"Error loading local data: {str(e)}", "ERROR")
            raise Exception(f"Error loading local data: {str(e)}")