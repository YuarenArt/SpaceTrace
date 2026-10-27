"""Optional benchmarks, run explicitly with: pytest test/benchmark."""
from datetime import timedelta
import math
import pytest
from SpaceTrace.src.orbital_data_processor.pyorbital_processor import PyOrbitalDataProcessor
from SpaceTrace.src.orbital_data_processor.skyfield import SkyfieldOrbitalDataProcessor
from test.conftest import START, TLE_LINE1, TLE_LINE2

@pytest.fixture(scope="module", params=["pyorbital", "skyfield"])
def processor(request):
    log = lambda *args: None
    if request.param == "pyorbital":
        return PyOrbitalDataProcessor("ISS", TLE_LINE1, TLE_LINE2, 51.6386, log)
    return SkyfieldOrbitalDataProcessor("ISS", TLE_LINE1, TLE_LINE2, log)

@pytest.mark.benchmark
def test_coordinate(benchmark, processor):
    lon, lat, alt = benchmark(processor.get_coord, START)
    assert all(math.isfinite(float(x)) for x in (lon, lat, alt))

@pytest.mark.benchmark
def test_propagation(benchmark, processor):
    points = benchmark(processor.propagate, START, 1, 10)
    assert len(points) == 7

@pytest.mark.benchmark
def test_parameter_batch(benchmark, processor):
    times = [START + timedelta(minutes=10 * i) for i in range(7)]
    points = benchmark(processor.compute_orbital_parameters, times)
    assert len(points) == 7
