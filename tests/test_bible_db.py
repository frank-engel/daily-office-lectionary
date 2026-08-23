"""
Integration tests for bible/db.py — hit the real KJVA Bible database.

Skipped automatically if it hasn't been downloaded (run `task fetch-bible`
or `daily-office-lectionary fetch-bible` first) so `task test` works without it.
"""

import pytest

from daily_office_lectionary.bible.db import fetch_psalm, fetch_psalm_token, fetch_verses
from daily_office_lectionary.bible.fetch import is_bible_installed

pytestmark = pytest.mark.skipif(
    not is_bible_installed(), reason="KJVA Bible database not downloaded (run `task fetch-bible`)"
)


def test_fetch_psalm_23():
    verses = fetch_psalm(23)
    assert len(verses) == 6
    assert verses[0]["verse"] == 1
    assert "shepherd" in verses[0]["text"].lower()


def test_fetch_psalm_119_first_verse():
    verses = fetch_psalm(119)
    assert verses[0]["verse"] == 1
    assert len(verses) > 100  # Psalm 119 has 176 verses


def test_fetch_verses_simple_range():
    verses = fetch_verses("Isa 1:1–9")
    assert len(verses) == 9
    assert verses[0]["chapter"] == 1
    assert verses[0]["verse"] == 1


def test_fetch_verses_cross_chapter():
    verses = fetch_verses("Luke 20:41–21:4")
    chapters = {v["chapter"] for v in verses}
    assert 20 in chapters
    assert 21 in chapters


def test_fetch_verses_sirach():
    verses = fetch_verses("Sir 1:1–5")
    assert len(verses) == 5
    assert "wisdom" in verses[0]["text"].lower()


def test_fetch_verses_wisdom():
    verses = fetch_verses("Wis 1:1–5")
    assert len(verses) >= 1


def test_fetch_verses_multi_range():
    verses = fetch_verses("Isa 5:8–12, 18–23")
    verse_nums = [v["verse"] for v in verses]
    assert 8 in verse_nums
    assert 12 in verse_nums
    assert 18 in verse_nums
    assert 23 in verse_nums
    # verses 13–17 should NOT be present
    assert 13 not in verse_nums


def test_fetch_verses_semicolon_separated():
    verses = fetch_verses("Gal 3:23–29; 4:4–7")
    chapters = [v["chapter"] for v in verses]
    assert 3 in chapters
    assert 4 in chapters


def test_fetch_verses_parenthetical_stripped():
    # John 17:1–11(12–26) should return only verses 1-11
    verses = fetch_verses("John 17:1–11(12–26)")
    assert all(v["verse"] <= 11 for v in verses)
    assert len(verses) == 11


# ---------------------------------------------------------------------------
# fetch_psalm_token — the three lectionary psalm token formats
# ---------------------------------------------------------------------------


def test_plain_integer_token():
    entry = fetch_psalm_token("23")
    assert entry["psalm"] == 23
    assert len(entry["verses"]) == 6
    assert "shepherd" in entry["verses"][0]["text"].lower()


def test_bracketed_optional_token():
    # "[58]" — optional psalm, square brackets stripped
    entry = fetch_psalm_token("[58]")
    assert entry["psalm"] == 58
    assert len(entry["verses"]) > 0


def test_verse_range_token():
    # "119:1–24" — verse range, en-dash separator
    entry = fetch_psalm_token("119:1–24")
    assert entry["psalm"] == 119
    assert len(entry["verses"]) == 24
    assert entry["verses"][0]["verse"] == 1
    assert entry["verses"][-1]["verse"] == 24


def test_verse_range_with_optional_extension_token():
    # "21:1–7(8–14)" — range with parenthetical extension (stripped)
    entry = fetch_psalm_token("21:1–7(8–14)")
    assert entry["psalm"] == 21
    assert entry["verses"][0]["verse"] == 1
    assert entry["verses"][-1]["verse"] == 7


def test_christmas_evening_psalm_token():
    # The real problematic token from the Christmas entry
    entry = fetch_psalm_token("110:1–5(6–7)")
    assert entry["psalm"] == 110
    assert entry["verses"][0]["verse"] == 1
    assert entry["verses"][-1]["verse"] == 5
