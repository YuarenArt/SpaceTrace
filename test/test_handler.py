import unittest
from datetime import date, datetime
from unittest.mock import patch
from src.Space_trace.orbital.handler import OrbitalLogicHandler
import numpy as np

class OrbitalLogicHandlerTest(unittest.TestCase):
    def setUp(self):
        self.handler = OrbitalLogicHandler()

    @patch('pyorbital.orbital.Orbital')
    def test_generate_points_valid_tle(self, mock_orbital):

        mock_orb = mock_orbital.return_value
        mock_orb.get_position.return_value = (np.array([1, 0, 0]), np.array([0, 1, 0]))
        mock_orb.get_lonlatalt.return_value = (121.11, -40.55, 430.43)

        tle_data = (
            "1 25544U 98067A   25087.72483446  .00032194  00000-0  56484-3 0  9999",
            "2 25544  51.6386 345.5386 0004029  59.5799 332.6073 15.50242233502686",
            51.6386
        )
        track_day = date(2025, 3, 28)
        step_minutes = 1

        points = self.handler.generate_points(tle_data, 'TLE', track_day, step_minutes)

        self.assertEqual(len(points), 1440)
        point = points[0]
        self.assertIsInstance(point[0], datetime) 
        self.assertAlmostEqual(point[1], 121.11, delta=0.01)
        self.assertAlmostEqual(point[2], -40.55, delta=0.01)    
        self.assertAlmostEqual(point[3], 430.43, delta=0.1)

    def test_generate_points_invalid_tle(self):
        invalid_tle = ("invalid", "invalid", 0)
        with self.assertRaises(ValueError):
            self.handler.generate_points(invalid_tle, 'TLE', date(2023, 10, 2), 1)
            
    def test_get_line_segments_crossing(self):
        points = [(-179.0, 0.0), (179.0, 1.0)] 
        segments = self.handler.get_line_segments(points)
        
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0], [(-179.0, 0.0), (-180.0, 0.5)])
        self.assertEqual(segments[1], [(180.0, 0.5), (179.0, 1.0)])
        
    