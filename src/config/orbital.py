class OrbitalConfig:
    """
    Configuration for orbital track generation.
    
    Encapsulates all settings required to generate orbital tracks.
    """
    def __init__(self, sat_id, track_day, step_minutes, output_path, file_format,
                 add_layer, login, password, data_format, create_line_layer, save_data, data_file_path,
                 save_data_path):
        
        self.sat_id             = sat_id            # Satellite NORAD ID (None if local file is used)
        self.track_day          = track_day         # Date for track computation
        self.step_minutes       = step_minutes      # Time step in minutes
        self.output_path        = output_path       # Output file path (if persistent layers are needed)
        self.file_format        = file_format       # File format (derived from output_path)
        self.add_layer          = add_layer         # Whether to add layers to QGIS project
        self.login              = login             # SpaceTrack login (None if local file is used)
        self.password           = password          # SpaceTrack password (None if local file is used)
        self.data_format        = data_format       # 'TLE' or 'OMM'
        self.create_line_layer  = create_line_layer # Flag to create line layer
        self.save_data          = save_data         # Flag to save received data
        self.data_file_path     = data_file_path    # Local data file path (if provided)
        self.save_data_path     = save_data_path
