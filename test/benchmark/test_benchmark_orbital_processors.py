import pytest
from datetime import datetime, timedelta
import os
import math
import statistics

from src.orbital_data_processor.pyorbital_processor import PyOrbitalDataProcessor
from src.orbital_data_processor.skyfield import SkyfieldOrbitalDataProcessor

def load_tle_data():
    base = os.path.dirname(__file__)
    tle_path = os.path.join(base, "TLE.txt")
    with open(tle_path, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        if lines[0].startswith('1 '):
            line1 = lines[0]
            line2 = lines[1]
        else:
            line1 = lines[1]
            line2 = lines[2]
        inclination = float(line2.split()[2])
        return line1, line2, inclination

TLE_LINE1, TLE_LINE2, INCLINATION = load_tle_data()

@pytest.fixture(scope="module")
def time_range():
    now = datetime.utcnow()
    seconds_per_week = 7 * 24 * 60 * 60
    step = 10
    return [now + timedelta(seconds=i * step) for i in range(seconds_per_week // step)]

@pytest.fixture(scope="module")
def pyorbital_proc():
    return PyOrbitalDataProcessor("test_pyorbital", TLE_LINE1, TLE_LINE2, INCLINATION)

@pytest.fixture(scope="module")
def skyfield_proc():
    return SkyfieldOrbitalDataProcessor("test_skyfield", TLE_LINE1, TLE_LINE2)

@pytest.mark.benchmark
def test_get_coord_pyorbital(benchmark, pyorbital_proc):
    time_utc = datetime.utcnow()
    benchmark(lambda: pyorbital_proc.get_coord(time_utc))

@pytest.mark.benchmark
def test_get_coord_skyfield(benchmark, skyfield_proc):
    time_utc = datetime.utcnow()
    benchmark(lambda: skyfield_proc.get_coord(time_utc))

@pytest.mark.benchmark
def test_compute_orbital_parameters_pyorbital(benchmark, pyorbital_proc, time_range):
    benchmark(lambda: pyorbital_proc.compute_orbital_parameters(time_range))

@pytest.mark.benchmark
def test_compute_orbital_parameters_skyfield(benchmark, skyfield_proc, time_range):
    benchmark(lambda: skyfield_proc.compute_orbital_parameters(time_range))

@pytest.mark.benchmark
def test_propagate_pyorbital(benchmark, pyorbital_proc):
    start = datetime.utcnow()
    benchmark(lambda: pyorbital_proc.propagate(start, duration_hours=1.0, step_minutes=1.0))

@pytest.mark.benchmark
def test_propagate_skyfield(benchmark, skyfield_proc):
    start = datetime.utcnow()
    benchmark(lambda: skyfield_proc.propagate(start, duration_hours=1.0, step_minutes=1.0))

def euclidean_distance(coord1, coord2):
    """Calculate Euclidean distance between two 3D coordinates."""
    return math.sqrt(
        (coord1[0] - coord2[0])**2 +
        (coord1[1] - coord2[1])**2 +
        (coord1[2] - coord2[2])**2
    )

def test_compare_coordinates_detailed_difference(pyorbital_proc, skyfield_proc, time_range):
    diffs = []
    diffs_x = []
    diffs_y = []
    diffs_z = []

    for t in time_range:
        coord_pyo = pyorbital_proc.get_coord(t)
        coord_sky = skyfield_proc.get_coord(t)

        dx = abs(coord_pyo[0] - coord_sky[0])
        dy = abs(coord_pyo[1] - coord_sky[1])
        dz = abs(coord_pyo[2] - coord_sky[2])
        dist = math.sqrt(dx**2 + dy**2 + dz**2)

        diffs.append(dist)
        diffs_x.append(dx)
        diffs_y.append(dy)
        diffs_z.append(dz)

        print(f"Time {t}: Δx={dx:.3f}, Δy={dy:.3f}, Δz={dz:.3f}, Euclidean Δ={dist:.3f}")

    print("\nSummary statistics:")
    print(f"Euclidean distance: mean={statistics.mean(diffs):.3f}, max={max(diffs):.3f}, min={min(diffs):.3f}")
    print(f"Δx: mean={statistics.mean(diffs_x):.3f}, max={max(diffs_x):.3f}, min={min(diffs_x):.3f}")
    print(f"Δy: mean={statistics.mean(diffs_y):.3f}, max={max(diffs_y):.3f}, min={min(diffs_y):.3f}")
    print(f"Δz: mean={statistics.mean(diffs_z):.3f}, max={max(diffs_z):.3f}, min={min(diffs_z):.3f}")

    max_allowed_diff = 1e3
    assert max(diffs) < max_allowed_diff, f"Max difference too large: {max(diffs)}"
