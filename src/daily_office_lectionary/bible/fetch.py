"""
On-demand download of the public-domain KJVA Bible SQLite database, so
"full mode" (actual scripture verse text) stays out of the base install.

Source: scrollmapper/bible_databases (MIT-licensed repo of public-domain
Bible texts) — https://github.com/scrollmapper/bible_databases
"""

from __future__ import annotations

import os
import urllib.request
from pathlib import Path

# Pinned to a specific commit rather than `master`: the branch tip has, at
# times, pointed to a KJVA.db build with every verse row duplicated several
# times over (see NOTICE.md). Pinning gives a reproducible, verified-good file.
_KJVA_COMMIT = "a228a19a29099a41c196c2a310cd93e50a390e30"
_KJVA_URL = (
    "https://raw.githubusercontent.com/scrollmapper/bible_databases/"
    f"{_KJVA_COMMIT}/formats/sqlite/KJVA.db"
)

_SOURCES: dict[str, str] = {
    "kjva": _KJVA_URL,
}


class BibleNotInstalledError(RuntimeError):
    """Raised when full-mode Bible text is requested but hasn't been downloaded yet."""


def cache_dir() -> Path:
    """Return the local cache directory for downloaded Bible databases, creating it if needed."""
    base = os.environ.get("XDG_CACHE_HOME") or os.environ.get("LOCALAPPDATA")
    root = (
        Path(base) / "daily-office-lectionary"
        if base
        else Path.home() / ".cache" / "daily-office-lectionary"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def bible_db_path(translation: str = "kjva") -> Path:
    """Return the local cache path for *translation*'s Bible database (may not exist yet)."""
    return cache_dir() / f"{translation.lower()}.db"


def is_bible_installed(translation: str = "kjva") -> bool:
    """Return True if *translation*'s Bible database has already been downloaded."""
    return bible_db_path(translation).exists()


def fetch_bible(
    translation: str = "kjva", dest: str | Path | None = None, force: bool = False
) -> Path:
    """
    Download the public-domain Bible SQLite database for *translation* into the
    local cache (or *dest*, if given). Returns the local file path.

    A no-op if the file already exists, unless *force* is True.
    """
    translation = translation.lower()
    if translation not in _SOURCES:
        raise ValueError(
            f"Unsupported translation: {translation!r}. Supported: {', '.join(sorted(_SOURCES))}."
        )

    target = Path(dest) if dest is not None else bible_db_path(translation)
    if target.exists() and not force:
        return target

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(_SOURCES[translation]) as response:
        with open(tmp, "wb") as out:
            while chunk := response.read(1 << 20):
                out.write(chunk)
    tmp.replace(target)
    return target
