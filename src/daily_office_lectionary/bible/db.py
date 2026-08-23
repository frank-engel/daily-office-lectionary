"""
Synchronous SQLite verse lookup against a downloaded KJVA Bible database
(KJVA_books / KJVA_verses tables).

Public API:
  fetch_verses(ref_str)     → list[dict]  — parse a lectionary reference, fetch verses
  fetch_psalm(number)       → list[dict]  — fetch all verses of a psalm
  fetch_psalm_token(token)  → dict        — resolve one lectionary psalm token
"""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path

from .book_map import book_id
from .fetch import BibleNotInstalledError, bible_db_path
from .reference_parser import VerseRange, parse_reference

log = logging.getLogger(__name__)

_MISSING_TEXT = "[Text not available in this edition]"

_PLAIN_RE = re.compile(r"^\d+$")
_BRACKETED_RE = re.compile(r"^\[(\d+)\]$")


def _require_db(db_path: str | Path | None) -> Path:
    path = Path(db_path) if db_path is not None else bible_db_path()
    if not path.exists():
        raise BibleNotInstalledError(
            f"Bible database not found at {path}. Call fetch_bible() first, "
            "or run `daily-office-lectionary fetch-bible`."
        )
    return path


def _fetch_range(conn: sqlite3.Connection, vr: VerseRange) -> list[dict]:
    """Fetch all verses for a single VerseRange."""
    bid = book_id(vr.book)
    if bid is None:
        log.warning("Unknown book abbreviation: %s", vr.book)
        return [
            {
                "book": vr.book,
                "chapter": vr.start_chapter,
                "verse": vr.start_verse,
                "text": _MISSING_TEXT,
            }
        ]

    # GROUP BY collapses duplicate (chapter, verse) rows — some upstream KJVA.db
    # builds have contained repeated rows per verse; grouping keeps this query
    # correct regardless of that data-quality issue.
    params: tuple[int, ...]
    if vr.start_chapter == vr.end_chapter:
        sql = """
            SELECT chapter, verse, text
            FROM KJVA_verses
            WHERE book_id = ? AND chapter = ? AND verse BETWEEN ? AND ?
            GROUP BY chapter, verse
            ORDER BY chapter, verse
        """
        params = (bid, vr.start_chapter, vr.start_verse, vr.end_verse)
    else:
        # Cross-chapter range
        sql = """
            SELECT chapter, verse, text
            FROM KJVA_verses
            WHERE book_id = ?
              AND (
                (chapter = ? AND verse >= ?)
                OR (chapter > ? AND chapter < ?)
                OR (chapter = ? AND verse <= ?)
              )
            GROUP BY chapter, verse
            ORDER BY chapter, verse
        """
        params = (
            bid,
            vr.start_chapter,
            vr.start_verse,
            vr.start_chapter,
            vr.end_chapter,
            vr.end_chapter,
            vr.end_verse,
        )

    rows = [
        {"book": vr.book, "chapter": row[0], "verse": row[1], "text": row[2]}
        for row in conn.execute(sql, params)
    ]

    if not rows:
        log.warning(
            "No verses found for %s %d:%d–%d:%d",
            vr.book,
            vr.start_chapter,
            vr.start_verse,
            vr.end_chapter,
            vr.end_verse,
        )
        rows.append(
            {
                "book": vr.book,
                "chapter": vr.start_chapter,
                "verse": vr.start_verse,
                "text": _MISSING_TEXT,
            }
        )
    return rows


def fetch_verses(ref_str: str, db_path: str | Path | None = None) -> list[dict]:
    """
    Parse *ref_str* and return all matching verses as a list of dicts.

    Each dict: {"book": str, "chapter": int, "verse": int, "text": str}
    Returns a single-element list with the missing-text sentinel on failure.
    Raises BibleNotInstalledError if the local Bible database hasn't been
    downloaded yet — call fetch_bible() first.
    """
    if not ref_str or not ref_str.strip():
        return []

    ranges = parse_reference(ref_str)
    if not ranges:
        log.warning("Could not parse reference: %r", ref_str)
        return [{"book": "", "chapter": 0, "verse": 0, "text": _MISSING_TEXT}]

    path = _require_db(db_path)
    with sqlite3.connect(path) as conn:
        results: list[dict] = []
        for vr in ranges:
            results.extend(_fetch_range(conn, vr))
    return results


def fetch_psalm(number: int | str, db_path: str | Path | None = None) -> list[dict]:
    """Fetch all verses of a psalm by number."""
    n = int(number)
    bid = book_id("Ps")
    path = _require_db(db_path)
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT chapter, verse, text FROM KJVA_verses"
            " WHERE book_id = ? AND chapter = ? GROUP BY verse ORDER BY verse",
            (bid, n),
        )
        return [{"psalm": n, "verse": row[1], "text": row[2]} for row in rows]


def fetch_psalm_token(token: str, db_path: str | Path | None = None) -> dict:
    """
    Resolve one lectionary psalm token to {"psalm": int, "verses": [...]}.

    Handles the three forms found in the lectionary JSON:
      "23"            plain integer — whole psalm
      "[58]"          bracketed optional — strip brackets, whole psalm
      "119:1–24"      verse range (with optional "(...)" extension, dropped)
    """
    token = token.strip()

    m = _BRACKETED_RE.match(token)
    if m:
        n = int(m.group(1))
        return {"psalm": n, "verses": fetch_psalm(n, db_path)}

    if _PLAIN_RE.match(token):
        n = int(token)
        return {"psalm": n, "verses": fetch_psalm(n, db_path)}

    n = int(token.split(":")[0])
    raw = fetch_verses(f"Ps {token}", db_path)
    verses = [{"psalm": n, "verse": v["verse"], "text": v["text"]} for v in raw]
    return {"psalm": n, "verses": verses}
