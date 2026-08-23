"""
Tests for the top-level get_rcl_readings() and get_full_readings() API.
"""

from daily_office_lectionary import get_full_readings, get_rcl_readings, get_readings


def test_get_rcl_readings_matches_issue_example():
    rcl = get_rcl_readings("2026-11-29", track=2)
    assert rcl.year == "B"
    assert rcl.title == "First Sunday of Advent"
    assert rcl.first_lesson == "Isa 64:1-9"
    assert rcl.psalm == "80:1-7, 17-19"
    assert rcl.second_lesson == "1 Cor 1:3-9"
    assert rcl.gospel == "Mark 13:24-37"
    assert rcl.collect is not None
    assert rcl.collect.title == "First Sunday of Advent"


def test_get_rcl_readings_returns_none_for_ordinary_weekday():
    assert get_rcl_readings("2026-08-24") is None


def test_get_full_readings_sunday_includes_both_and_shared_collect():
    full = get_full_readings("2026-11-29")
    assert full.office is not None
    assert full.rcl is not None
    assert full.collect is not None
    # Both resolvers route through the same Collect resolution.
    assert full.collect == get_readings("2026-11-29").collect
    assert full.collect == full.rcl.collect


def test_get_full_readings_weekday_has_office_only():
    full = get_full_readings("2026-08-24")
    assert full.office is not None
    assert full.rcl is None
    # The Collect still resolves from the Office side alone.
    assert full.collect is not None


def test_get_full_readings_default_track_is_2():
    full = get_full_readings("2026-08-23")
    assert full.rcl.track == 2
