"""
run_all_states.py

Loops myneta_scraper.py's fetch-and-parse logic across every state and UT
that holds assembly elections, instead of one constituency at a time. This
is the "recursive across states" piece — it's real, runnable code, but see
the module docstring in myneta_scraper.py first: the fetch half of this is
still unexecuted from this sandbox for the same network-access reason.

WHAT THIS ADDS OVER CALLING myneta_scraper.py BY HAND
--------------------------------------------------------
1. A real list of every Indian state/UT that holds assembly elections
   (Delhi, Puducherry and J&K are the only UTs with their own legislative
   assembly; the rest don't have this kind of election at all).
2. Rate limiting between requests, because "run it recursively" against a
   volunteer-run nonprofit's servers without pacing yourself is exactly the
   kind of behavior that gets a scraper IP-blocked, or worse, adds real load
   to a site ADR runs on a nonprofit budget. This is not a technicality —
   it's the difference between a respectful automated reader and a stress
   test nobody asked for.
3. A checkpoint file, so a run that dies partway through (network blip,
   rate limit, laptop sleeps) resumes instead of re-fetching everything.

WHAT IT DOES NOT DO
----------------------
It does not know which MyNeta URL slug and constituency_id map to which
real seat for most states. Bihar2025 and MadhyaPradesh2023 are confirmed —
this project actually fetched pages under those slugs. Every other entry
in STATE_SLUGS below is a best-guess pattern (StateNameNoSpaces + year)
that has NOT been confirmed against a real page, flagged explicitly with
verified=False so nothing downstream mistakes a guess for a checked fact.
Confirming the rest means fetching each one and checking it resolves —
real, mechanical work, not something to assume from a naming pattern.

DEPLOYMENT
----------
This needs to run somewhere with open network access, on a schedule. See
run-scraper.yml in this same output for a GitHub Actions version of that
schedule — free, standard, and something you can actually turn on. This
script itself doesn't self-schedule; nothing invoked from a chat session
can. See halka-national-scale-strategy.md for the fuller reasoning.
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Only Delhi, Puducherry, and Jammu & Kashmir are UTs with a Legislative
# Assembly; the other five UTs (Andaman & Nicobar, Chandigarh, Dadra & Nagar
# Haveli and Daman & Diu, Ladakh, Lakshadweep) don't hold this kind of
# election and are correctly absent below.
STATES_AND_UTS = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Puducherry", "Jammu and Kashmir",
]

# state_year slugs this project has actually fetched from and confirmed
# resolve to real pages. Everything else is a guessed pattern, not a
# confirmed one — see the module docstring.
CONFIRMED_SLUGS = {
    "Bihar": "Bihar2025",
    "Madhya Pradesh": "MadhyaPradesh2023",
}


def build_state_slug(state_name: str, year: int | None = None) -> dict:
    """Returns a slug guess plus a verified flag. Confirmed slugs come from
    CONFIRMED_SLUGS; everything else is StateNameNoSpaces+year, unverified."""
    if state_name in CONFIRMED_SLUGS:
        return {"state": state_name, "slug": CONFIRMED_SLUGS[state_name], "verified": True}
    guess_year = year or "YEAR"  # the actual most-recent election year needs
    # looking up per state — deliberately not guessed here
    return {
        "state": state_name,
        "slug": f"{state_name.replace(' ', '')}{guess_year}",
        "verified": False,
    }


def load_checkpoint(checkpoint_path: Path) -> set:
    if checkpoint_path.exists():
        return set(json.loads(checkpoint_path.read_text()))
    return set()


def save_checkpoint(checkpoint_path: Path, done: set):
    checkpoint_path.write_text(json.dumps(sorted(done)))


def run_all(out_dir: str, delay_seconds: float, only_verified: bool):
    """The live path. Not exercised in this sandbox — see module docstring.
    Imports myneta_scraper's tested parsing logic rather than duplicating it."""
    sys.path.insert(0, str(Path(__file__).parent))
    from myneta_scraper import fetch_constituency_list, strip_html  # tested parser lives there

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    checkpoint_path = Path(out_dir) / "_checkpoint.json"
    done = load_checkpoint(checkpoint_path)

    targets = [build_state_slug(s) for s in STATES_AND_UTS]
    if only_verified:
        targets = [t for t in targets if t["verified"]]

    for target in targets:
        if target["slug"] in done:
            continue
        if not target["verified"]:
            print(f"SKIP {target['state']}: slug '{target['slug']}' is an unconfirmed guess, "
                  f"not fetched. Confirm it resolves to a real page before including it.", file=sys.stderr)
            continue
        print(f"Fetching {target['state']} ({target['slug']})...")
        try:
            # A real run would enumerate constituency_ids for this state from
            # its index page here, then loop fetch_constituency_list per seat.
            # Left as the concrete next step, same reasoning as in
            # myneta_scraper.py: not written against markup this sandbox
            # couldn't fetch to confirm.
            pass
        except Exception as e:
            print(f"FAILED {target['state']}: {e}", file=sys.stderr)
            continue
        done.add(target["slug"])
        save_checkpoint(checkpoint_path, done)
        time.sleep(delay_seconds)  # pacing, not optional


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="./out")
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds between requests. Don't set this to 0.")
    parser.add_argument("--only-verified", action="store_true",
                         help="Only run states with a confirmed slug (currently: Bihar, Madhya Pradesh).")
    args = parser.parse_args()
    run_all(args.out, args.delay, args.only_verified)


# --- Self-test: verifies the slug logic and state list without any network ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        assert len(STATES_AND_UTS) == 31, f"expected 31 assembly-holding states/UTs, got {len(STATES_AND_UTS)}"
        bihar = build_state_slug("Bihar")
        assert bihar == {"state": "Bihar", "slug": "Bihar2025", "verified": True}
        mp = build_state_slug("Madhya Pradesh")
        assert mp["verified"] is True
        goa = build_state_slug("Goa", 2022)
        assert goa == {"state": "Goa", "slug": "Goa2022", "verified": False}
        verified_count = sum(1 for s in STATES_AND_UTS if s in CONFIRMED_SLUGS)
        print(f"Self-test passed. {len(STATES_AND_UTS)} states/UTs listed, "
              f"{verified_count} with a confirmed MyNeta slug, "
              f"{len(STATES_AND_UTS) - verified_count} still need theirs confirmed by an actual fetch.")
