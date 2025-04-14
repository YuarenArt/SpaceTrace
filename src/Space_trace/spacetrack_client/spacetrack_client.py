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

    def search_by_name(self, name, limit=100):
        """
        Search satellites by name (partial match).
        """
        results = self.client.satcat(
            satname=op.like(f'%{name}%'),
            orderby='NORAD_CAT_ID asc',
            limit=limit,
            format='json'
        )
        return json.loads(results) if isinstance(results, str) else results
        
    def get_active_satellites(self, limit=100):
        results = self.client.satcat(
            current='Y',
            orderby='NORAD_CAT_ID desc',
            limit=limit,
            format='json'
        )
        return json.loads(results) if isinstance(results, str) else results

        
    def search_by_country(self, country_code, limit=100):
        """
        Search satellites launched by a specific country.
        Example country codes: 'USA', 'RUS', 'CHN'.
        """
        results = self.client.satcat(
            country=country_code,
            orderby='NORAD_CAT_ID asc',
            limit=limit,
            format='json'
        )
        return json.loads(results) if isinstance(results, str) else results
    
    def search_by_norad_id(self, norad_input, limit=100):
        """
        Search satellites by NORAD ID (single, range, or list).

        Args:
            norad_input (str): Single NORAD ID (e.g., '25544'), range (e.g., '25544-25550'), or list (e.g., '25544,25545').
            limit (int): Maximum number of results.

        Returns:
            list: List of satellite data dictionaries.

        Raises:
            ValueError: If NORAD input format is invalid.
        """
        norad_input = norad_input.strip()
        if '-' in norad_input:
            # Handle range (e.g., '25544-25550')
            try:
                start, end = map(int, norad_input.split('-'))
                if start > end:
                    raise ValueError("Start of range must be less than or equal to end.")
                norad_ids = op.inclusive_range(start, end)
            except ValueError as e:
                raise ValueError(f"Invalid NORAD ID range format: {norad_input}. Use e.g., '25544-25550'.") from e
        elif ',' in norad_input:
            # Handle list (e.g., '25544,25545')
            try:
                norad_ids = [int(id.strip()) for id in norad_input.split(',')]
                if not norad_ids:
                    raise ValueError("NORAD ID list cannot be empty.")
                norad_ids = ','.join(map(str, norad_ids))
            except ValueError as e:
                raise ValueError(f"Invalid NORAD ID list format: {norad_input}. Use e.g., '25544,25545'.") from e
        else:
            # Handle single ID (e.g., '25544')
            try:
                norad_ids = int(norad_input)
            except ValueError as e:
                raise ValueError(f"Invalid NORAD ID: {norad_input}. Must be a number.") from e

        results = self.client.satcat(
            norad_cat_id=norad_ids,
            orderby='NORAD_CAT_ID asc',
            limit=limit,
            format='json'
        )
        return json.loads(results) if isinstance(results, str) else results
