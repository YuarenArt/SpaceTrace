"""API request construction without network traffic or credentials."""
import json
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from SpaceTrace.src.spacetrack_client.spacetrack_client import SpacetrackClientWrapper
from test.conftest import TLE_LINE1, TLE_LINE2
from SpaceTrace.src.spacetrack_dialog.custom_query_dialog import field_types


@pytest.fixture
def client():
    wrapper = SpacetrackClientWrapper.__new__(SpacetrackClientWrapper)
    wrapper.client = Mock()
    return wrapper


@pytest.mark.unit
def test_current_tle_uses_gp_and_parses_lines(client):
    client.client.gp.return_value = f"ISS\n{TLE_LINE1}\n{TLE_LINE2}\n"
    line1, line2, inclination = client.get_tle(25544, datetime.now(timezone.utc))
    client.client.gp.assert_called_once_with(norad_cat_id=25544, format="tle")
    client.client.gp_history.assert_not_called()
    assert (line1, line2) == (TLE_LINE1, TLE_LINE2)
    assert inclination == pytest.approx(51.6386)


@pytest.mark.unit
def test_historical_omm_uses_gp_history(client):
    data = [{"TLE_LINE1": TLE_LINE1, "TLE_LINE2": TLE_LINE2}]
    client.client.gp_history.return_value = json.dumps(data)
    assert client.get_omm(25544, datetime(2025, 3, 28, 18)) == data
    assert client.client.gp_history.call_args.kwargs["format"] == "json"
    client.client.gp.assert_not_called()


@pytest.mark.unit
def test_invalid_tle_response_is_rejected(client):
    client.client.gp.return_value = "not a TLE"
    with pytest.raises(ValueError, match="invalid TLE"):
        client.get_tle(25544, datetime.now(timezone.utc))


@pytest.mark.unit
@pytest.mark.parametrize("method,args,expected", [
    ("search_by_name", ("ISS", 1), "satname"),
    ("get_active_satellites", (1,), "current"),
    ("search_by_country", ("US", 1), "country"),
    ("search_by_norad_id", ("25544", 1), "norad_cat_id"),
])
def test_search_predicate_dispatch(client, method, args, expected):
    client.client.satcat.return_value = '[{"NORAD_CAT_ID": 25544}]'
    result = getattr(client, method)(*args)
    assert result[0]["NORAD_CAT_ID"] == 25544
    assert expected in client.client.satcat.call_args.kwargs


@pytest.mark.unit
def test_custom_query_validates_field_and_value(client):
    with pytest.raises(ValueError, match="Unknown field"):
        client.search_by_custom_query([("UNKNOWN", "=", "x")])
    with pytest.raises(ValueError, match="integer"):
        client.search_by_custom_query([("NORAD_CAT_ID", "=", "bad")])
    client.client.satcat.return_value = "[]"
    assert client.search_by_custom_query([("NORAD_CAT_ID", "=", "25544")], 1) == []
    assert client.client.satcat.call_args.kwargs["norad_cat_id"] == 25544


@pytest.mark.unit
@pytest.mark.parametrize("text,expected", [
    ("25544", "25544"),
    ("25544,40000", "25544,40000"),
    ("25544-25546", "25544"),
])
def test_norad_search_variants(client, text, expected):
    client.client.satcat.return_value = "[]"
    assert client.search_by_norad_id(text, 25) == []
    kwargs = client.client.satcat.call_args.kwargs
    assert expected in str(kwargs["norad_cat_id"])
    assert kwargs["limit"] == 25


@pytest.mark.unit
@pytest.mark.parametrize("text", ["3-2", "1-", ",2", "1,,2", "x", "1-2-3", "0", "1-1002"])
def test_invalid_norad_search_never_calls_api(client, text):
    with pytest.raises(ValueError):
        client.search_by_norad_id(text)
    client.client.satcat.assert_not_called()


@pytest.mark.unit
def test_custom_query_requires_condition(client):
    with pytest.raises(ValueError, match="at least one condition"):
        client.search_by_custom_query([])
    client.client.satcat.assert_not_called()


@pytest.mark.unit
@pytest.mark.parametrize("field,kind", list(field_types.items()))
def test_every_custom_query_field_maps_to_satcat(client, field, kind):
    examples = {
        "int": "25544", "decimal": "90.5", "date": "2025-03-28",
        "string": "ISS", "enum": "Y",
    }
    client.client.satcat.return_value = "[]"
    assert client.search_by_custom_query([(field, "=", examples[kind])], 5) == []
    assert field.lower() in client.client.satcat.call_args.kwargs
    assert client.client.satcat.call_args.kwargs["limit"] == 5


@pytest.mark.unit
@pytest.mark.parametrize("field,operator,value", [
    ("NORAD_CAT_ID", "!=", "25544"),
    ("NORAD_CAT_ID", "<", "25544"),
    ("NORAD_CAT_ID", ">", "25544"),
    ("INCLINATION", "<", "90.5"),
    ("INCLINATION", ">", "90.5"),
    ("LAUNCH", "<", "2025-03-28"),
    ("LAUNCH", ">", "2025-03-28"),
    ("DECAY", "IS NULL", None),
    ("DECAY", "IS NOT NULL", None),
    ("SATNAME", "LIKE", "%ISS%"),
    ("CURRENT", "!=", "N"),
])
def test_custom_query_operator_matrix(client, field, operator, value):
    client.client.satcat.return_value = "[]"
    assert client.search_by_custom_query([(field, operator, value)]) == []
    assert field.lower() in client.client.satcat.call_args.kwargs


@pytest.mark.unit
@pytest.mark.parametrize("field,operator,value", [
    ("NORAD_CAT_ID", "=", "bad"),
    ("INCLINATION", "=", "bad"),
    ("INCLINATION", "=", "nan"),
    ("INCLINATION", "=", "inf"),
    ("LAUNCH", "=", "2025-02-30"),
    ("CURRENT", "=", "maybe"),
    ("SATNAME", "<", "ISS"),
    ("NORAD_CAT_ID", "LIKE", "255%"),
])
def test_custom_query_invalid_predicates_do_not_call_api(client, field, operator, value):
    with pytest.raises(ValueError):
        client.search_by_custom_query([(field, operator, value)])
    client.client.satcat.assert_not_called()


@pytest.mark.unit
def test_custom_query_multiple_fields_and_repeated_field(client):
    client.client.satcat.return_value = "[]"
    client.search_by_custom_query([
        ("CURRENT", "=", "Y"),
        ("NORAD_CAT_ID", ">", "100"),
        ("NORAD_CAT_ID", "<", "200"),
    ], 10)
    kwargs = client.client.satcat.call_args.kwargs
    assert kwargs["current"] == "Y"
    assert "100" in str(kwargs["norad_cat_id"])
    assert "200" in str(kwargs["norad_cat_id"])
    assert "," in str(kwargs["norad_cat_id"])
    assert kwargs["limit"] == 10


@pytest.mark.unit
@pytest.mark.parametrize("name", ["ISS", "STARLINK-1234", "ÉTOILE_1"])
def test_name_search_passes_partial_match_predicate(client, name):
    client.client.satcat.return_value = "[]"
    client.search_by_name(name, 10)
    kwargs = client.client.satcat.call_args.kwargs
    assert name in str(kwargs["satname"])
    assert kwargs["limit"] == 10


@pytest.mark.unit
@pytest.mark.parametrize("hours_from_now,use_gp", [
    (-25, False),
    (-24, True),
    (0, True),
    (1, True),
    (2, False),
])
def test_current_and_historical_api_boundary(client, monkeypatch, hours_from_now, use_gp):
    from datetime import timedelta
    from SpaceTrace.src.spacetrack_client import spacetrack_client as module

    fixed = datetime(2026, 1, 1, tzinfo=timezone.utc)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(module, "datetime", FixedDateTime)
    client.client.gp.return_value = "[]"
    client.client.gp_history.return_value = "[]"
    client.get_omm(25544, fixed + timedelta(hours=hours_from_now))
    if use_gp:
        client.client.gp.assert_called_once()
        client.client.gp_history.assert_not_called()
    else:
        client.client.gp_history.assert_called_once()
        client.client.gp.assert_not_called()


@pytest.mark.unit
def test_active_search_uses_narrow_satcat_predicates(client):
    client.client.satcat.return_value = "[]"
    client.get_active_satellites(1)
    kwargs = client.client.satcat.call_args.kwargs
    assert kwargs["current"] == "Y"
    assert "decay" in kwargs and kwargs["decay"] is None
    assert kwargs["limit"] == 1


@pytest.mark.unit
@pytest.mark.parametrize("response", ["", "not json"])
def test_omm_response_errors_are_explicit(client, response):
    client.client.gp.return_value = response
    with pytest.raises((ValueError, Exception)):
        client.get_omm(25544, datetime.now(timezone.utc))
