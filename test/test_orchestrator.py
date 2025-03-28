import unittest
from unittest.mock import Mock, patch
from src.Space_trace.orbital.orchestrator import OrbitalOrchestrator
from datetime import date

class OrbitalOrchestratorTest(unittest.TestCase):
    def setUp(self):
        self.orchestrator = OrbitalOrchestrator("test@example.com", "password")
        self.config = Mock(
            sat_id=25544,
            track_day=date(2025, 3, 28),
            data_format='TLE',
            step_minutes=1,
            output_path='test_output.shp',
            file_format='shp',
            create_line_layer=True,
            save_data=False,
            data_file_path=None,
            save_data_path=None
        )

    @patch('src.orbital.spacetrack_client.SpacetrackClientWrapper')
    @patch('src.orbital.handler.OrbitalLogicHandler')
    def test_process_persistent_track(self, mock_logic_handler, mock_client):
        mock_client.return_value.get_tle.return_value = (
            "TLE1", "TLE2", 51.6448
        )
        mock_logic_handler.return_value.create_persistent_orbital_track.return_value = (
            'test_output.shp', 'test_output_line.shp'
        )

        result = self.orchestrator.process_persistent_track(self.config)
        mock_client.return_value.get_tle.assert_called_once_with(25544, date(2025, 3, 28), latest=False)
        self.assertEqual(result, ('test_output.shp', 'test_output_line.shp'))