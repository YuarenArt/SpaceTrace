"""Protect PyOrbital callers from an endless propagation loop."""
from datetime import datetime
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest

from SpaceTrace.src.orbital_data_processor.pyorbital_processor import PyOrbitalDataProcessor


@pytest.mark.unit
def test_invalid_steps_are_rejected_without_hanging():
    # Keep the test itself bounded even if a future change reintroduces the loop.
    code = """
from datetime import datetime
from src.orbital_data_processor.pyorbital_processor import PyOrbitalDataProcessor
processor = PyOrbitalDataProcessor.__new__(PyOrbitalDataProcessor)
processor.log_callback = None
for step in (0, -1, 1e-15):
    try:
        processor.propagate(datetime(2025, 3, 28), 1, step)
    except ValueError as exc:
        assert 'step' in str(exc)
    else:
        raise AssertionError(f'Invalid step {step} was accepted')
"""
    subprocess.run(
        [sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[1],
        timeout=5, check=True,
    )


@pytest.mark.unit
def test_positive_step_still_generates_expected_times():
    processor = PyOrbitalDataProcessor.__new__(PyOrbitalDataProcessor)
    processor.log_callback = None
    processor.compute_orbital_parameters = Mock(side_effect=lambda times: times)
    times = processor.propagate(datetime(2025, 3, 28), 0.5, 10)
    assert len(times) == 4
    assert (times[-1] - times[0]).total_seconds() == 1800
