"""
build_app.py

Assembles halka-app.html from its parts, and merges the scraper's real output
into the hand-researched candidate records.

WHY THIS IS A BUILD STEP AND NOT A HAND-EDITED FILE
---------------------------------------------------
Three things have to stay in sync and would drift immediately if maintained by
hand: the promise taxonomy (defined in promise_taxonomy.py), the categorised
promise data derived from it, and the candidate records the scraper produces.
Generating the app means the classifier that labels a promise and the UI that
renders the label are the same source of truth.

THE MERGE, AND WHY IT KEEPS BOTH KINDS OF RECORD
------------------------------------------------
Bankipur had three hand-researched candidates with news coverage, background
notes and cited sources. The scraper returns all 23 who actually filed. Neither
is a superset of the other:

  - hand-researched records have context a scraper cannot produce (news links,
    disputed-source flags, asset history)
  - scraped records cover the 20 candidates nobody hand-researched, who are
    still on the ballot and still deserve to be shown

So they are merged on affidavit source URL, hand-researched fields win where
they exist, and scraped-only candidates are marked newsStatus:"not-researched"
— which the UI renders as its own explicit state, distinct from "we checked and
found nothing". Showing 3 of 23 candidates would misrepresent the ballot;
silently dropping the researched detail would lose real work.

Usage: python3 build_app.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from promise_taxonomy import classify_manifesto, export_taxonomy_js

HERE = Path(__file__).parent

MANIFESTOS = {
    "NDA": [
        "1 crore jobs pledged over five years (NDA “Sankalp Patra,” released 31 Oct 2025)",
        "₹10 lakh assistance for Extremely Backward Classes, plus an EBC commission led by a retired Supreme Court judge",
        "10 new industrial parks / factories in every district",
        "1 crore women to become “Lakhpati Didi”; free electricity up to 125 units; 50 lakh new houses",
    ],
    "MGB": [
        "Government job for one member of every family — law promised within 20 days of forming government (“Bihar Ka Tejashwi Pran,” released 28 Oct 2025)",
        "₹2,500/month to women under the Mai-Behin Maan Yojana",
        "Reservation raised to 60%; Old Pension Scheme restored",
        "Liquor prohibition law to be reviewed",
    ],
    "JANSURAAJ": [
        "No formal manifesto released before the 2025 poll — founder Prashant Kishor instead set out a public agenda",
        "Education and employment named as top priority; pension expansion",
        "Soft loans / self-employment support for women; land reforms",
        "Liquor ban to be lifted; public hospitals made functional",
    ],
}

# Which coalition manifesto applies to a party. Only parties whose manifesto
# this project actually located are listed; everything else gets no manifesto
# and the UI says so, rather than inheriting a coalition's pledges it never
# signed up to.
PARTY_TO_MANIFESTO = {
    "BJP": "NDA",
    "JDU": "NDA",
    "RJD": "MGB",
    "INC": "MGB",
    "CPI(ML)(L)": "MGB",
    "Jan Suraaj Party": "JANSURAAJ",
}

# Party colour band, matching the existing legend.
PARTY_TAG = {
    "BJP": "tag-a", "JDU": "tag-a",
    "INC": "tag-b", "RJD": "tag-b", "CPI(ML)(L)": "tag-b",
    "Independent": "tag-ind", "IND": "tag-ind",
}

EDU_LEVELS = [
    ("doctorate", 6), ("ph.d", 6),
    ("post graduate", 5), ("post-graduate", 5), ("masters", 5),
    ("graduate professional", 4), ("graduate", 4),
    ("12th", 3), ("higher secondary", 3), ("intermediate", 3),
    ("10th", 2), ("matric", 2), ("secondary", 2),
    ("8th", 1), ("literate", 1), ("5th", 1),
]


def edu_level(education: str | None) -> int | None:
    """Map MyNeta's education category to a 1-6 level for the comparison pips.

    Returns None when the text doesn't start with a recognised category —
    the UI shows "not recorded" rather than assuming a level. Matching is on
    the leading category token only, since the field also contains free-text
    degree detail that would otherwise produce false hits (a 10th-pass
    candidate whose detail mentions a relative's doctorate, for instance).
    """
    if not education:
        return None
    head = education.strip().lower()[:40]
    for token, level in EDU_LEVELS:
        if token in head:
            return level
    return None


def clean_education(education: str | None) -> str:
    if not education:
        return "Not available in this data pull"
    return re.sub(r"\s+", " ", education).strip()


def load_scraped(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text()).get("candidates", [])


def merge_bankipur(existing_js: str) -> str:
    """Replace the 3-candidate Bankipur array with all 23 real candidates,
    preserving hand-researched detail where it exists."""
    scraped = load_scraped(HERE / "data" / "Bihar2025_252.json")
    if not scraped:
        print("  no scraped Bankipur data found — leaving the existing array alone")
        return existing_js

    # Pull the hand-researched records out of the existing JS by source URL, so
    # their news links and background survive the merge.
    researched: dict[str, str] = {}
    block = re.search(r"const bankipurCandidates = \[(.*?)\n\];", existing_js, re.S)
    if block:
        for obj in re.findall(r"\{\s*\n?\s*id:\d+.*?\n  \}", block.group(1), re.S):
            m = re.search(r'sourceUrl:"([^"]+)"', obj)
            if m:
                researched[m.group(1)] = obj

    print(f"  {len(scraped)} scraped, {len(researched)} hand-researched to preserve")

    out, next_id = [], 300
    for i, c in enumerate(scraped, start=1):
        url = c.get("sourceUrl", "")
        if url in researched:
            # Renumber the preserved record to its position in the real,
            # complete candidate list. Its original sno came from a 3-candidate
            # subset, so keeping it produced duplicate ballot numbers — two
            # different people both shown as "1" on the same ballot, which is
            # exactly the kind of error a voter would act on.
            obj = re.sub(r"\bsno:\s*\d+", f"sno:{i}", researched[url].strip(), count=1)
            out.append(obj)
            continue
        party = c.get("party") or "Unknown"
        crim = c.get("criminalCount")
        rec = {
            "id": next_id, "sno": i, "winner": False,
            "name": (c.get("name") or "").strip(),
            "party": party,
            "tag": PARTY_TAG.get(party, "tag-c"),
            "age": c.get("age"),
            "education": clean_education(c.get("education")),
            "eduLevel": edu_level(c.get("education")),
            "terms": 0,
            "profession": (c.get("profession") or "Not listed in this data pull").strip(),
            "criminalCount": crim,
            "criminalNote": (
                "No pending criminal cases declared in the affidavit."
                if crim == 0 else
                f"{crim} case(s) declared as pending in the affidavit. A declared case is a charge, "
                "not a conviction — see the source link for the full record."
                if crim else
                "Criminal case count could not be read from this affidavit in this pull."
            ),
            "assets": c.get("assets") or "Not available in this data pull",
            "liabilities": c.get("liabilities") or "Not available in this data pull",
            "assetHistory": None,
            "manifestoKey": PARTY_TO_MANIFESTO.get(party),
            "manifestoNote": (
                "Contesting as an independent — no party manifesto."
                if party in ("Independent", "IND")
                else "No published manifesto located for this party in this election."
            ),
            "sourceUrl": url,
            # Genuinely not researched — distinct from "checked, found nothing".
            "newsStatus": "not-researched",
            "background": [], "newsLinks": [],
        }
        next_id += 1
        out.append(json.dumps(rec, ensure_ascii=False, indent=2).replace("\n", "\n  "))

    replacement = "const bankipurCandidates = [\n  " + ",\n  ".join(out) + "\n];"
    # Lambda, not a plain string: the replacement contains JSON \u escapes and
    # re.sub would try to interpret them as regex escapes and fail.
    return re.sub(
        r"const bankipurCandidates = \[.*?\n\];",
        lambda _m: replacement,
        existing_js, flags=re.S,
    )


def refresh_bankipur_note(js: str) -> str:
    """Rewrite the Bankipur blurb, which described a 3-candidate subset and
    became wrong the moment the full 23-candidate list was merged in. A stale
    note claiming "all three candidates shown" above a list of 23 undermines
    the one thing this app sells: that what it says matches what it shows."""
    new_note = (
        '"This election hasn\'t happened yet \\u2014 voting is 30 Jul 2026, results 3 Aug 2026. '
        'All 23 candidates who filed for this seat are shown, each with its own sworn-affidavit source link, '
        'fetched live from ADR/MyNeta on 26 Jul 2026. Three of them were additionally hand-researched for news '
        'coverage and background; the other 20 show affidavit data only, marked as not-yet-researched rather than '
        'as having no coverage. Two candidates\' affidavit names differ from how news coverage identifies them '
        '\\u2014 flagged on their cards rather than silently resolved."'
    )
    return re.sub(
        r'(bankipur: \{ label:"[^"]*", candidates: bankipurCandidates, status:"upcoming", note:)"(?:[^"\\]|\\.)*"',
        lambda m: m.group(1) + new_note,
        js,
    )


def add_manifesto_keys(js: str) -> str:
    """Swap the old `manifesto: NDA_MANIFESTO` references for `manifestoKey`,
    which the UI resolves against the categorised promise data."""
    js = re.sub(r"manifesto:\s*NDA_MANIFESTO", 'manifestoKey:"NDA"', js)
    js = re.sub(r"manifesto:\s*MGB_MANIFESTO", 'manifestoKey:"MGB"', js)
    js = re.sub(r"manifesto:\s*JANSURAAJ_AGENDA", 'manifestoKey:"JANSURAAJ"', js)
    js = re.sub(r"manifesto:\s*\[\]", "manifestoKey:null", js)
    return js


def main():
    print("Building halka-app.html")

    shell = (HERE / "_ui_shell.html").read_text()
    symbols = (HERE / "party_symbols.js").read_text()
    ui = (HERE / "_ui_code.js").read_text()
    data = (HERE / "_candidate_data.js").read_text()

    print("Merging real scraped Bankipur data…")
    data = merge_bankipur(data)
    data = refresh_bankipur_note(data)
    data = add_manifesto_keys(data)

    notes = (
        'const NOT_RESEARCHED_NOTE = "News research hasn\'t been run for this candidate yet. '
        'This is different from having checked and found nothing — at full scale this step has to run '
        'for every candidate in every constituency.";\n'
        'const NO_COVERAGE_NOTE = "Searched, and no independent news coverage turned up for this candidate '
        'beyond the ECI affidavit record — typical for down-ballot candidates.";\n'
    )

    promises = classify_manifesto  # referenced for clarity
    categorized = {k: promises(v) for k, v in MANIFESTOS.items()}
    promise_js = (
        export_taxonomy_js() + "\n\n"
        + "const CATEGORIZED_PROMISES = "
        + json.dumps(categorized, indent=2, ensure_ascii=False) + ";\n"
    )

    html = (shell
            .replace("/*__PARTY_SYMBOLS__*/", symbols)
            .replace("/*__PROMISE_DATA__*/", promise_js)
            .replace("/*__CANDIDATE_DATA__*/", notes + "\n" + data)
            .replace("/*__UI_CODE__*/", ui))

    out = HERE / "halka-app.html"
    out.write_text(html)

    total = sum(len(v) for v in categorized.values())
    flagged = sum(1 for v in categorized.values() for p in v if p["needsReview"])
    print(f"Wrote {out.name} ({len(html):,} bytes)")
    print(f"  {total} categorised pledges across {len(categorized)} manifestos, {flagged} flagged for review")


if __name__ == "__main__":
    main()
