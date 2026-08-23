# daily-office-lectionary

BCP 1979 Daily Office readings for any date — psalms, scripture lessons, and
the Collect of the Day — plus optional Revised Common Lectionary (RCL)
readings for Sundays. Pure Python, no required dependencies.

```python
from daily_office_lectionary import get_readings

readings = get_readings("2026-04-05")
readings.week  # "Easter Week"
readings.psalms["morning"]  # ["148", "149", "150"]
readings.morning_lessons  # {"first": "Exod 12:1-14", "second": "John 1:1-18"}
readings.collect.contemporary
```

## Revised Common Lectionary (RCL)

The Daily Office (2-year cycle, Year One/Two) and the RCL (3-year cycle,
Year A/B/C) are separate systems — the Collect of the Day is the one thing
they share. `get_rcl_readings()` covers "what's read at Mass," the same way
`get_readings()` covers "what's prayed privately":

```python
from daily_office_lectionary import get_rcl_readings

rcl = get_rcl_readings("2026-11-29", track=2)
rcl.year  # "B"
rcl.title  # "First Sunday of Advent"
rcl.first_lesson  # "Isa 64:1-9"
rcl.psalm  # "80:1-7, 17-19"
rcl.second_lesson  # "1 Cor 1:3-9"
rcl.gospel  # "Mark 13:24-37"
```

`track` selects the Season-after-Pentecost Old Testament reading (Track 1:
semi-continuous narrative; Track 2: thematically paired with the Gospel —
the default). The other track's citations are always available as
`alternate_first_lesson` / `alternate_psalm`, never silently dropped. On
Palm Sunday, the top-level fields carry the Liturgy of the Passion and the
procession Gospel/Psalm are under `rcl.palms`.

`get_rcl_readings()` resolves on Sundays plus the fixed weekday propers (Ash
Wednesday, Maundy Thursday, Good Friday, Holy Saturday, Ascension Day) —
`None` otherwise. `get_full_readings()` returns both lectionaries plus the
shared Collect for any date, leaving `.rcl` as `None` when RCL doesn't apply:

```python
from daily_office_lectionary import get_full_readings

full = get_full_readings("2026-11-29")
full.office  # OfficeReadings
full.rcl  # RCLReadings
full.collect  # shared Collect of the Day
```

## Light vs. full mode

**Light mode** (`get_readings`) needs no extra install, no network access, and
no dependencies beyond the standard library. Scripture lessons come back as
reference strings (e.g. `"Isa 1:1-9"`), psalms as lectionary tokens (e.g.
`"23"`, `"119:1-24"`), and the Collect of the Day is included in full — it's
small, public-domain BCP prayer text.

**Full mode** (`get_readings_with_text`) additionally resolves the actual
scripture verse text, once a Bible database has been downloaded once:

```python
from daily_office_lectionary import fetch_bible, get_readings_with_text

fetch_bible()  # downloads the public-domain KJVA database to a local cache
readings = get_readings_with_text("2026-04-05")
readings.morning_lessons["first"].verses[0].text
```

Or from the command line:

```sh
daily-office-lectionary fetch-bible
daily-office-lectionary readings 2026-04-05 --full --json
daily-office-lectionary rcl 2026-11-29 --track 2 --json
daily-office-lectionary full 2026-11-29 --json
```

`fetch_bible()` downloads the King James Version with Apocrypha (KJVA) — a
public-domain translation — from
[scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases)
into a local cache directory, pinned to a specific known-good commit. It is
never bundled in the package itself, so the base install stays tiny. See
[NOTICE.md](NOTICE.md) for a licensing note on that database's bundled
tagging data (not used by this package).

## Data sources

See [NOTICE.md](NOTICE.md) for full attribution. In short: the Daily Office
lectionary data originated from [reubenlillie/daily-office](https://github.com/reubenlillie/daily-office)
(MIT), substantially reorganized and extended here; BCP 1979 prayer text is
public domain; Bible text is the public-domain KJVA, fetched on demand; RCL
scripture citations were cross-checked against
[Vanderbilt Divinity Library's lectionary database](https://lectionary.library.vanderbilt.edu/).

## Prior art

[`pylect`](https://pypi.org/project/pylect/) covers the 2019 ACNA BCP
lectionary with ESV-API-backed text. This package targets the 1979 BCP
(Episcopal Church) and needs no API key for full-text mode.

## Development

Requires [go-task](https://taskfile.dev/) (`winget install Task.Task`).

```sh
task install   # pip install -e .[dev]
task check     # lint + format check + typecheck + test
task test      # run the test suite
```

Full-mode tests are skipped automatically unless a Bible database is present;
run `task fetch-bible` first to include them.
