from dataclasses import dataclass
from datetime import datetime

@dataclass
class OrbitalConfig:
    """Configuration for orbital track generation."""
    sat_id: int = None              # Satellite NORAD ID (None if using local file)
    start_datetime: datetime = None # Start date and time for the track
    duration_hours: float = 24.0    # Duration of the track in hours
    step_minutes: float = 0.5       # Time step in minutes
    output_path: str = ""           # Path for saving output (empty for temp layer)
    file_format: str = None         # Output file format (e.g., shp, gpkg)
    add_layer: bool = True          # Whether to add layer to QGIS project
    login: str = None               # SpaceTrack login
    password: str = None            # SpaceTrack password
    data_format: str = "TLE"        # Data format (TLE or OMM)
    create_line_layer: bool = True  # Whether to create a line layer
    save_data: bool = False         # Whether to save received data
    data_file_path: str = ""        # Path to local data file
    save_data_path: str = ""        # Path to save received data