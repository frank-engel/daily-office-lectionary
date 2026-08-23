"""
Tests for the RCL loader and resolver.
"""

from datetime import date

import pytest

from daily_office_lectionary.rcl.loader import RCL_INDEX, load_rcl
from daily_office_lectionary.rcl.resolver import resolve_rcl


@pytest.fixture(scope="module", autouse=True)
def loaded_index():
    load_rcl()


def test_advent_sunday_2026_matches_issue_example():
    # From issue #1's own worked example.
    result = resolve_rcl(date(2026, 11, 29), track=2)
    assert result["year"] == "B"
    assert result["title"] == "First Sunday of Advent"
    assert result["first_lesson"] == "Isa 64:1-9"
    assert result["psalm"] == "80:1-7, 17-19"
    assert result["second_lesson"] == "1 Cor 1:3-9"
    assert result["gospel"] == "Mark 13:24-37"
    # No track split outside the Season after Pentecost.
    assert result["track"] is None
    assert result["alternate_first_lesson"] is None


def test_proper_default_track_is_2():
    result = resolve_rcl(date(2026, 8, 23))
    assert result["track"] == 2
    assert result["first_lesson"] == "Isa 51:1-6"
    assert result["psalm"] == "138"
    # Track 1's citations are still exposed, not silently dropped.
    assert result["alternate_first_lesson"] == "Exod 1:8-2:10"
    assert result["alternate_psalm"] == "124"


def test_proper_track_1_flips_primary_and_alternate():
    result = resolve_rcl(date(2026, 8, 23), track=1)
    assert result["track"] == 1
    assert result["first_lesson"] == "Exod 1:8-2:10"
    assert result["psalm"] == "124"
    assert result["alternate_first_lesson"] == "Isa 51:1-6"
    assert result["alternate_psalm"] == "138"
    # Second lesson and Gospel are shared between tracks.
    assert result["second_lesson"] == "Rom 12:1-8"
    assert result["gospel"] == "Matt 16:13-20"


def test_palm_sunday_embeds_both_liturgies():
    result = resolve_rcl(date(2026, 3, 29))
    assert result["week"] == "Palm Sunday"
    # Primary fields carry the Liturgy of the Passion.
    assert result["first_lesson"] == "Isa 50:4-9a"
    assert result["gospel"] == "Matt 26:14-27:66"
    # The Liturgy of the Palms procession is embedded, not dropped.
    assert result["palms"] == {"gospel": "Matt 21:1-11", "psalm": "118:1-2, 19-29"}


def test_fixed_weekday_proper_ash_wednesday():
    result = resolve_rcl(date(2026, 2, 18))
    assert result["week"] == "Ash Wednesday"
    assert result["first_lesson"] == "Joel 2:1-2, 12-17"
    assert result["gospel"] == "Matt 6:1-6, 16-21"


def test_fixed_weekday_proper_same_readings_every_year():
    # Ash Wednesday falls on different calendar dates each year, but the
    # fixed-day index is year-independent, so both should resolve.
    ash_2026 = resolve_rcl(date(2026, 2, 18))
    ash_2027 = resolve_rcl(date(2027, 2, 10))
    assert ash_2026["first_lesson"] == ash_2027["first_lesson"] == "Joel 2:1-2, 12-17"
    assert ash_2026["year"] != ash_2027["year"]  # different RCL year, same readings


def test_non_sunday_non_fixed_date_returns_none():
    assert resolve_rcl(date(2026, 8, 24)) is None


def test_year_a_year_c_advent_lookups():
    result_a = resolve_rcl(date(2025, 11, 30))  # Advent 2025 -> Year A
    assert result_a["year"] == "A"
    assert result_a["first_lesson"] == "Isa 2:1-5"

    result_c = resolve_rcl(date(2027, 11, 28))  # Advent 2027 -> Year C
    assert result_c["year"] == "C"
    assert result_c["first_lesson"] == "Jer 33:14-16"


def test_index_loaded():
    assert ("A", "First Sunday of Advent") in RCL_INDEX
    assert ("B", "First Sunday of Advent") in RCL_INDEX
    assert ("C", "First Sunday of Advent") in RCL_INDEX
