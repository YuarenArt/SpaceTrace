"""TLE validation is independent of QGIS and network access."""

import pytest

from SpaceTrace.src.orbital_data_processor.tle_validation import validate_tle_lines
from test.conftest import TLE_LINE1, TLE_LINE2


@pytest.mark.unit
def test_fixture_tle_has_valid_structure_and_checksum():
    assert validate_tle_lines(TLE_LINE1, TLE_LINE2) == (TLE_LINE1, TLE_LINE2)


@pytest.mark.unit
@pytest.mark.parametrize("first,second", [
    ("", TLE_LINE2),
    (TLE_LINE1[:-1], TLE_LINE2),
    (TLE_LINE1[:-1] + ("0" if TLE_LINE1[-1] != "0" else "1"), TLE_LINE2),
    (TLE_LINE1, TLE_LINE2[:2] + "12345" + TLE_LINE2[7:]),
    (TLE_LINE2, TLE_LINE1),
])
def test_bad_tle_is_rejected_before_propagation(first, second):
    with pytest.raises(ValueError, match="TLE"):
        validate_tle_lines(first, second)
