"""
This module contains the OrbitalOrchestrator class that orchestrates the process
of retrieving TLE/OMM data and generating orbital track layers.
"""

from datetime import date
import os
import json

from .spacetrack_client import SpacetrackClientWrapper
from .orbital_handler import OrbitalLogicHandler

class OrbitalOrchestrator:
    """
    Orchestrates the process of retrieving TLE/OMM data and generating orbital tracks.
    """

    def __init__(self, username, password):
        """
        Initialize with SpaceTrack credentials.
        
        :param username: SpaceTrack login.
        :param password: SpaceTrack password.
        """
        self.client = SpacetrackClientWrapper(username, password)
        self.logic_handler = OrbitalLogicHandler()

    def process_persistent_track(self, sat_id, track_day, step_minutes, output_shapefile, data_format='TLE', split_type='none', split_count=0):
        """
        Generate persistent orbital track shapefiles.
        
        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :param output_shapefile: Output point shapefile path.
        :param data_format: 'TLE' or 'OMM'.
        :param split_type: 'none', 'antimeridian', or 'custom' - type of track splitting.
        :param split_count: Number of segments for 'custom' splitting.
        :return: Tuple (point_shapefile, line_shapefile).
        :raises ValueError: If data format is invalid.
        """
        use_latest = track_day > date.today()
        if data_format == 'TLE':
            data = self.client.get_tle(sat_id, track_day, latest=use_latest)
        elif data_format == 'OMM':
            data = self.client.get_omm(sat_id, track_day, latest=use_latest)
            if isinstance(data, str):
                data = json.loads(data)
            json_filename = os.path.splitext(output_shapefile)[0] + '.json'
            self.client.save_omm_json(data, json_filename)
        else:
            raise ValueError("Invalid data format. Choose 'TLE' or 'OMM'.")
        return self.logic_handler.create_persistent_orbital_track(
            data, data_format, track_day, step_minutes, output_shapefile, split_type, split_count
        )

    def process_in_memory_track(self, sat_id, track_day, step_minutes, data_format='TLE', split_type='antimeridian', split_count=0):
        """
        Generate temporary in-memory QGIS layers.
        
        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :param data_format: 'TLE' or 'OMM'.
        :param split_type: 'none', 'antimeridian', or 'custom' - type of track splitting.
        :param split_count: Number of segments for 'custom' splitting.
        :return: Tuple (point_layer, line_layer).
        :raises ValueError: If data format is invalid.
        """
        use_latest = track_day > date.today()
        if data_format == 'TLE':
            data = self.client.get_tle(sat_id, track_day, latest=use_latest)
        elif data_format == 'OMM':
            data = self.client.get_omm(sat_id, track_day, latest=use_latest)
            if isinstance(data, str):
                data = json.loads(data)
        else:
            raise ValueError("Invalid data format. Choose 'TLE' or 'OMM'.")
        return self.logic_handler.create_in_memory_layers(
            data, data_format, track_day, step_minutes, split_type, split_count
        )
