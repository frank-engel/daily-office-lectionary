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
from .rcl.loader import load_rcl
from .rcl.resolver import resolve_rcl

__all__ = [
    "get_readings",
    "get_readings_with_text",
    "get_rcl_readings",
    "get_full_readings",
    "fetch_bible",
    "is_bible_installed",
    "BibleNotInstalledError",
    "OfficeReadings",
    "OfficeReadingsWithText",
    "RCLReadings",
    "FullReadings",
    "Collect",
    "Psalm",
    "PsalmVerse",
    "Lesson",
    "Verse",
    "Liturgy",
]

# The lectionary/collect JSON is ~380 KB total; load it once at import time
# rather than requiring callers to remember an explicit startup step.
load_lectionary()
load_collects()
load_rcl()


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
class Liturgy:
    """A secondary liturgy sharing a date with the primary Sunday/day service.

    Used for the Liturgy of the Palms (Palm Sunday), the Easter Vigil (Holy
    Saturday), and Easter Evening (Easter Day) — each only populates the
    fields that liturgy actually has.
    """

    first_lesson: str | None = None
    psalm: str | None = None
    second_lesson: str | None = None
    gospel: str | None = None


@dataclass
class RCLReadings:
    """Revised Common Lectionary readings for a Sunday (or fixed weekday proper)."""

    date: str
    year: str  # "A" | "B" | "C"
    season: str
    week: str  # "Proper 16", "First Sunday of Advent", "Ash Wednesday", ...
    title: str | None
    track: int | None  # None outside the Season after Pentecost
    first_lesson: str | None
    psalm: str | None
    second_lesson: str | None
    gospel: str | None
    alternate_first_lesson: str | None
    alternate_psalm: str | None
    palms: Liturgy | None  # populated only on Palm Sunday
    vigil: Liturgy | None  # populated only on Holy Saturday
    evening: Liturgy | None  # populated only on Easter Day
    collect: Collect | None


@dataclass
class FullReadings:
    """The BCP 1979 Daily Office and RCL readings for one date, with the shared Collect."""

    date: str
    office: OfficeReadings | None
    rcl: RCLReadings | None
    collect: Collect | None


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


def get_rcl_readings(when: _date | str | None = None, track: int = 2) -> RCLReadings | None:
    """
    Return the Revised Common Lectionary readings for *when* (default: today).

    *track* selects which Season-after-Pentecost Old Testament reading is
    primary (Track 1: semi-continuous narrative; Track 2: thematically
    paired with the Gospel — the default, matching common Rite II practice).
    The non-selected track's citations are always included as
    alternate_first_lesson/alternate_psalm, never silently dropped.

    On Palm Sunday, the top-level fields carry the Liturgy of the Passion
    (the day's principal readings); the Liturgy of the Palms procession
    Gospel and Psalm are returned separately under .palms.

    Returns None if *when* is not a Sunday or one of the fixed RCL weekday
    propers (Ash Wednesday, the Triduum, Ascension Day).
    """
    d = _coerce_date(when)
    result = resolve_rcl(d, track=track)
    if result is None:
        return None
    lit_ctx = liturgical_context(d) or {}
    collect_raw = resolve_collect(d, lit_ctx)

    def _liturgy(raw: dict | None) -> Liturgy | None:
        if not raw:
            return None
        return Liturgy(
            first_lesson=raw.get("first"),
            psalm=raw.get("psalm"),
            second_lesson=raw.get("second"),
            gospel=raw.get("gospel"),
        )

    return RCLReadings(
        date=result["date"],
        year=result["year"],
        season=result["season"],
        week=result["week"],
        title=result.get("title"),
        track=result.get("track"),
        first_lesson=result.get("first_lesson"),
        psalm=result.get("psalm"),
        second_lesson=result.get("second_lesson"),
        gospel=result.get("gospel"),
        alternate_first_lesson=result.get("alternate_first_lesson"),
        alternate_psalm=result.get("alternate_psalm"),
        palms=_liturgy(result.get("palms")),
        vigil=_liturgy(result.get("vigil")),
        evening=_liturgy(result.get("evening")),
        collect=Collect(**collect_raw) if collect_raw else None,
    )


def get_full_readings(when: _date | str | None = None, track: int = 2) -> FullReadings:
    """
    Return both the BCP 1979 Daily Office and RCL readings for *when* (any
    date — default: today), plus the shared Collect of the Day.

    .office is populated whenever the Daily Office resolver has an entry for
    the date (nearly always). .rcl is populated only when the date is a
    Sunday or a fixed RCL weekday proper; it's None on other dates, so
    callers never need to know in advance whether RCL applies. .collect is
    taken from whichever of the two resolved one — both are derived from
    the same underlying Collect resolution, so they agree when both are
    present.
    """
    d = _coerce_date(when)
    office = get_readings(d)
    rcl = get_rcl_readings(d, track=track)
    collect = (office.collect if office else None) or (rcl.collect if rcl else None)
    return FullReadings(date=d.isoformat(), office=office, rcl=rcl, collect=collect)
