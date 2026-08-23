# daily-office-lectionary

BCP 1979 Daily Office readings for any date — psalms, scripture lessons, and
the Collect of the Day. Pure Python, no required dependencies.

```python
from daily_office_lectionary import get_readings

readings = get_readings("2026-04-05")
readings.week  # "Easter Week"
readings.psalms["morning"]  # ["148", "149", "150"]
readings.morning_lessons  # {"first": "Exod 12:1-14", "second": "John 1:1-18"}
readings.collect.contemporary
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
```

`fetch_bible()` downloads the King James Version with Apocrypha (KJVA) — a
public-domain translation — from
[scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases)
into a local cache directory, pinned to a specific known-good commit. It is
never bundled in the package itself, so the base install stays tiny. See
[NOTICE.md](NOTICE.md) for a licensing note on that database's bundled
tagging data (not used by this package).

## Data sources

See [NOTICE.md](NOTICE.md) for full attribution. In short: the lectionary
data originated from [reubenlillie/daily-office](https://github.com/reubenlillie/daily-office)
(MIT), substantially reorganized and extended here; BCP 1979 prayer text is
public domain; Bible text is the public-domain KJVA, fetched on demand.

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
