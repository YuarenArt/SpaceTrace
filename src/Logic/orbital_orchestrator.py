"""
This module contains the OrbitalOrchestrator class that orchestrates the overall
process of retrieving TLE data and generating orbital track layers.
"""

from datetime import date
# Импортируем классы из локальных модулей:
from .spacetrack_client import SpacetrackClientWrapper
from .orbital_handler import OrbitalLogicHandler

class OrbitalOrchestrator:
    """
    Orchestrates the overall process of retrieving TLE data and generating orbital track layers.

    It combines a SpaceTrack client (SpacetrackClientWrapper) and a logic handler
    (OrbitalLogicHandler) to produce either persistent shapefiles on disk or
    temporary in-memory QGIS layers.
    """

    def __init__(self, username, password):
        """
        Initialize the orchestrator with SpaceTrack credentials.

        :param username: SpaceTrack account login.
        :param password: SpaceTrack account password.
        """
        self.client = SpacetrackClientWrapper(username, password)
        self.logic_handler = OrbitalLogicHandler()

    def process_persistent_track(self, sat_id, track_day, step_minutes, output_shapefile):
        """
        Generate persistent orbital track shapefiles on disk.

        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :param output_shapefile: Output filename for the point shapefile.
        :return: Tuple (point_shapefile, line_shapefile) with file paths.
        """
        # Determine whether to use the latest TLE based on the track day.
        use_latest = track_day > date.today()
        tle_data = self.client.get_tle(sat_id, track_day, latest=use_latest)

        return self.logic_handler.create_persistent_orbital_track(
            sat_id, track_day, step_minutes, output_shapefile, tle_data
        )

    def process_in_memory_track(self, sat_id, track_day, step_minutes):
        """
        Generate temporary in-memory QGIS layers representing the orbital track.

        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for track computation.
        :param step_minutes: Time step in minutes.
        :return: Tuple (point_layer, line_layer) of QGIS in-memory layers.
        """
        use_latest = track_day > date.today()
        tle_data = self.client.get_tle(sat_id, track_day, latest=use_latest)

        return self.logic_handler.create_in_memory_layers(
            sat_id, track_day, step_minutes, tle_data
        )
