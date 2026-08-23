# Third-Party Notices

This project's own code is MIT licensed — see [LICENSE](LICENSE). This file
documents the provenance of the bundled and downloaded data.

## Daily Office Lectionary data (`src/daily_office_lectionary/data/readings/`)

The Year One / Year Two daily lectionary, holy days, and special occasions
JSON originated from **[reubenlillie/daily-office](https://github.com/reubenlillie/daily-office)**,
which is MIT licensed:

```
MIT License

Copyright (c) 2018 Reuben L. Lillie

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

This project's data has been substantially reorganized, normalized (SBL book
abbreviation fixes, corrected ambiguous references, consistent schema), and
extended (BCP 1979 Collects added and cross-referenced) beyond the original
dataset. The calendar/lectionary *code* in this package (Easter computation,
liturgical season logic, precedence resolution) is original work, independent
of Reuben Lillie's own [daily-office-lectionary](https://github.com/reubenlillie/daily-office)
JavaScript library.

## BCP 1979 Collects, Psalm and lesson assignments (prayer-book text)

The Collect of the Day text (`data/collects/`) is drawn from the 1979 Book of
Common Prayer, cross-checked against [bcponline.org](https://www.bcponline.org/).
The Book of Common Prayer has never been under copyright — the Episcopal
Church first ratified it in 1789 and last certified this edition in 2007 — so
no attribution is legally required for this text, but its liturgical source is
documented here for transparency.

## Revised Common Lectionary data (`src/daily_office_lectionary/data/rcl/`)

The Revised Common Lectionary (RCL) is published by the
[Consultation on Common Texts](https://commontexts.org/). Its scripture
citations — a list of book/chapter/verse references, not original prose —
are reference data rather than separately copyrightable text, the same
reasoning already applied above to the BCP psalm and lesson tables. The
citations bundled here were cross-checked against
[Vanderbilt Divinity Library's lectionary database](https://lectionary.library.vanderbilt.edu/),
whose own tooling/presentation is a separate work from the RCL citations
themselves; this package reproduces only the citations, not Vanderbilt's
site content.

## Bible verse text (full mode only, downloaded on demand)

Full mode resolves scripture verse text from the **King James Version with
Apocrypha (KJVA, 1769)** — the base translation is public domain — via a
SQLite database downloaded on first use from
**[scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases)**
(the repository's own tooling/code is MIT licensed). That database's
`translations` table self-reports its license as **GPL**, which appears to
refer to the bundled Strong's-number and morphology tagging rather than the
KJV text itself; this package does not use or expose that tagging data, only
the plain verse text. This data is never bundled in the package itself — it
is downloaded directly by the end user via `fetch_bible()`
(`daily_office_lectionary.bible.fetch`), pinned to a specific verified-good
commit rather than the mutable `master` branch (whose tip has, at times,
served a `KJVA.db` build with every verse row duplicated several times over).

## Prior art

[`pylect`](https://pypi.org/project/pylect/) (MIT) is a related PyPI package
covering the 2019 ACNA Book of Common Prayer lectionary, with Scripture text
fetched via the ESV API. This package targets the 1979 BCP (Episcopal Church)
instead and needs no external API key for its optional full-text mode.
