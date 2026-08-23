"""
Convert Vanderbilt Divinity Library's RCL scripture-citation exports
(plain-text, one per liturgical year -- see scripts/rcl_sources/) into
src/daily_office_lectionary/data/rcl/*.json.

Source files came from https://lectionary.library.vanderbilt.edu/
(?season=all&download=txt for each liturgical year). Re-run this whenever
new years' source files are added to scripts/rcl_sources/, then review the
generated JSON diff before committing.
"""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCES = Path(__file__).resolve().parent / "rcl_sources"
DATA_DIR = REPO / "src" / "daily_office_lectionary" / "data" / "rcl"

FULL_TO_ABBR = {
    "Genesis": "Gen",
    "Exodus": "Exod",
    "Leviticus": "Lev",
    "Numbers": "Num",
    "Deuteronomy": "Deut",
    "Joshua": "Josh",
    "Judges": "Judg",
    "Ruth": "Ruth",
    "1 Samuel": "1 Sam",
    "2 Samuel": "2 Sam",
    "1 Kings": "1 Kgs",
    "2 Kings": "2 Kgs",
    "1 Chronicles": "1 Chr",
    "2 Chronicles": "2 Chr",
    "Ezra": "Ezra",
    "Nehemiah": "Neh",
    "Esther": "Esth",
    "Job": "Job",
    "Proverbs": "Prov",
    "Ecclesiastes": "Eccl",
    "Song of Solomon": "Song",
    "Isaiah": "Isa",
    "Jeremiah": "Jer",
    "Lamentations": "Lam",
    "Ezekiel": "Ezek",
    "Daniel": "Dan",
    "Hosea": "Hos",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obadiah": "Obad",
    "Jonah": "Jonah",
    "Micah": "Mic",
    "Nahum": "Nah",
    "Habakkuk": "Hab",
    "Zephaniah": "Zeph",
    "Haggai": "Hag",
    "Zechariah": "Zech",
    "Malachi": "Mal",
    "Wisdom of Solomon": "Wis",
    "Sirach": "Sir",
    "Baruch": "Bar",
    "Matthew": "Matt",
    "Mark": "Mark",
    "Luke": "Luke",
    "John": "John",
    "Acts": "Acts",
    "Romans": "Rom",
    "1 Corinthians": "1 Cor",
    "2 Corinthians": "2 Cor",
    "Galatians": "Gal",
    "Ephesians": "Eph",
    "Philippians": "Phil",
    "Colossians": "Col",
    "1 Thessalonians": "1 Thess",
    "2 Thessalonians": "2 Thess",
    "1 Timothy": "1 Tim",
    "2 Timothy": "2 Tim",
    "Titus": "Titus",
    "Philemon": "Phlm",
    "Hebrews": "Heb",
    "James": "Jas",
    "1 Peter": "1 Pet",
    "2 Peter": "2 Pet",
    "1 John": "1 John",
    "2 John": "2 John",
    "3 John": "3 John",
    "Jude": "Jude",
    "Revelation": "Rev",
}

_BOOK_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(n) for n in sorted(FULL_TO_ABBR, key=len, reverse=True)) + r")\b"
)


def _replace_books(text: str) -> str:
    return _BOOK_PATTERN.sub(lambda m: FULL_TO_ABBR[m.group(1)], text)


def normalize_ref(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("*"):
        raw = raw[1:].strip()
    raw = raw.replace("&#8211;", "–").replace("&#8217;", "’")
    raw = _replace_books(raw)
    return raw.strip()


def normalize_psalm(raw: str) -> str:
    raw = normalize_ref(raw)
    raw = re.sub(r"^Psalm\s+", "", raw)
    return raw.strip()


# A few Propers use a canticle (not the Psalter) as the psalm-substitute, so
# the source line has no literal "Psalm" token to split on -- e.g. "1 Samuel
# 1:4-20 1 Samuel 2:1-10" (the Song of Hannah as the response). Handled as
# explicit overrides keyed on the exact raw source text, in the same spirit
# as lectionary/normalizer.py's KNOWN_OVERRIDES for malformed references.
_CANTICLE_SPLIT_OVERRIDES: dict[str, tuple[str, str]] = {
    "1 Samuel 1:4-20 1 Samuel 2:1-10": ("1 Samuel 1:4-20", "1 Samuel 2:1-10"),
    "Isaiah 65:17-25 Isaiah 12": ("Isaiah 65:17-25", "Isaiah 12"),
    "Jeremiah 23:1-6 Luke 1:68-79": ("Jeremiah 23:1-6", "Luke 1:68-79"),
}


def split_first_and_psalm(raw: str) -> tuple[str, str]:
    """Split a Vanderbilt 'First* reading and Psalm' combined line."""
    raw = raw.strip()
    if not raw:
        return "", ""
    if raw in _CANTICLE_SPLIT_OVERRIDES:
        first_part, psalm_part = _CANTICLE_SPLIT_OVERRIDES[raw]
        return normalize_ref(first_part), normalize_ref(psalm_part)
    parts = re.split(r"\bPsalm\b", raw, maxsplit=1)
    if len(parts) == 1:
        raise ValueError(f"Could not split first-reading/psalm from: {raw!r}")
    first_part, psalm_part = parts
    return normalize_ref(first_part), normalize_psalm(psalm_part)


def parse_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    records = []
    for block in blocks:
        lines = block.splitlines()
        if not lines[0].startswith("Liturgical Date:"):
            continue
        rec: dict = {"name": lines[0].split(":", 1)[1].strip()}
        cal_line = next((line for line in lines if line.startswith("Calendar Date:")), None)
        rec["date"] = cal_line.split(":", 1)[1].strip() if cal_line else None

        joined = "\n".join(lines)

        # Easter Vigil: one giant quoted line, extract NT epistle/psalm/gospel only.
        if "Easter Vigil" in joined and "Old Testament Readings" in joined:
            m_gospel = re.search(r'Gospel - ([^"]+?)"', joined)
            rec["vigil_gospel"] = normalize_ref(m_gospel.group(1)) if m_gospel else None
            rec["vigil_second"] = "Rom 6:3-11"
            rec["vigil_psalm"] = "114"
            records.append(rec)
            continue

        for line in lines:
            if line.startswith("First* reading and Psalm:"):
                first, psalm = split_first_and_psalm(line.split(":", 1)[1])
                rec["track1_first"], rec["track1_psalm"] = first, psalm
            elif line.startswith("Alternate* First reading and Psalm:"):
                first, psalm = split_first_and_psalm(line.split(":", 1)[1])
                rec["track2_first"], rec["track2_psalm"] = first, psalm
            elif line.startswith("First reading:"):
                rec["first"] = normalize_ref(line.split(":", 1)[1])
            elif line.startswith("Psalm:"):
                rec["psalm"] = normalize_psalm(line.split(":", 1)[1])
            elif line.startswith("Second reading:"):
                rec["second"] = normalize_ref(line.split(":", 1)[1])
            elif line.startswith("Gospel:"):
                rec["gospel"] = normalize_ref(line.split(":", 1)[1])
        records.append(rec)
    return records


# Vanderbilt "Liturgical Date" name -> our week key. None = skip entirely.
NAME_TO_WEEK = {
    "First Sunday of Advent": "First Sunday of Advent",
    "Second Sunday of Advent": "Second Sunday of Advent",
    "Third Sunday of Advent": "Third Sunday of Advent",
    "Fourth Sunday of Advent": "Fourth Sunday of Advent",
    "Holy Name of Jesus": "Holy Name of Jesus",
    "New Year's Day": None,  # civil-calendar alternate to Holy Name; not resolvable
    "Second Sunday after Christmas Day": "Second Sunday after Christmas Day",
    "Nativity of the Lord - Proper I": "Christmas Eve",
    "Nativity of the Lord - Proper II": None,  # dawn service; not resolvable (see Proper III)
    "Nativity of the Lord - Proper III": "Christmas Day",
    "First Sunday after Christmas Day": "First Sunday after Christmas Day",
    "Epiphany of the Lord": "Epiphany of the Lord",
    "Baptism of the Lord": "Baptism of the Lord",
    "Second Sunday after the Epiphany": "Second Sunday after the Epiphany",
    "Third Sunday after the Epiphany": "Third Sunday after the Epiphany",
    "Fourth Sunday after the Epiphany": "Fourth Sunday after the Epiphany",
    "Fifth Sunday after the Epiphany": "Fifth Sunday after the Epiphany",
    "Sixth Sunday after the Epiphany": "Sixth Sunday after the Epiphany",
    "Seventh Sunday after the Epiphany": "Seventh Sunday after the Epiphany",
    "Presentation of the Lord": "Presentation of the Lord",
    "Transfiguration Sunday": "Transfiguration Sunday",
    "Ash Wednesday": "Ash Wednesday",
    "First Sunday in Lent": "First Sunday in Lent",
    "Second Sunday in Lent": "Second Sunday in Lent",
    "Third Sunday in Lent": "Third Sunday in Lent",
    "Fourth Sunday in Lent": "Fourth Sunday in Lent",
    "Fifth Sunday in Lent": "Fifth Sunday in Lent",
    "Annunciation of the Lord": "Annunciation of the Lord",
    "Monday of Holy Week": "Monday of Holy Week",
    "Tuesday of Holy Week": "Tuesday of Holy Week",
    "Wednesday of Holy Week": "Wednesday of Holy Week",
    "Maundy Thursday": "Maundy Thursday",
    "Good Friday": "Good Friday",
    "Holy Saturday": "Holy Saturday",
    "Resurrection of the Lord": "Easter Day",
    "Easter Evening": None,  # attached to Easter Day's entry separately
    "Second Sunday of Easter": "Second Sunday of Easter",
    "Third Sunday of Easter": "Third Sunday of Easter",
    "Fourth Sunday of Easter": "Fourth Sunday of Easter",
    "Fifth Sunday of Easter": "Fifth Sunday of Easter",
    "Sixth Sunday of Easter": "Sixth Sunday of Easter",
    "Ascension of the Lord": "Ascension Day",
    "Seventh Sunday of Easter": "Seventh Sunday of Easter",
    "Day of Pentecost": "Day of Pentecost",
    "Visitation of Mary to Elizabeth": "Visitation of Mary to Elizabeth",
    "Trinity Sunday": "Trinity Sunday",
    "Holy Cross": "Holy Cross",
    "Canadian Thanksgiving Day": "Canadian Thanksgiving Day",
    "All Saints Day": "All Saints Day",
    "Thanksgiving Day": "Thanksgiving Day",
}

# Fixed days whose readings are identical every RCL year -- these go in the
# shared fixed_days.json. Everything else (including Holy Saturday, whose
# embedded Vigil Gospel varies by year, and All Saints/Thanksgiving/Canadian
# Thanksgiving, whose readings follow their own 3-year cycle) is written to
# the per-year files instead.
FIXED_WEEK_NAMES = {
    "Ash Wednesday",
    "Monday of Holy Week",
    "Tuesday of Holy Week",
    "Wednesday of Holy Week",
    "Maundy Thursday",
    "Good Friday",
    "Ascension Day",
    "Christmas Eve",
    "Christmas Day",
    "Holy Name of Jesus",
    "Epiphany of the Lord",
    "Presentation of the Lord",
    "Annunciation of the Lord",
    "Visitation of Mary to Elizabeth",
    "Holy Cross",
}


def build_year(records: list[dict]) -> list[dict]:
    by_week: dict[str, dict] = {}
    palms_by_date: dict[str, dict] = {}
    passion_by_date: dict[str, dict] = {}
    vigil_rec: dict | None = None

    for rec in records:
        name = rec["name"]
        if name.startswith("Proper "):
            m = re.match(r"Proper (\d+) \((\d+)\)", name)
            week = f"Proper {m.group(1)}"
            title = name
        elif name.startswith("Reign of Christ"):
            m = re.match(r"Reign of Christ - Proper (\d+) \((\d+)\)", name)
            week = f"Proper {m.group(1)}"
            title = "Reign of Christ"
        elif name == "Liturgy of the Palms":
            palms_by_date[rec["date"]] = rec
            continue
        elif name == "Liturgy of the Passion":
            passion_by_date[rec["date"]] = rec
            continue
        elif name == "Easter Vigil":
            vigil_rec = rec
            continue
        else:
            week = NAME_TO_WEEK.get(name, "__UNKNOWN__")
            if week is None:
                continue
            if week == "__UNKNOWN__":
                raise ValueError(f"Unmapped liturgical date: {name!r}")
            title = name

        entry: dict = {"week": week, "title": title, "lessons": {}}

        # "First*/Alternate* First reading and Psalm" is the source's label
        # for genuine two-track Propers, but it's also used (with an empty
        # Alternate line) for several fixed/named days that don't actually
        # have a second track (Trinity Sunday, Visitation, All Saints, the
        # Thanksgivings) -- those collapse to a flat reading.
        has_real_alternate = bool(rec.get("track2_first", "").strip())
        if "track1_first" in rec and has_real_alternate:
            entry["lessons"]["track1"] = {
                "first": rec["track1_first"],
                "psalm": rec["track1_psalm"],
            }
            entry["lessons"]["track2"] = {
                "first": rec["track2_first"],
                "psalm": rec["track2_psalm"],
            }
            entry["lessons"]["second"] = rec.get("second", "")
            entry["lessons"]["gospel"] = rec.get("gospel", "")
        elif "track1_first" in rec:
            entry["lessons"]["first"] = rec["track1_first"]
            entry["lessons"]["psalm"] = rec["track1_psalm"]
            entry["lessons"]["second"] = rec.get("second", "")
            entry["lessons"]["gospel"] = rec.get("gospel", "")
        else:
            entry["lessons"]["first"] = rec.get("first", "")
            entry["lessons"]["psalm"] = rec.get("psalm", "")
            entry["lessons"]["second"] = rec.get("second", "")
            entry["lessons"]["gospel"] = rec.get("gospel", "")

        if week in by_week:
            raise ValueError(f"Duplicate week key: {week!r} ({name!r})")
        by_week[week] = entry

    # Merge Palm Sunday: palms + passion by matching Calendar Date.
    for d, palms_rec in palms_by_date.items():
        passion_rec = passion_by_date.get(d)
        if passion_rec is None:
            raise ValueError(f"Liturgy of the Palms on {d} has no matching Passion record")
        # Year A's source export has the Palms Gospel citation under
        # "Second reading" instead of "Gospel" (a data quirk not present
        # in Years B/C) -- fall back to "second" when "gospel" is blank.
        palms_gospel = palms_rec.get("gospel") or palms_rec.get("second", "")
        by_week["Palm Sunday"] = {
            "week": "Palm Sunday",
            "title": "Palm Sunday",
            "lessons": {
                "palms": {"gospel": palms_gospel, "psalm": palms_rec.get("psalm", "")},
                "passion": {
                    "first": passion_rec.get("first", ""),
                    "psalm": passion_rec.get("psalm", ""),
                    "second": passion_rec.get("second", ""),
                    "gospel": passion_rec.get("gospel", ""),
                },
            },
        }

    # Attach the Easter Vigil onto Holy Saturday's entry as a sub-field.
    if vigil_rec and "Holy Saturday" in by_week:
        by_week["Holy Saturday"]["lessons"]["vigil"] = {
            "second": vigil_rec.get("vigil_second"),
            "psalm": vigil_rec.get("vigil_psalm"),
            "gospel": vigil_rec.get("vigil_gospel"),
        }

    return list(by_week.values())


def attach_easter_evening(entries: list[dict], records: list[dict]) -> None:
    evening_rec = next((r for r in records if r["name"] == "Easter Evening"), None)
    if evening_rec is None:
        return
    for e in entries:
        if e["week"] == "Easter Day":
            e["lessons"]["evening"] = {
                "first": evening_rec.get("first", ""),
                "psalm": evening_rec.get("psalm", ""),
                "second": evening_rec.get("second", ""),
                "gospel": evening_rec.get("gospel", ""),
            }
            return


def split_sunday_and_fixed(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    per_year = [e for e in entries if e["week"] not in FIXED_WEEK_NAMES]
    fixed = [e for e in entries if e["week"] in FIXED_WEEK_NAMES]
    return per_year, fixed


def validate(out_paths: list[Path]) -> None:
    """Flag any empty-string citation values across the generated files."""
    print("\n--- validation: empty-string values found ---")
    found_any = False
    for out_path in out_paths:
        data = json.loads(out_path.read_text(encoding="utf-8"))

        def walk(prefix: str, obj, out_path: Path = out_path) -> None:
            nonlocal found_any
            if isinstance(obj, dict):
                for k, v in obj.items():
                    walk(f"{prefix}.{k}", v, out_path)
            elif obj == "":
                found_any = True
                print(f"{out_path.name}: {prefix} is empty")

        for entry in data:
            walk(entry["week"], entry.get("lessons", {}))
    if not found_any:
        print("(none)")


def main() -> None:
    files = {"A": SOURCES / "year_a.txt", "B": SOURCES / "year_b.txt", "C": SOURCES / "year_c.txt"}
    all_fixed: dict[str, dict] = {}
    out_paths = []
    for year_letter, path in files.items():
        records = parse_file(path)
        entries = build_year(records)
        attach_easter_evening(entries, records)
        per_year, fixed = split_sunday_and_fixed(entries)
        per_year.sort(key=lambda e: e["week"])
        out_path = DATA_DIR / f"year_{year_letter.lower()}.json"
        out_path.write_text(
            json.dumps(per_year, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        out_paths.append(out_path)
        print(f"Year {year_letter}: {len(per_year)} entries, {len(fixed)} fixed-day entries")
        for f in fixed:
            all_fixed[f["week"]] = f  # identical across years -- last write wins

    fixed_path = DATA_DIR / "fixed_days.json"
    fixed_list = sorted(all_fixed.values(), key=lambda e: e["week"])
    fixed_path.write_text(
        json.dumps(fixed_list, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    out_paths.append(fixed_path)
    print(f"fixed_days.json: {len(fixed_list)} entries")

    validate(out_paths)


if __name__ == "__main__":
    main()
