"""
This module contains the SpacetrackClientWrapper class for SpaceTrack API communication.
It provides methods to retrieve TLE and OMM data.
"""

from datetime import date, timedelta
import spacetrack.operators as op
from spacetrack import SpaceTrackClient
import json

class SpacetrackClientWrapper:
    """
    Wrapper for SpaceTrack API.

    This class encapsulates the logic to retrieve satellite data (TLE or OMM) using the SpaceTrack API.
    """

    def __init__(self, username, password):
        """
        Initialize the SpaceTrack client with user credentials.

        :param username: SpaceTrack account login (email).
        :param password: SpaceTrack account password.
        """
        self.username = username
        self.password = password
        self.client = SpaceTrackClient(identity=username, password=password)

    def get_tle(self, sat_id, track_day=None, latest=False):
        """
        Retrieve TLE data for the specified satellite.

        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for which TLE data is needed. If None or in the future,
                          the latest TLE data is used.
        :param latest: Boolean flag to force retrieval of the latest TLE.
        :return: Tuple (tle_1, tle_2, orb_incl) containing the TLE lines and orbital inclination.
        :raises Exception: If TLE data cannot be retrieved.
        """
        if latest or (track_day is None or track_day > date.today()):
            data = self.client.gp(norad_cat_id=sat_id, orderby='epoch desc', limit=1, format='tle')
        else:
            daterange = op.inclusive_range(track_day, track_day + timedelta(days=1))
            data = self.client.gp_history(norad_cat_id=sat_id, orderby='epoch desc', limit=1,
                                          format='tle', epoch=daterange)

        if not data:
            raise Exception(f'Failed to retrieve TLE for satellite with ID {sat_id}')

        tle_1 = data[0:69]
        tle_2 = data[70:139]
        orb_incl = data[78:86]
        return tle_1, tle_2, orb_incl

    def get_omm(self, sat_id, track_day=None, latest=False):
        """
        Retrieve OMM data for the specified satellite in JSON format.

        :param sat_id: Satellite NORAD ID.
        :param track_day: Date for which OMM data is needed. If None or in the future,
                          the latest OMM data is used.
        :param latest: Boolean flag to force retrieval of the latest OMM.
        :return: OMM data as a JSON object.
        :raises Exception: If OMM data cannot be retrieved.
        """
        if latest or (track_day is None or track_day > date.today()):
            data = self.client.gp(norad_cat_id=sat_id, orderby='epoch desc',
                                  limit=1, format='json')
        else:
            daterange = op.inclusive_range(track_day, track_day + timedelta(days=1))
            data = self.client.gp_history(norad_cat_id=sat_id, orderby='epoch desc',
                                          limit=1, format='json', epoch=daterange)

        if not data:
            raise Exception(f'Failed to retrieve OMM data for satellite {sat_id}')

        return data
