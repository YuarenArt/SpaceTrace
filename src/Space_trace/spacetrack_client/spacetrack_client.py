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
        self.client = SpaceTrackClient(identity=username, password=password)

    def get_tle(self, sat_id, start_datetime):
        """
        Retrieve TLE data for the specified satellite based on start_datetime.

        :param sat_id: Satellite NORAD ID.
        :param start_datetime: Start date and time for which TLE data is needed (latest data before this time).
        :return: Tuple (tle_1, tle_2, orb_incl) containing the TLE lines and orbital inclination.
        :raises Exception: If TLE data cannot be retrieved.
        """
        # Define a range from 30 days before start_datetime to start_datetime to ensure data availability
        start_range = start_datetime - timedelta(days=30)
        daterange = op.inclusive_range(start_range.strftime('%Y-%m-%d'), start_datetime.strftime('%Y-%m-%d %H:%M:%S'))
        
        # Fetch the most recent TLE data before the specified start_datetime
        data = self.client.gp_history(
            norad_cat_id=sat_id,
            epoch=daterange,
            orderby='epoch desc',
            limit=1,
            format='tle'
        )
        if not data:
            raise Exception(f'No TLE data found for satellite {sat_id} before {start_datetime}')
        tle_1 = data[0:69]
        tle_2 = data[70:139]
        orb_incl = data[78:86] 
        return tle_1, tle_2, orb_incl

    def get_omm(self, sat_id, start_datetime):
        """
        Retrieve OMM data for the specified satellite based on start_datetime.

        :param sat_id: Satellite NORAD ID.
        :param start_datetime: Start date and time for which OMM data is needed (latest data before this time).
        :return: OMM data as a parsed JSON object.
        :raises Exception: If OMM data cannot be retrieved.
        """
        # Define a range from 30 days before start_datetime to start_datetime to ensure data availability
        start_range = start_datetime - timedelta(days=30)
        daterange = op.inclusive_range(start_range.strftime('%Y-%m-%d'), start_datetime.strftime('%Y-%m-%d %H:%M:%S'))
        
        # Fetch the most recent OMM data before the specified start_datetime
        data = self.client.gp_history(
            norad_cat_id=sat_id,
            epoch=daterange,
            orderby='epoch desc',
            limit=1,
            format='json'
        )
        if not data:
            raise Exception(f'No OMM data found for satellite {sat_id} before {start_datetime}')
        return json.loads(data)

    def search_by_name(self, name):
        """
        Search for satellites matching part of the name using a wildcard query.
        
        :param name: Partial satellite name to search for.
        :return: A list of found satellites in JSON format.
        :raises Exception: If no satellites are found.
        """
        data = self.client.satcat(OBJECT_NAME=f'*{name}*', format='json')
        if not data:
            raise Exception(f"No satellites found matching name: {name}")
        return data
        
    def get_active_satellites(self, limit=100):
        """
        Return a list of active satellites.
        An active satellite is typically defined as one that does not have a DECAY_DATE.
        
        :param limit: Maximum number of satellites to return.
        :return: A list of active satellites in JSON format.
        :raises Exception: If no active satellites are found.
        """
        # Filtering satellites where DECAY_DATE is empty.
        data = self.client.satcat(DECAY_DATE='', limit=limit, format='json')
        if not data:
            raise Exception("No active satellites found")
        return data
        
    def search_by_country(self, country_code):
        """
        Search for satellites by country code.
        
        :param country_code: Country code (e.g., 'US') to filter satellites.
        :return: A list of satellites from the specified country in JSON format.
        :raises Exception: If no satellites are found for the given country.
        """
        data = self.client.satcat(COUNTRY_CODE=country_code.upper(), format='json')
        if not data:
            raise Exception(f"No satellites found for country: {country_code}")
        return data