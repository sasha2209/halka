"""
calendar_discovery.py

The cheap poll that drives the expensive one.

THE PROBLEM THIS SOLVES
-----------------------
`refresh_policy.py` can rank work by how close a seat is to polling day — but
only if something tells it a seat has an election coming at all. Discovering
that was the missing piece, and the obvious source doesn't work:

    eci.gov.in returns 403 to automated requests, browser User-Agent included.
    Verified 2026-07-26. So an unattended job cannot read the ECI calendar
    directly, and pretending otherwise would produce a scheduler that silently
    never fires.

The fix came from actually reading MyNeta's markup instead of assuming it only
holds candidate data. Every state index page labels its own seats with their
election dates:

    <a ... constituency_id=59  title='Date of Election 17-11-2023'>DATIA</a>
    <a ... constituency_id=234'>DATIA : BYE ELECTION ON 30-07-2026 </a>

That is an election calendar, on a host that is reachable and whose robots.txt
permits these paths. One request per state returns every seat, its MyNeta ID,
and its polling date. So the calendar signal costs ~30 requests for all of
India, not one per constituency — and it comes from the same site we already
read, adding no new dependency.

THE COST ASYMMETRY THIS BUYS
----------------------------
    Discovery:  1 request per state       (~30 total, all of India)
    Ingestion:  1 + N requests per seat   (~24 for a 23-candidate seat)

Discovering that nothing changed nationally is ~30 requests. Blindly
re-scraping every seat is ~100,000. That ratio is the whole argument for
event-driven refresh, and it is why this module exists as a separate, cheap
stage rather than being folded into the scraper.

WHAT IT CANNOT TELL YOU
-----------------------
MyNeta publishes the POLLING date. It does not publish nomination, scrutiny,
or withdrawal deadlines — those come from the ECI notification. So a
discovered event has `poll` filled in and the earlier milestones left None,
and `refresh_policy` degrades honestly: without a withdrawal date it treats
the run-up as CAMPAIGN rather than inventing a NOMINATION window. Filling
those in is a human step, and they're marked unverified until someone does it.

Self-test: `python3 calendar_discovery.py --self-test` (no network).
Live run:  `python3 calendar_discovery.py --states Bihar2025 MadhyaPradesh2023 Gujarat2022`
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

MYNETA_BASE = "https://www.myneta.info"
USER_AGENT = "Halka civic-data bot (voter information tool; contact in repo README)"

# Two link shapes appear on a state index page, and they carry the date
# differently. Both are matched rather than assuming one form — the by-election
# form is the one that matters most for this project, since by-polls are
# exactly the events that appear with little warning between general elections.
#
#   general:  constituency_id=59  title='Date of Election 17-11-2023'>DATIA</a>
#   by-poll:  constituency_id=234'>DATIA : BYE ELECTION ON 30-07-2026 </a>
RE_GENERAL = re.compile(
    r"constituency_id=(\d+)\s+title='Date of Election\s+(\d{2}-\d{2}-\d{4})'\s*>([^<]+?)\s*</a>",
    re.IGNORECASE,
)
RE_BYPOLL = re.compile(
    r"constituency_id=(\d+)'\s*>\s*([^<:]+?)\s*:\s*BYE ELECTION ON\s+(\d{2}-\d{2}-\d{4})\s*</a>",
    re.IGNORECASE,
)


def parse_dmy(s: str) -> date:
    return datetime.strptime(s.strip(), "%d-%m-%Y").date()


def parse_state_index(html: str, slug: str) -> list[dict]:
    """Extract every seat + polling date from one state index page.

    Pure string work, no network — this is the part the self-test covers
    against real captured markup.
    """
    seats: dict[tuple[str, int], dict] = {}

    for cid, dmy, name in RE_GENERAL.findall(html):
        key = (slug, int(cid))
        seats[key] = {
            "myneta_slug": slug,
            "myneta_constituency_id": int(cid),
            "constituency": name.strip(),
            "poll_date": parse_dmy(dmy).isoformat(),
            "election_type": "general",
        }

    for cid, name, dmy in RE_BYPOLL.findall(html):
        key = (slug, int(cid))
        seats[key] = {
            "myneta_slug": slug,
            "myneta_constituency_id": int(cid),
            "constituency": name.strip(),
            "poll_date": parse_dmy(dmy).isoformat(),
            "election_type": "bye-election",
        }

    return sorted(seats.values(), key=lambda s: (s["poll_date"], s["constituency"]))


def fetch_state_index(slug: str, timeout: int = 25) -> str:
    import requests

    resp = requests.get(f"{MYNETA_BASE}/{slug}/", headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def discover(slugs: list[str], delay: float = 3.0, today: date | None = None) -> dict:
    """Fetch each state index once and return everything upcoming or recent.

    `delay` is pacing between states, not an optimization target — see the
    politeness reasoning in refresh_policy.PolitenessBudget.
    """
    today = today or datetime.now(timezone.utc).date()
    all_seats: list[dict] = []
    errors: list[dict] = []

    for i, slug in enumerate(slugs):
        try:
            html = fetch_state_index(slug)
            seats = parse_state_index(html, slug)
            all_seats.extend(seats)
            print(f"  {slug}: {len(seats)} seats found", file=sys.stderr)
        except Exception as e:
            errors.append({"slug": slug, "error": str(e)})
            print(f"  {slug}: FAILED — {e}", file=sys.stderr)
        if i < len(slugs) - 1:
            time.sleep(delay)

    upcoming = [s for s in all_seats if s["poll_date"] >= today.isoformat()]
    upcoming.sort(key=lambda s: s["poll_date"])

    return {
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "today": today.isoformat(),
        "states_checked": slugs,
        "request_count": len(slugs),
        "seats_total": len(all_seats),
        "upcoming": upcoming,
        "errors": errors,
        "note": (
            "Polling dates are as published on MyNeta state index pages. Nomination, "
            "scrutiny and withdrawal dates are NOT available from this source and are "
            "left unset — they come from the ECI notification and need a human to fill "
            "in. Seats here are flagged unverified until that happens."
        ),
    }


def to_calendar_events(discovery: dict) -> list[dict]:
    """Shape discovery output into refresh_policy.ElectionEvent-compatible dicts."""
    events = []
    for seat in discovery["upcoming"]:
        events.append({
            "constituency": seat["constituency"],
            "state": seat["myneta_slug"],
            "myneta_slug": seat["myneta_slug"],
            "myneta_constituency_id": seat["myneta_constituency_id"],
            "poll": seat["poll_date"],
            "counting": None,
            "notification": None,
            "nomination_last": None,
            "scrutiny": None,
            "withdrawal_last": None,
            # Discovered automatically, not confirmed by a human against the ECI
            # notification. refresh_policy surfaces this in every plan it emits.
            "verified": False,
            "source": f"{MYNETA_BASE}/{seat['myneta_slug']}/ (index page, auto-discovered)",
            "election_type": seat["election_type"],
        })
    return events


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--states", nargs="+", help="MyNeta state slugs, e.g. Bihar2025 Gujarat2022")
    ap.add_argument("--delay", type=float, default=3.0, help="Seconds between state fetches. Don't set to 0.")
    ap.add_argument("--out", default="election_calendar.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        run_self_test()
        return

    if not args.states:
        ap.error("--states is required for a live run (or use --self-test)")

    print(f"Discovering elections across {len(args.states)} state index page(s)…", file=sys.stderr)
    result = discover(args.states, delay=args.delay)
    result["events"] = to_calendar_events(result)

    Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nWrote {args.out}", file=sys.stderr)
    print(f"{len(result['upcoming'])} upcoming/current seat(s) from {result['request_count']} request(s):", file=sys.stderr)
    for s in result["upcoming"][:20]:
        print(f"  {s['poll_date']}  {s['constituency']:28s} {s['myneta_slug']} id={s['myneta_constituency_id']} ({s['election_type']})", file=sys.stderr)


# --- Self-test against real captured markup (no network) -----------------

def run_self_test():
    # Verbatim fragments captured live from MyNeta on 2026-07-26. Kept as
    # real samples rather than hand-written fixtures so the test fails if the
    # site's markup drifts away from what the parser was built against.
    mp_sample = (
        "<a class='w3-bar-item w3-button w3-padding-small' href=index.php?action=show_candidates&"
        "constituency_id=59  title='Date of Election 17-11-2023'>DATIA</a>  "
        "<a class='w3-bar-item' href=index.php?action=show_candidates&constituency_id=234'>"
        "DATIA : BYE ELECTION ON 30-07-2026 </a>"
    )
    seats = parse_state_index(mp_sample, "MadhyaPradesh2023")
    by_id = {s["myneta_constituency_id"]: s for s in seats}
    assert 59 in by_id and 234 in by_id, f"expected both seat forms parsed, got {list(by_id)}"
    assert by_id[59]["poll_date"] == "2023-11-17", by_id[59]
    assert by_id[59]["election_type"] == "general"
    assert by_id[234]["poll_date"] == "2026-07-30", by_id[234]
    assert by_id[234]["election_type"] == "bye-election"
    assert by_id[234]["constituency"] == "DATIA", by_id[234]

    bihar_sample = (
        "<a href=index.php?action=show_candidates&constituency_id=252'>"
        "BANKIPUR : BYE ELECTION ON 30-07-2026</a>"
    )
    bihar = parse_state_index(bihar_sample, "Bihar2025")
    assert len(bihar) == 1 and bihar[0]["myneta_constituency_id"] == 252, bihar
    assert bihar[0]["poll_date"] == "2026-07-30"

    gj_sample = (
        "<a href=index.php?action=show_candidates&constituency_id=618'>"
        "MANJALPUR : BYE ELECTION ON 30-07-2026 </a>"
        "<a href=index.php?action=show_candidates&constituency_id=602  "
        "title='Date of Election 05-12-2022'>MANJALPUR</a>"
    )
    gj = parse_state_index(gj_sample, "Gujarat2022")
    assert len(gj) == 2, gj
    bypoll = [s for s in gj if s["election_type"] == "bye-election"][0]
    assert bypoll["myneta_constituency_id"] == 618 and bypoll["poll_date"] == "2026-07-30"

    # Filtering: only future/current polls surface as upcoming.
    fake = {
        "upcoming": [s for s in (seats + bihar + gj) if s["poll_date"] >= "2026-07-26"],
    }
    events = to_calendar_events(fake)
    assert len(events) == 3, f"expected the 3 seats polling 2026-07-30, got {len(events)}"
    assert all(e["verified"] is False for e in events), "auto-discovered events must not claim verification"
    assert all(e["nomination_last"] is None for e in events), "nomination dates aren't available from this source"

    print("calendar_discovery self-test passed (parsed real captured MyNeta markup).")
    print(f"  {len(events)} seats polling 2026-07-30 recovered from index markup alone:")
    for e in events:
        print(f"    {e['constituency']:12s} {e['myneta_slug']:20s} id={e['myneta_constituency_id']}")


if __name__ == "__main__":
    main()
