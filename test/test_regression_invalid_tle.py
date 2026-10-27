"""Invalid TLE containers should fail with a useful validation error."""
import pytest

from SpaceTrace.src.Space_trace.orbital.handler import OrbitalLogicHandler


@pytest.mark.unit
@pytest.mark.parametrize("data", [None, 42, {}, object(), [], ["one"]])
def test_invalid_tle_container_raises_value_error(data):
    with pytest.raises(ValueError, match="Incorrect TLE data"):
        OrbitalLogicHandler()._get_processor(data, "TLE")
