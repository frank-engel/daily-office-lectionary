"""
RCL calendar engine: given a date, determine the Revised Common Lectionary
year (A/B/C) and week name for RCL lectionary lookup.

Resolution order (mirrors BCP precedence — Principal Feasts, then Sundays,
then lesser Holy Days):
  1. Fixed "Feasts of our Lord" (Christmas Eve/Day, Holy Name, Epiphany) —
     these win even when they fall on a Sunday.
  2. Fixed weekday propers relative to Easter (Ash Wednesday through the
     Triduum, Ascension Day) — never fall on a Sunday, so no conflict.
  3. Sundays (Advent through the Season after Pentecost).
  4. Lesser fixed Holy Days (Presentation, Annunciation, Visitation, Holy
     Cross, All Saints, the Thanksgivings) — only resolved when the date
     isn't itself a Sunday, since an ordinary Sunday's Proper takes
     precedence over a lesser feast that happens to coincide with it.
"""

from datetime import date, timedelta

from .computus import (
    ascension_day,
    ash_wednesday,
    easter_sunday,
    first_sunday_of_advent,
    pentecost,
    proper_sundays,
    trinity_sunday,
)
from .computus import palm_sunday as _palm_sunday_date

_ORDINALS = [
    "First",
    "Second",
    "Third",
    "Fourth",
    "Fifth",
    "Sixth",
    "Seventh",
    "Eighth",
    "Ninth",
    "Tenth",
]

# Feasts of our Lord fixed to the civil calendar, regardless of weekday —
# these outrank even a Sunday when they coincide.
_PRINCIPAL_FIXED_DATES: dict[tuple[int, int], tuple[str, str]] = {
    (12, 24): ("Christmas Eve", "Christmas"),
    (12, 25): ("Christmas Day", "Christmas"),
    (1, 1): ("Holy Name of Jesus", "Christmas"),
    (1, 6): ("Epiphany of the Lord", "Epiphany"),
}

# Lesser fixed Holy Days: resolved only when the date isn't itself a Sunday —
# an ordinary Sunday's Proper takes precedence over these when they coincide.
_LESSER_FIXED_DATES: dict[tuple[int, int], tuple[str, str]] = {
    (2, 2): ("Presentation of the Lord", "Epiphany"),
    (3, 25): ("Annunciation of the Lord", "Lent"),
    (5, 31): ("Visitation of Mary to Elizabeth", "Pentecost"),
    (9, 14): ("Holy Cross", "Pentecost"),
    (11, 1): ("All Saints Day", "Pentecost"),
}

# Fixed weekday propers relative to Easter (same readings every year).
_FIXED_WEEKDAYS: list[tuple[str, str]] = [
    ("Ash Wednesday", "Lent"),
    ("Monday of Holy Week", "Lent"),
    ("Tuesday of Holy Week", "Lent"),
    ("Wednesday of Holy Week", "Lent"),
    ("Maundy Thursday", "Lent"),
    ("Good Friday", "Lent"),
    ("Holy Saturday", "Lent"),
    ("Ascension Day", "Easter"),
]


def _fixed_weekday_date(name: str, easter_year: int) -> date:
    if name == "Ash Wednesday":
        return ash_wednesday(easter_year)
    palm = _palm_sunday_date(easter_year)
    if name == "Monday of Holy Week":
        return palm + timedelta(days=1)
    if name == "Tuesday of Holy Week":
        return palm + timedelta(days=2)
    if name == "Wednesday of Holy Week":
        return palm + timedelta(days=3)
    if name == "Maundy Thursday":
        return palm + timedelta(days=4)
    if name == "Good Friday":
        return palm + timedelta(days=5)
    if name == "Holy Saturday":
        return palm + timedelta(days=6)
    return ascension_day(easter_year)  # "Ascension Day"


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    """The nth occurrence (1-indexed) of *weekday* (Mon=0..Sun=6) in *month*."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _next_sunday_after(d: date) -> date:
    """First Sunday strictly after d."""
    days = (7 - ((d.weekday() + 1) % 7)) % 7
    if days == 0:
        days = 7
    return d + timedelta(days=days)


def rcl_context(d: date) -> dict | None:
    """
    Return the RCL context for date *d*:
        {"year": "A"|"B"|"C", "week": str, "season": str}

    Returns None for dates outside RCL coverage.
    """
    # Determine which Easter year and RCL year (A/B/C) govern this date,
    # mirroring calendar.liturgical_year.liturgical_context's Advent-anchor
    # logic — RCL and the BCP Daily Office share the same liturgical-year
    # boundary (the First Sunday of Advent).
    advent_this = first_sunday_of_advent(d.year)
    if d >= advent_this:
        advent_year = d.year
        easter_year = d.year + 1
        advent_start = advent_this
    else:
        advent_year = d.year - 1
        easter_year = d.year
        advent_start = first_sunday_of_advent(d.year - 1)

    year = ["A", "B", "C"][(advent_year - 2022) % 3]

    # ── FEASTS OF OUR LORD (fixed date; outrank even a Sunday) ─────────────
    principal = _PRINCIPAL_FIXED_DATES.get((d.month, d.day))
    if principal:
        week, season = principal
        return {"year": year, "week": week, "season": season}

    # ── FIXED WEEKDAY PROPERS (relative to Easter; never fall on a Sunday) ─
    for name, season in _FIXED_WEEKDAYS:
        if _fixed_weekday_date(name, easter_year) == d:
            return {"year": year, "week": name, "season": season}

    if d.weekday() == 6:
        easter = easter_sunday(easter_year)
        ash = ash_wednesday(easter_year)
        palm = _palm_sunday_date(easter_year)
        pent = pentecost(easter_year)
        trinity = trinity_sunday(easter_year)
        christmas = date(easter_year - 1, 12, 25)
        jan6 = date(easter_year, 1, 6)

        # ── ADVENT ───────────────────────────────────────────────────────
        if advent_start <= d < christmas:
            n = (d - advent_start).days // 7 + 1
            return {
                "year": year,
                "week": f"{_ORDINALS[n - 1]} Sunday of Advent",
                "season": "Advent",
            }

        # ── CHRISTMAS ────────────────────────────────────────────────────
        if christmas <= d < jan6:
            week = (
                "First Sunday after Christmas Day"
                if d.month == 12
                else "Second Sunday after Christmas Day"
            )
            return {"year": year, "week": week, "season": "Christmas"}

        baptism_sunday = _next_sunday_after(jan6)
        last_epi_sunday = ash - timedelta(days=3)

        # ── EPIPHANY ─────────────────────────────────────────────────────
        if baptism_sunday <= d < ash:
            if d == baptism_sunday:
                week = "Baptism of the Lord"
            elif d >= last_epi_sunday:
                week = "Transfiguration Sunday"
            else:
                n = (d - baptism_sunday).days // 7 + 1
                week = f"{_ORDINALS[n - 1]} Sunday after the Epiphany"
            return {"year": year, "week": week, "season": "Epiphany"}

        lent1_sunday = _next_sunday_after(ash)

        # ── LENT ─────────────────────────────────────────────────────────
        if lent1_sunday <= d < palm:
            n = (d - lent1_sunday).days // 7 + 1
            return {
                "year": year,
                "week": f"{_ORDINALS[n - 1]} Sunday in Lent",
                "season": "Lent",
            }

        # ── PALM SUNDAY ──────────────────────────────────────────────────
        if d == palm:
            return {"year": year, "week": "Palm Sunday", "season": "Lent"}

        # ── EASTER DAY ───────────────────────────────────────────────────
        if d == easter:
            return {"year": year, "week": "Easter Day", "season": "Easter"}

        easter2 = easter + timedelta(days=7)

        # ── EASTER 2-7 ───────────────────────────────────────────────────
        if easter2 <= d < pent:
            n = (d - easter2).days // 7 + 2
            return {
                "year": year,
                "week": f"{_ORDINALS[n - 1]} Sunday of Easter",
                "season": "Easter",
            }

        # ── DAY OF PENTECOST ─────────────────────────────────────────────
        if d == pent:
            return {"year": year, "week": "Day of Pentecost", "season": "Pentecost"}

        # ── TRINITY SUNDAY ───────────────────────────────────────────────
        if d == trinity:
            return {"year": year, "week": "Trinity Sunday", "season": "Pentecost"}

        # ── SEASON AFTER PENTECOST (Proper N) ──────────────────────────
        for n, sun in proper_sundays(easter_year):
            if sun == d:
                return {"year": year, "week": f"Proper {n}", "season": "Pentecost"}

        return None  # a Sunday, but outside every defined RCL window

    # ── LESSER FIXED HOLY DAYS (yield to an ordinary Sunday) ────────────────
    lesser = _LESSER_FIXED_DATES.get((d.month, d.day))
    if lesser:
        week, season = lesser
        return {"year": year, "week": week, "season": season}
    if d == _nth_weekday_of_month(d.year, 11, 3, 4):  # 4th Thursday of November
        return {"year": year, "week": "Thanksgiving Day", "season": "Pentecost"}
    if d == _nth_weekday_of_month(d.year, 10, 0, 2):  # 2nd Monday of October
        return {"year": year, "week": "Canadian Thanksgiving Day", "season": "Pentecost"}

    return None
