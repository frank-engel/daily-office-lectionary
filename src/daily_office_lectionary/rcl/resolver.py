"""
Resolve a calendar date to a Revised Common Lectionary entry.

Lookup order:
  1. Fixed weekday propers (RCL_FIXED_INDEX) — Ash Wednesday, the Triduum,
     and Ascension Day use the same readings every year.
  2. Sunday index (RCL_INDEX), keyed on (year, week).
"""

from datetime import date

from ..calendar.rcl_year import rcl_context
from .loader import RCL_FIXED_INDEX, RCL_INDEX


def resolve_rcl(d: date, track: int = 2) -> dict | None:
    """
    Return a resolved RCL dict for date *d*, or None if no entry exists.

    *track* selects which Season-after-Pentecost OT reading is primary
    (Track 1: semi-continuous; Track 2: thematically paired with the
    Gospel). The non-selected track's citations are always included under
    alternate_first_lesson/alternate_psalm, regardless of which is
    requested — nothing is silently dropped.

    On Palm Sunday, first_lesson/psalm/second_lesson/gospel carry the
    Liturgy of the Passion (the day's principal readings); the Liturgy of
    the Palms procession Gospel and Psalm are additionally returned under
    "palms".

    Returned shape::

        {
            "date": "2026-08-23",
            "year": "A",
            "season": "Pentecost",
            "week": "Proper 16",
            "title": str | None,
            "track": int | None,
            "first_lesson": str | None,
            "psalm": str | None,
            "second_lesson": str | None,
            "gospel": str | None,
            "alternate_first_lesson": str | None,
            "alternate_psalm": str | None,
            "palms": {"gospel": str | None, "psalm": str | None} | None,
        }
    """
    ctx = rcl_context(d)
    if ctx is None:
        return None

    year = ctx["year"]
    week = ctx["week"]
    entry = RCL_FIXED_INDEX.get(week) or RCL_INDEX.get((year, week))
    if entry is None:
        return None

    lessons = entry.get("lessons", {})
    result: dict = {
        "date": d.isoformat(),
        "year": year,
        "season": ctx["season"],
        "week": week,
        "title": entry.get("title"),
        "track": None,
        "first_lesson": None,
        "psalm": None,
        "second_lesson": lessons.get("second"),
        "gospel": lessons.get("gospel"),
        "alternate_first_lesson": None,
        "alternate_psalm": None,
        "palms": None,
    }

    if "palms" in lessons and "passion" in lessons:
        passion = lessons["passion"]
        result["first_lesson"] = passion.get("first")
        result["psalm"] = passion.get("psalm")
        result["second_lesson"] = passion.get("second")
        result["gospel"] = passion.get("gospel")
        result["palms"] = dict(lessons["palms"])
        return result

    if "track1" in lessons and "track2" in lessons:
        primary = lessons.get(f"track{track}", {})
        alternate = lessons.get("track2" if track == 1 else "track1", {})
        result["track"] = track
        result["first_lesson"] = primary.get("first")
        result["psalm"] = primary.get("psalm")
        result["alternate_first_lesson"] = alternate.get("first")
        result["alternate_psalm"] = alternate.get("psalm")
        return result

    # Flat shape: a single OT reading, no track split
    result["first_lesson"] = lessons.get("first")
    result["psalm"] = lessons.get("psalm")
    return result
