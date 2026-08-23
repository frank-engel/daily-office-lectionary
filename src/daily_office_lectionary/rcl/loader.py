"""
Load the Revised Common Lectionary JSON files into in-memory indexes.

Indexes built:
  RCL_INDEX      : Dict[(year: str, week: str), entry]
                   Keyed on RCL Year A/B/C and the week name produced by
                   calendar.rcl_year.rcl_context.
  RCL_FIXED_INDEX: Dict[str, entry]
                   Keyed on the fixed weekday propers' week name (e.g.
                   "Ash Wednesday"), which use the same readings every year
                   regardless of the A/B/C cycle.
"""

import json
import logging
from pathlib import Path
from typing import TypeAlias

log = logging.getLogger(__name__)

# Type aliases
RCLKey: TypeAlias = tuple[str, str]  # (year, week)
RCLIndex: TypeAlias = dict[RCLKey, dict]
RCLFixedIndex: TypeAlias = dict[str, dict]

# Populated by load_rcl()
RCL_INDEX: RCLIndex = {}
RCL_FIXED_INDEX: RCLFixedIndex = {}

_DATA_DIR = Path(__file__).parent.parent / "data" / "rcl"

_YEAR_FILES = [
    (_DATA_DIR / "year_a.json", "A"),
    (_DATA_DIR / "year_b.json", "B"),
    (_DATA_DIR / "year_c.json", "C"),
]


def load_rcl() -> None:
    """Load all RCL JSON files and populate RCL_INDEX and RCL_FIXED_INDEX."""
    RCL_INDEX.clear()
    RCL_FIXED_INDEX.clear()

    for path, year in _YEAR_FILES:
        if not path.exists():
            log.error("Missing RCL file: %s", path)
            continue
        with open(path, encoding="utf-8") as f:
            entries = json.load(f)
        dupes = 0
        for entry in entries:
            week = entry.get("week", "")
            if not week:
                log.warning("RCL entry missing 'week' field, skipping: %s", entry.get("title"))
                continue
            key: RCLKey = (year, week)
            if key in RCL_INDEX:
                dupes += 1
                log.debug("Duplicate RCL key %s — keeping first", key)
            else:
                RCL_INDEX[key] = entry
        log.info("Loaded %s: %d entries (%d dupes skipped)", path.name, len(entries), dupes)

    fixed_path = _DATA_DIR / "fixed_days.json"
    if fixed_path.exists():
        with open(fixed_path, encoding="utf-8") as f:
            entries = json.load(f)
        for entry in entries:
            week = entry.get("week", "")
            if week:
                RCL_FIXED_INDEX[week] = entry
        log.info("Loaded %s: %d fixed-day entries", fixed_path.name, len(RCL_FIXED_INDEX))

    log.info(
        "RCL lectionary loaded: %d Sunday entries, %d fixed-day entries",
        len(RCL_INDEX),
        len(RCL_FIXED_INDEX),
    )
