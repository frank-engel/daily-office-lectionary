"""
Tests for the RCL calendar engine (year A/B/C + week resolution).

Ground-truth dates cross-checked against the issue's own worked example and
Vanderbilt Divinity Library's lectionary database
(https://lectionary.library.vanderbilt.edu/).
"""

from datetime import date

from daily_office_lectionary.calendar.rcl_year import rcl_context


def test_advent_sunday_2026_matches_issue_example():
    # From issue #1: get_rcl_readings("2026-11-29") -> year "B", "First Sunday of Advent"
    ctx = rcl_context(date(2026, 11, 29))
    assert ctx == {"year": "B", "week": "First Sunday of Advent", "season": "Advent"}


def test_second_sunday_of_advent_2026():
    ctx = rcl_context(date(2026, 12, 6))
    assert ctx["week"] == "Second Sunday of Advent"
    assert ctx["year"] == "B"


def test_baptism_of_the_lord_2026():
    ctx = rcl_context(date(2026, 1, 11))
    assert ctx["week"] == "First Sunday after the Epiphany: The Baptism of the Lord"
    assert ctx["season"] == "Epiphany"


def test_last_epiphany_2026():
    # Sunday before Ash Wednesday (2026-02-18) is 2026-02-15
    ctx = rcl_context(date(2026, 2, 15))
    assert ctx["week"] == "Last Sunday after the Epiphany"


def test_ash_wednesday_2026_fixed_weekday():
    ctx = rcl_context(date(2026, 2, 18))
    assert ctx == {"year": "A", "week": "Ash Wednesday", "season": "Lent"}


def test_lent_sundays_2026():
    ctx = rcl_context(date(2026, 2, 22))  # First Sunday in Lent (Ash Wed 2026-02-18)
    assert ctx["week"] == "First Sunday in Lent"


def test_palm_sunday_2026():
    ctx = rcl_context(date(2026, 3, 29))
    assert ctx == {"year": "A", "week": "Palm Sunday", "season": "Lent"}


def test_maundy_thursday_good_friday_holy_saturday_2026():
    assert rcl_context(date(2026, 4, 2))["week"] == "Maundy Thursday"
    assert rcl_context(date(2026, 4, 3))["week"] == "Good Friday"
    assert rcl_context(date(2026, 4, 4))["week"] == "Holy Saturday"


def test_easter_day_2026():
    ctx = rcl_context(date(2026, 4, 5))
    assert ctx == {"year": "A", "week": "Easter Day", "season": "Easter"}


def test_second_sunday_of_easter_2026():
    ctx = rcl_context(date(2026, 4, 12))
    assert ctx["week"] == "Second Sunday of Easter"


def test_ascension_day_2026_fixed_weekday():
    ctx = rcl_context(date(2026, 5, 14))
    assert ctx == {"year": "A", "week": "Ascension Day", "season": "Easter"}


def test_day_of_pentecost_2026():
    ctx = rcl_context(date(2026, 5, 24))
    assert ctx == {"year": "A", "week": "Day of Pentecost", "season": "Pentecost"}


def test_trinity_sunday_2026():
    ctx = rcl_context(date(2026, 5, 31))
    assert ctx == {"year": "A", "week": "Trinity Sunday", "season": "Pentecost"}


def test_proper_16_2026_matches_vanderbilt():
    # Vanderbilt's own database lists "Proper 16 (21) Aug 23, 2026"
    ctx = rcl_context(date(2026, 8, 23))
    assert ctx == {"year": "A", "week": "Proper 16", "season": "Pentecost"}


def test_non_sunday_non_fixed_returns_none():
    assert rcl_context(date(2026, 8, 24)) is None


def test_three_year_cycle_rotation():
    # Advent 2025 -> A, Advent 2026 -> B, Advent 2027 -> C, Advent 2028 -> A
    assert rcl_context(date(2025, 11, 30))["year"] == "A"
    assert rcl_context(date(2026, 11, 29))["year"] == "B"
    assert rcl_context(date(2027, 11, 28))["year"] == "C"
    assert rcl_context(date(2028, 12, 3))["year"] == "A"
