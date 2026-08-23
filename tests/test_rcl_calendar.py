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
    assert ctx["week"] == "Baptism of the Lord"
    assert ctx["season"] == "Epiphany"


def test_transfiguration_sunday_2026():
    # Sunday before Ash Wednesday (2026-02-18) is 2026-02-15
    ctx = rcl_context(date(2026, 2, 15))
    assert ctx["week"] == "Transfiguration Sunday"


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


# ---------------------------------------------------------------------------
# Extended fixed-day coverage (Feasts of our Lord + lesser fixed Holy Days)
# ---------------------------------------------------------------------------


def test_christmas_eve_and_day_2025_outrank_weekday():
    assert rcl_context(date(2025, 12, 24))["week"] == "Christmas Eve"
    assert rcl_context(date(2025, 12, 25))["week"] == "Christmas Day"


def test_holy_name_of_jesus_2026():
    assert rcl_context(date(2026, 1, 1))["week"] == "Holy Name of Jesus"


def test_epiphany_of_the_lord_2026():
    assert rcl_context(date(2026, 1, 6))["week"] == "Epiphany of the Lord"


def test_presentation_of_the_lord_2026():
    ctx = rcl_context(date(2026, 2, 2))
    assert ctx == {"year": "A", "week": "Presentation of the Lord", "season": "Epiphany"}


def test_annunciation_of_the_lord_2026():
    ctx = rcl_context(date(2026, 3, 25))
    assert ctx == {"year": "A", "week": "Annunciation of the Lord", "season": "Lent"}


def test_monday_tuesday_wednesday_of_holy_week_2026():
    assert rcl_context(date(2026, 3, 30))["week"] == "Monday of Holy Week"
    assert rcl_context(date(2026, 3, 31))["week"] == "Tuesday of Holy Week"
    assert rcl_context(date(2026, 4, 1))["week"] == "Wednesday of Holy Week"


def test_visitation_yields_to_trinity_sunday_when_they_coincide_2026():
    # 2026-05-31 is both the fixed Feast of the Visitation (May 31) and
    # Trinity Sunday — the Sunday takes precedence per BCP/RCL rubrics.
    ctx = rcl_context(date(2026, 5, 31))
    assert ctx["week"] == "Trinity Sunday"


def test_visitation_resolves_on_a_non_sunday_2027():
    # 2027-05-31 is a Monday, so the fixed feast applies directly.
    ctx = rcl_context(date(2027, 5, 31))
    assert ctx == {"year": "B", "week": "Visitation of Mary to Elizabeth", "season": "Pentecost"}


def test_holy_cross_2026():
    ctx = rcl_context(date(2026, 9, 14))
    assert ctx == {"year": "A", "week": "Holy Cross", "season": "Pentecost"}


def test_all_saints_day_yields_to_proper_sunday_when_they_coincide_2026():
    # 2026-11-01 is both All Saints Day (Nov 1) and Proper 26 — the Sunday
    # takes precedence.
    ctx = rcl_context(date(2026, 11, 1))
    assert ctx["week"] == "Proper 26"


def test_thanksgiving_day_us_2026():
    # 4th Thursday of November, matches Vanderbilt's own listing.
    ctx = rcl_context(date(2026, 11, 26))
    assert ctx == {"year": "A", "week": "Thanksgiving Day", "season": "Pentecost"}


def test_canadian_thanksgiving_day_2026():
    # 2nd Monday of October, matches Vanderbilt's own listing.
    ctx = rcl_context(date(2026, 10, 12))
    assert ctx == {"year": "A", "week": "Canadian Thanksgiving Day", "season": "Pentecost"}
