"""
daily-office-lectionary: BCP 1979 Daily Office readings for any date.

Light mode (the default) needs no extra install, no network access, and no
dependencies beyond the standard library. It returns scripture *references*
(e.g. "Isa 1:1-9") and the full text of the Collect of the Day (small,
public-domain BCP prayer text).

Full mode additionally resolves scripture *verse text*, once the public
domain KJVA Bible database has been downloaded once via fetch_bible().

    >>> from daily_office_lectionary import get_readings
    >>> readings = get_readings("2026-04-05")
    >>> readings.week
    'Easter Week'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date

from .bible.db import fetch_psalm_token, fetch_verses
from .bible.fetch import BibleNotInstalledError, fetch_bible, is_bible_installed
from .calendar.liturgical_year import liturgical_context
from .collects.loader import load_collects
from .collects.resolver import resolve_collect
from .lectionary.loader import load_lectionary
from .lectionary.resolver import resolve_office

__all__ = [
    "get_readings",
    "get_readings_with_text",
    "fetch_bible",
    "is_bible_installed",
    "BibleNotInstalledError",
    "OfficeReadings",
    "OfficeReadingsWithText",
    "Collect",
    "Psalm",
    "PsalmVerse",
    "Lesson",
    "Verse",
]

# The lectionary/collect JSON is ~380 KB total; load it once at import time
# rather than requiring callers to remember an explicit startup step.
load_lectionary()
load_collects()


@dataclass
class Collect:
    title: str
    preface: str
    traditional: str
    contemporary: str


@dataclass
class Verse:
    book: str
    chapter: int
    verse: int
    text: str


@dataclass
class PsalmVerse:
    psalm: int
    verse: int
    text: str


@dataclass
class Psalm:
    number: int
    verses: list[PsalmVerse] = field(default_factory=list)


@dataclass
class Lesson:
    reference: str | None
    verses: list[Verse] = field(default_factory=list)


@dataclass
class OfficeReadings:
    """Light mode: references only, no scripture verse text."""

    date: str
    title: str | None
    season: str
    week: str
    cycle: int
    psalms: dict[str, list[str]]
    morning_lessons: dict[str, str]
    evening_lessons: dict[str, str]
    collect: Collect | None


@dataclass
class OfficeReadingsWithText:
    """Full mode: same as OfficeReadings, with resolved scripture verse text."""

    date: str
    title: str | None
    season: str
    week: str
    cycle: int
    morning_psalms: list[Psalm]
    evening_psalms: list[Psalm]
    morning_lessons: dict[str, Lesson]
    evening_lessons: dict[str, Lesson]
    collect: Collect | None


def _coerce_date(when: _date | str | None) -> _date:
    if when is None:
        return _date.today()
    if isinstance(when, str):
        return _date.fromisoformat(when)
    return when


def get_readings(when: _date | str | None = None) -> OfficeReadings | None:
    """
    Return the BCP 1979 Daily Office readings for *when* (default: today).

    Pure stdlib, no network, no extra install required. Scripture lessons are
    returned as reference strings (e.g. "Isa 1:1-9"); psalms as lectionary
    tokens (e.g. "23", "119:1-24"). The Collect of the Day is included in full.

    Returns None if no lectionary entry exists for the date.
    """
    d = _coerce_date(when)
    result = resolve_office(d)
    if result is None:
        return None
    lit_ctx = liturgical_context(d) or {}
    collect_raw = resolve_collect(d, lit_ctx)
    return OfficeReadings(
        date=result["date"],
        title=result.get("title"),
        season=result["season"],
        week=result["week"],
        cycle=result["cycle"],
        psalms=result["psalms"],
        morning_lessons=result["morning_lessons"],
        evening_lessons=result["evening_lessons"],
        collect=Collect(**collect_raw) if collect_raw else None,
    )


def get_readings_with_text(
    when: _date | str | None = None, translation: str = "kjva"
) -> OfficeReadingsWithText | None:
    """
    Return the BCP 1979 Daily Office readings for *when*, with full scripture
    verse text resolved from a local Bible database.

    Raises BibleNotInstalledError if *translation*'s database hasn't been
    downloaded yet — call fetch_bible() first, or run
    `daily-office-lectionary fetch-bible`.

    Returns None if no lectionary entry exists for the date.
    """
    light = get_readings(when)
    if light is None:
        return None
    if not is_bible_installed(translation):
        raise BibleNotInstalledError(
            f"No local Bible database found for translation {translation!r}. "
            "Call fetch_bible() first, or run `daily-office-lectionary fetch-bible`."
        )

    def _expand_lessons(lessons: dict[str, str]) -> dict[str, Lesson]:
        out: dict[str, Lesson] = {}
        for key, ref in lessons.items():
            if ref:
                raw = fetch_verses(ref)
                out[key] = Lesson(reference=ref, verses=[Verse(**v) for v in raw])
            else:
                out[key] = Lesson(reference=None, verses=[])
        return out

    def _expand_psalms(tokens: list[str]) -> list[Psalm]:
        psalms = []
        for token in tokens:
            entry = fetch_psalm_token(token)
            psalms.append(
                Psalm(number=entry["psalm"], verses=[PsalmVerse(**v) for v in entry["verses"]])
            )
        return psalms

    return OfficeReadingsWithText(
        date=light.date,
        title=light.title,
        season=light.season,
        week=light.week,
        cycle=light.cycle,
        morning_psalms=_expand_psalms(light.psalms.get("morning", [])),
        evening_psalms=_expand_psalms(light.psalms.get("evening", [])),
        morning_lessons=_expand_lessons(light.morning_lessons),
        evening_lessons=_expand_lessons(light.evening_lessons),
        collect=light.collect,
    )
