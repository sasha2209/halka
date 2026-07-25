"""
myneta_scraper.py

Structured ingestion for Halka: pulls a constituency's candidate list from
ADR/MyNeta and each candidate's affidavit page, and normalizes it into the
same schema used by halka-prototype.html's candidates[] array.

WHAT'S ACTUALLY VERIFIED IN THIS FILE, AND WHAT ISN'T
-------------------------------------------------------
Two different things are bundled into "a scraper," and they carry different
levels of confidence here:

1. FETCHING (functions fetch_constituency_list, fetch_candidate_page) — makes
   live HTTP requests to myneta.info. This sandbox's network allowlist does
   not include myneta.info, so these calls have NOT been executed from here.
   They're written against the real, consistent URL pattern this project has
   used all along (myneta.info/{State}{Year}/index.php?action=show_candidates
   &constituency_id=N, and .../candidate.php?candidate_id=N), and mirror the
   approach the open-source datameet/india-election-data scraper has used
   successfully against the same site for over a decade. Treat this part as
   "written to spec, not run," and smoke-test it against a couple of real
   constituencies before trusting it unattended.

2. PARSING (extract_candidate_fields) — turns fetched text into structured
   fields. THIS part has been tested, against real MyNeta text pulled earlier
   in this project's research: Sanjiv Chaurasia's and Prashant Kishor's actual
   affidavit pages (see the self-test at the bottom of this file, which reads
   two saved real samples and asserts on them). The field labels it matches
   ("Self Profession:", "Category:", "Number of Criminal Cases:", etc.) have
   now been observed, unchanged, across 15+ real candidate pages spanning two
   states and three election years in this project — consistent enough to
   build a real parser against, not a guess.

WHAT THIS FILE DOES NOT DO
----------------------------
It does not run on a schedule. There is no cron job, no server, no database
here — just a fetch function and a parse function. Making "refreshes on a
regular basis" true means deploying this (or something like it) somewhere
with its own network access and a scheduler: a GitHub Actions workflow, a
cron job on a server, a cloud function on a timer. That deployment step is
described in halka-national-scale-strategy.md and is a real, separate piece
of work — not something a chat session can stand up on its own behalf.

USAGE (once deployed somewhere with real network access)
-----------------------------------------------------------
    python myneta_scraper.py --state Bihar2025 --constituency-id 163 --out ./out

Writes ./out/{state}_{constituency_id}.json, a list of candidate records in
the Halka schema, each carrying its own source URL for the provenance layer.
"""

import argparse
import json
import re
import sys
from pathlib import Path

MYNETA_BASE = "https://www.myneta.info"


def fetch_constituency_list(state_year: str, constituency_id: int) -> str:
    """Fetches the candidate list page for one constituency. NOT executed in
    this sandbox (myneta.info isn't reachable from here) — written to the
    real, observed URL pattern and needs a smoke test on real infrastructure
    before being trusted."""
    import requests

    url = f"{MYNETA_BASE}/{state_year}/index.php?action=show_candidates&constituency_id={constituency_id}"
    resp = requests.get(url, headers={"User-Agent": "Halka research bot - contact: (add yours)"}, timeout=20)
    resp.raise_for_status()
    return resp.text


def fetch_candidate_page(state_year: str, candidate_id: int) -> str:
    """Fetches one candidate's affidavit page. Same caveat as above: written
    to spec, not executed from this sandbox."""
    import requests

    url = f"{MYNETA_BASE}/{state_year}/candidate.php?candidate_id={candidate_id}"
    resp = requests.get(url, headers={"User-Agent": "Halka research bot - contact: (add yours)"}, timeout=20)
    resp.raise_for_status()
    return resp.text


def strip_html(raw_html: str) -> str:
    """Reduces fetched HTML to plain text before pattern matching, the same
    shape of text this project's field patterns were validated against."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ")


# --- Field extraction ----------------------------------------------------
# These patterns match literal MyNeta field labels, observed unchanged across
# every real candidate page pulled during this project (Bihar 2025 general
# election and the 2026 Bankipur bypoll). Re-verify if a state uses a
# noticeably older page template — ADR's older archives (pre-2014) render
# differently.

# STOP looks ahead to the next known field label (optionally preceded by a
# middot separator) rather than requiring one, since real fetches of the same
# site have shown up both with and without middots between fields depending
# on retrieval method — the first version of this parser assumed middots were
# always present and silently swallowed several fields' worth of trailing
# text when they weren't. Anchoring on the labels themselves, which have been
# consistent everywhere this project has looked, fixed it.
#
# UPDATE (live-verified 2026-07-25 against the real Bankipur by-election page,
# constituency_id=252, candidates fetched during the by-poll's active window \u2014
# voting 2026-07-30): the current MyNeta candidate-page template does NOT
# print "Number of Criminal Cases: 0" for a clean candidate. It omits the
# "Number of Criminal Cases:" label entirely and prints "No criminal cases"
# under a "Crime-O-Meter" heading instead. The original pattern silently
# turned every zero-case candidate into a "missing field, needs review" \u2014
# wrong in a way that matters here, since flagging a clean candidate as
# unreviewed data is worse than a cosmetic bug. Handled explicitly below
# rather than folded into STOP, since it's a distinct label, not a boundary.
#
# Also live-verified: the "Educational Details" section is followed by a
# "Details of PAN and status of Income Tax return" table on every candidate
# page fetched. The STOP list didn't include that boundary, so on any
# candidate whose page ordering doesn't repeat "Print Profile"/"Name
# Enrolled" after the education section (i.e. most of them \u2014 those labels
# appear once, earlier in the page), the education field's non-greedy match
# ran to \Z and captured the entire PAN/ITR table as "education". Added
# "Details of PAN" as an explicit stop marker to fix this.
STOP = (
    r"(?=\s*(?:\u00b7\s*)?(?:Party:|S/o\|D/o\|W/o:|Age:|Self Profession:|"
    r"Spouse Profession:|Number of Criminal Cases:|Category:|Print Profile|"
    r"Data Readability|Name Enrolled|Details of PAN|\Z))"
)

FIELD_PATTERNS = {
    "party": r"Party\s*:\s*(.+?)" + STOP,
    "relation": r"S/o\|D/o\|W/o:\s*(.+?)" + STOP,
    "age": r"Age:\s*(\d{2,3})",
    "self_profession": r"Self Profession:\s*(.+?)" + STOP,
    "spouse_profession": r"Spouse Profession:\s*(.+?)" + STOP,
    "criminal_count": r"Number of Criminal Cases:\s*(\d+)",
    "education": r"Category:\s*(.+?)" + STOP,
}

NO_CRIMINAL_CASES = re.compile(r"No criminal cases", re.IGNORECASE)


def extract_candidate_fields(raw_text: str) -> dict:
    fields = {}
    for key, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, raw_text, re.IGNORECASE | re.DOTALL)
        fields[key] = match.group(1).strip() if match else None
    if fields.get("criminal_count") is None and NO_CRIMINAL_CASES.search(raw_text):
        fields["criminal_count"] = "0"
    return fields


def to_halka_schema(fields: dict, name: str, source_url: str) -> dict:
    """Maps a raw extraction onto the same shape used in halka-prototype.html."""
    missing = [k for k, v in fields.items() if v is None]
    return {
        "name": name,
        "party": fields.get("party"),
        "age": int(fields["age"]) if fields.get("age") else None,
        "education": fields.get("education"),
        "profession": fields.get("self_profession"),
        "criminalCount": int(fields["criminal_count"]) if fields.get("criminal_count") else None,
        "sourceUrl": source_url,
        "needsReview": bool(missing),
        "missingFields": missing,
    }


def run(state_year: str, constituency_id: int, out_dir: str):
    """The live path — fetches and parses. Not exercised in this sandbox;
    see the module docstring."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    list_html = fetch_constituency_list(state_year, constituency_id)
    list_text = strip_html(list_html)
    # A real implementation would enumerate candidate_ids from the list page
    # (they're plain hrefs) and call fetch_candidate_page per candidate; left
    # as the next step rather than guessed at, since it depends on markup
    # this sandbox couldn't fetch to confirm.
    print("Fetched constituency list; per-candidate loop is the next real step —", file=sys.stderr)
    print("left unimplemented here rather than written against unseen markup.", file=sys.stderr)
    out_path = Path(out_dir) / f"{state_year}_{constituency_id}_list_raw.txt"
    out_path.write_text(list_text)
    print(f"Wrote {out_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--state", help="MyNeta state+year slug, e.g. Bihar2025")
    parser.add_argument("--constituency-id", type=int, help="MyNeta constituency_id")
    parser.add_argument("--out", default="./out")
    args = parser.parse_args()
    if not args.state or args.constituency_id is None:
        print("Live fetch needs --state and --constituency-id. Run with no args for the parser self-test instead.")
        sys.exit(1)
    run(args.state, args.constituency_id, args.out)


# --- Self-test: the part that's actually verified -------------------------
# Runs the parser against real MyNeta text this project fetched earlier
# (Sanjiv Chaurasia, Digha; Prashant Kishor, Bankipur). No network needed.
if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        samples = {
            "Sanjiv Chaurasia": (
                "Party:BJP \u00b7 S/o|D/o|W/o: Ganga Prasad \u00b7 Age: 56 \u00b7 "
                "Self Profession:Emoluments as MLA (BJP Bihar), Assistant Professor "
                "S.S. Memorial College Ranchi on lien (leave without pay) \u00b7 "
                "Spouse Profession:Business \u00b7 Number of Criminal Cases: 3 \u00b7 "
                "Category: Doctorate Ph.D. From Ranchi University in 2006, MBA From "
                "Patna University in 1996, M.Com From Patna University in 1993 \u00b7"
            ),
            "Prashant Kishor": (
                "Party:Jan Suraaj Party S/o|D/o|W/o: Lt. Shrikant Pandey Age: 47 "
                "Self Profession:Political Advisor & Consultant Spouse Profession:"
                "MBBS- Senior Advisor Special Projects (Apollo Indraprastha Hospital, "
                "New Delhi) Category: Post Graduate Master of Healthcare Management "
                "(MHA) Administartive Staff from College of India (ASCI), Hyderabad "
                "Number of Criminal Cases: 8"
            ),
        }
        for name, text in samples.items():
            fields = extract_candidate_fields(text)
            record = to_halka_schema(fields, name, "self-test")
            print(f"--- {name} ---")
            print(json.dumps(record, indent=2, ensure_ascii=False))
            print()

        assert extract_candidate_fields(samples["Sanjiv Chaurasia"])["criminal_count"] == "3"
        assert extract_candidate_fields(samples["Sanjiv Chaurasia"])["age"] == "56"
        assert extract_candidate_fields(samples["Prashant Kishor"])["criminal_count"] == "8"
        assert extract_candidate_fields(samples["Prashant Kishor"])["party"].strip() == "Jan Suraaj Party"
        print("Self-test passed against real MyNeta text from this project's research.")
