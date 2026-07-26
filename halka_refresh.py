"""
halka_refresh.py

The executor. Turns a plan from `refresh_policy` into actual fetches, with
change detection, and writes the dataset the frontend reads.

    calendar_discovery.py  →  what elections exist        (~1 request/state)
    refresh_policy.py      →  what's worth fetching now   (0 requests, pure)
    halka_refresh.py       →  do it, carefully            (budgeted)

DEFAULTS TO DRY-RUN, DELIBERATELY
---------------------------------
Running with no flags prints the plan and touches nothing. Hitting a
nonprofit's servers is an explicit act (`--execute`), not something that
happens because someone ran a file to see what it did.

CHANGE DETECTION
----------------
Fingerprints are taken over PARSED FIELDS, never raw HTML. Verified reason:
two back-to-back fetches of the same MyNeta candidate page return different
bytes, because CSS is served with a rotating cache-buster (?r=1 / ?r=2) from
different backends. A raw-HTML hash would report "changed" on literally every
poll, which would make the whole unchanged-backoff mechanism inert and lead to
a scraper that re-fetches everything forever while believing it's being smart.

STATE
-----
`refresh_state.json` holds last-fetch times, fingerprints, and unchanged
streaks. It is what makes the scheduler adaptive across runs instead of
starting cold every time; delete it and the next run behaves as if nothing has
ever been fetched.

Usage:
    python3 halka_refresh.py                      # dry run — plan only, no network
    python3 halka_refresh.py --execute            # fetch approved work
    python3 halka_refresh.py --execute --budget 60
    python3 halka_refresh.py --self-test          # offline
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

from refresh_policy import (
    ElectionEvent, PolitenessBudget, Stream, TargetState,
    build_plan, count_missing_critical, record_fingerprint,
)

STATE_FILE = "refresh_state.json"
CALENDAR_FILE = "election_calendar.json"           # auto-discovered, overwritten each run
CURATED_CALENDAR_FILE = "election_calendar_curated.json"  # human-verified, wins on conflict
# Streams with a working ingester. NEWS and MANIFESTO are modelled in
# refresh_policy (their cadence logic is real and tested) but have no fetcher
# yet, so they are excluded from planning rather than silently consuming the
# request budget. Add a stream here the moment its ingester lands.
IMPLEMENTED_STREAMS = (Stream.AFFIDAVIT,)

DATA_DIR = "data"
CHANGELOG_FILE = "data/changelog.jsonl"


def _parse_date(v) -> date | None:
    if not v:
        return None
    if isinstance(v, date):
        return v
    return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()


def load_calendar(*paths: str) -> list[ElectionEvent]:
    """Reads one or more calendar files and merges them.

    Hand-curated entries (with real ECI nomination/scrutiny/withdrawal dates
    and verified=true) take precedence over auto-discovered ones for the same
    seat, since a human-confirmed calendar is strictly better information than
    a polling date scraped from a link label. Precedence is by the `verified`
    flag, not by file order, so it holds regardless of how they're passed.

    Seats are keyed on (constituency, myneta_constituency_id) case-insensitively
    — discovery yields "BANKIPUR" from an uppercase link label while a curated
    entry might say "Bankipur", and those are the same seat.
    """
    entries: list[dict] = []
    for path in paths:
        p = Path(path)
        if not p.exists():
            continue
        raw = json.loads(p.read_text())
        entries.extend(raw.get("events") or raw.get("upcoming") or [])

    by_seat: dict[tuple[str, int | None], ElectionEvent] = {}
    for e in entries:
        ev = ElectionEvent(
            constituency=e.get("constituency", "?"),
            state=e.get("state") or e.get("myneta_slug") or "?",
            myneta_slug=e.get("myneta_slug"),
            myneta_constituency_id=e.get("myneta_constituency_id"),
            notification=_parse_date(e.get("notification")),
            nomination_last=_parse_date(e.get("nomination_last")),
            scrutiny=_parse_date(e.get("scrutiny")),
            withdrawal_last=_parse_date(e.get("withdrawal_last")),
            poll=_parse_date(e.get("poll") or e.get("poll_date")),
            counting=_parse_date(e.get("counting")),
            verified=bool(e.get("verified", False)),
            source=e.get("source"),
        )
        key = (ev.constituency.strip().upper(), ev.myneta_constituency_id)
        existing = by_seat.get(key)
        if existing is None or (ev.verified and not existing.verified):
            by_seat[key] = ev
    return list(by_seat.values())


def load_state(path: str) -> dict[tuple[str, Stream], TargetState]:
    p = Path(path)
    if not p.exists():
        return {}
    raw = json.loads(p.read_text())
    out: dict[tuple[str, Stream], TargetState] = {}
    for item in raw.get("targets", []):
        stream = Stream(item["stream"])
        lf = item.get("last_fetched")
        out[(item["constituency"], stream)] = TargetState(
            constituency=item["constituency"],
            stream=stream,
            last_fetched=datetime.fromisoformat(lf) if lf else None,
            last_fingerprint=item.get("last_fingerprint"),
            records_total=item.get("records_total", 0),
            records_missing_critical=item.get("records_missing_critical", {}),
            consecutive_unchanged=item.get("consecutive_unchanged", 0),
        )
    return out


def save_state(path: str, states: dict[tuple[str, Stream], TargetState]) -> None:
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "targets": [
            {
                "constituency": s.constituency,
                "stream": s.stream.value,
                "last_fetched": s.last_fetched.isoformat() if s.last_fetched else None,
                "last_fingerprint": s.last_fingerprint,
                "records_total": s.records_total,
                "records_missing_critical": s.records_missing_critical,
                "consecutive_unchanged": s.consecutive_unchanged,
            }
            for s in states.values()
        ],
    }
    Path(path).write_text(json.dumps(payload, indent=2))


def append_changelog(entry: dict) -> None:
    """One line per real change. This is the provenance trail — it answers
    'when did this candidate's declared assets change, and to what' without
    needing to diff whole files."""
    p = Path(CHANGELOG_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def fetch_affidavits(slug: str, cid: int, delay: float, max_requests: int) -> tuple[list[dict], int, dict]:
    """Fetch one constituency: list page, then each candidate.

    Returns (records, requests_used, coverage). `coverage` reports how many
    candidates the list page advertised versus how many were actually
    retrieved, so a partial fetch is visible in the stored data rather than
    only in a log line nobody reads."""
    from myneta_scraper import (
        enumerate_candidates, extract_candidate_fields, fetch_candidate_page,
        fetch_constituency_list, strip_html, to_halka_schema,
    )

    used = 0
    list_html = fetch_constituency_list(slug, cid)
    used += 1
    candidates = enumerate_candidates(list_html)
    print(f"    {len(candidates)} candidates on the list page", file=sys.stderr)

    records: list[dict] = []
    dropped: list[dict] = []
    for c in candidates:
        if used >= max_requests:
            print(f"    stopping at request budget ({max_requests}); "
                  f"{len(candidates) - len(records)} candidates not fetched", file=sys.stderr)
            break

        # Retry transient failures. A read timeout silently costing one
        # candidate is a real failure mode, not a cosmetic one — it happened on
        # the first Bankipur run (candidate 2965) and produced a 22-of-23
        # dataset that looked complete. A missing candidate is a person a voter
        # never sees on their ballot preview.
        url = f"https://www.myneta.info/{slug}/candidate.php?candidate_id={c['candidate_id']}"
        last_err = None
        for attempt in range(3):
            time.sleep(delay * (attempt + 1))  # back off on retries
            try:
                html = fetch_candidate_page(slug, c["candidate_id"])
                used += 1
                fields = extract_candidate_fields(strip_html(html))
                records.append(to_halka_schema(fields, c["name"], url))
                last_err = None
                break
            except Exception as e:
                last_err = e
                used += 1
                if attempt < 2:
                    print(f"    candidate {c['candidate_id']} attempt {attempt + 1} failed "
                          f"({type(e).__name__}), retrying…", file=sys.stderr)
        if last_err is not None:
            print(f"    candidate {c['candidate_id']} ({c['name']}) FAILED after 3 attempts: "
                  f"{last_err}", file=sys.stderr)
            dropped.append({"candidate_id": c["candidate_id"], "name": c["name"], "error": str(last_err)})

    if dropped:
        # Never let a partial fetch pass as a complete one.
        print(f"    WARNING: {len(dropped)} of {len(candidates)} candidates could not be "
              f"fetched: {[d['name'] for d in dropped]}", file=sys.stderr)
    coverage = {
        "listed_on_page": len(candidates),
        "retrieved": len(records),
        "complete": len(dropped) == 0 and len(records) == len(candidates),
        "dropped": dropped,
    }
    return records, used, coverage


def run(execute: bool, budget_requests: int, delay: float, calendar_paths: list[str], state_path: str) -> int:
    events = load_calendar(*calendar_paths)
    if not events:
        print(f"No calendar found in {calendar_paths}. Run calendar_discovery.py first:", file=sys.stderr)
        print("  python3 calendar_discovery.py --states Bihar2025 MadhyaPradesh2023 Gujarat2022", file=sys.stderr)
        return 1

    states = load_state(state_path)
    now = datetime.now(timezone.utc)
    budget = PolitenessBudget(max_requests=budget_requests, delay_seconds=delay)
    # Only plan streams that actually have an ingester. Budgeting for streams
    # we cannot fetch starved the one we can: a 30-request run reserved 6 for
    # news/manifesto no-ops, leaving 24 for a 26-request affidavit fetch, which
    # then deferred. The plan looked full while doing nothing.
    plan = build_plan(events=events, states=states, now=now, budget=budget,
                      streams=IMPLEMENTED_STREAMS)

    print(f"\n{'EXECUTING' if execute else 'DRY RUN'} — plan generated {plan['generated_at']}")
    print(f"Calendar: {len(events)} seat(s) tracked")
    print(f"Budget: {budget_requests} requests, {delay}s apart "
          f"(~{plan['estimated_runtime_minutes']} min if fully spent)")
    print(f"\nApproved ({len(plan['approved'])}):")
    for item in plan["approved"]:
        flag = "" if item["verified_calendar"] else "  [UNVERIFIED CALENDAR]"
        print(f"  {item['priority']:.3f}  {item['constituency']:14s} {item['stream']:10s} "
              f"{item['phase']:11s} ~{item['estimated_requests']:3d} req{flag}")
        print(f"          {item['reason']}")

    if plan["deferred_over_budget"]:
        print(f"\nDeferred, over budget ({len(plan['deferred_over_budget'])}) — "
              f"raise --budget or wait for the next run:")
        for item in plan["deferred_over_budget"]:
            print(f"  {item['priority']:.3f}  {item['constituency']:14s} {item['stream']:10s} "
                  f"~{item['estimated_requests']} req")

    skipped_shown = plan["skipped"][:6]
    if skipped_shown:
        print(f"\nSkipped ({len(plan['skipped'])} total, showing {len(skipped_shown)}):")
        for item in skipped_shown:
            print(f"  {item['constituency']:14s} {item['stream']:10s} {item['reason']}")

    if plan["unverified_calendar_warnings"]:
        print(f"\nNOTE: these seats' calendars were auto-discovered, not human-verified: "
              f"{', '.join(sorted(set(plan['unverified_calendar_warnings'])))}")
        print("      Polling dates come from MyNeta index labels; nomination/withdrawal")
        print("      dates are unknown, so phase detection is coarser for them.")

    unimplemented = [s.value for s in Stream
                     if s not in IMPLEMENTED_STREAMS and s is not Stream.CALENDAR]
    if unimplemented:
        print(f"\nNot planned — no ingester yet for: {', '.join(unimplemented)}. "
              f"Their cadence logic exists in refresh_policy but nothing fetches them,")
        print("      so they are excluded from the budget rather than reserving requests.")

    if not execute:
        print("\nDry run — nothing fetched. Re-run with --execute to actually fetch.")
        return 0

    # --- real fetching ---------------------------------------------------
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    remaining = budget_requests
    changed_any = False

    for item in plan["approved"]:
        if remaining <= 1:
            print("\n  Request budget exhausted.")
            break

        slug, cid = item["myneta_slug"], item["myneta_constituency_id"]
        if not slug or cid is None:
            print(f"\n  SKIP {item['constituency']}: no MyNeta slug/id on the calendar entry.")
            continue

        print(f"\n  Fetching {item['constituency']} ({slug} id={cid})…")
        try:
            records, used, coverage = fetch_affidavits(slug, cid, delay, remaining)
        except Exception as e:
            print(f"    FAILED: {e}", file=sys.stderr)
            continue
        remaining -= used

        key = (item["constituency"], Stream.AFFIDAVIT)
        prev = states.get(key) or TargetState(item["constituency"], Stream.AFFIDAVIT)
        fp = record_fingerprint(records)
        changed = fp != prev.last_fingerprint

        out_path = Path(DATA_DIR) / f"{slug}_{cid}.json"
        payload = {
            "constituency": item["constituency"],
            "state": item["state"],
            "myneta_slug": slug,
            "myneta_constituency_id": cid,
            "source": f"https://www.myneta.info/{slug}/index.php?action=show_candidates&constituency_id={cid}",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "phase": item["phase"],
            "fingerprint": fp,
            "candidate_count": len(records),
            "coverage": coverage,
            "candidates": records,
        }
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

        missing = count_missing_critical(records)
        states[key] = TargetState(
            constituency=item["constituency"], stream=Stream.AFFIDAVIT,
            last_fetched=datetime.now(timezone.utc), last_fingerprint=fp,
            records_total=len(records), records_missing_critical=missing,
            consecutive_unchanged=0 if changed else prev.consecutive_unchanged + 1,
        )

        if changed:
            changed_any = True
            append_changelog({
                "at": datetime.now(timezone.utc).isoformat(),
                "constituency": item["constituency"], "slug": slug, "constituency_id": cid,
                "previous_fingerprint": prev.last_fingerprint, "fingerprint": fp,
                "candidate_count": len(records), "phase": item["phase"],
            })
            print(f"    CHANGED — {len(records)} candidates, {used} requests → {out_path}")
        else:
            print(f"    unchanged ({prev.consecutive_unchanged + 1} in a row) — "
                  f"{used} requests → {out_path}")

        if not coverage["complete"]:
            print(f"    INCOMPLETE: {coverage['retrieved']}/{coverage['listed_on_page']} "
                  f"candidates retrieved — re-run to fill the gap.")
        gaps = {k: v for k, v in missing.items() if v}
        if gaps:
            print(f"    incomplete fields: {gaps}")

    save_state(state_path, states)
    print(f"\nState saved to {state_path}.")
    if changed_any:
        print(f"Changes recorded in {CHANGELOG_FILE}.")
    return 0


# --- Self-test (no network) ----------------------------------------------

def self_test():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        cal = Path(td) / "cal.json"
        # A human-verified entry and an auto-discovered one for the SAME seat.
        # The verified one must win — that's the precedence rule load_calendar
        # exists to enforce.
        cal.write_text(json.dumps({"events": [
            {"constituency": "Bankipur", "state": "Bihar", "myneta_slug": "Bihar2025",
             "myneta_constituency_id": 252, "poll": "2026-07-30", "counting": "2026-08-03",
             "nomination_last": "2026-07-13", "scrutiny": "2026-07-14",
             "withdrawal_last": "2026-07-16", "verified": True},
            {"constituency": "Bankipur", "state": "Bihar", "myneta_slug": "Bihar2025",
             "myneta_constituency_id": 252, "poll": "2026-07-30", "verified": False},
            {"constituency": "Datia", "state": "MadhyaPradesh2023", "myneta_slug": "MadhyaPradesh2023",
             "myneta_constituency_id": 234, "poll": "2026-07-30", "verified": False},
        ]}))
        events = load_calendar(str(cal))
        assert len(events) == 2, f"same seat must collapse to one entry, got {len(events)}"
        bankipur = [e for e in events if e.constituency == "Bankipur"][0]
        assert bankipur.verified is True, "human-verified calendar must win over auto-discovered"
        assert bankipur.withdrawal_last == date(2026, 7, 16)

        # State round-trips without loss.
        sp = Path(td) / "state.json"
        st = {("Bankipur", Stream.AFFIDAVIT): TargetState(
            "Bankipur", Stream.AFFIDAVIT,
            last_fetched=datetime(2026, 7, 25, 11, 24, tzinfo=timezone.utc),
            last_fingerprint="abc123", records_total=23,
            records_missing_critical={"criminalCount": 0}, consecutive_unchanged=2)}
        save_state(str(sp), st)
        loaded = load_state(str(sp))
        got = loaded[("Bankipur", Stream.AFFIDAVIT)]
        assert got.last_fingerprint == "abc123" and got.consecutive_unchanged == 2
        assert got.records_total == 23 and got.last_fetched.year == 2026

        # A plan over the loaded calendar ranks the live seats and stays in budget.
        plan = build_plan(events=events, states=loaded,
                          now=datetime(2026, 7, 26, 9, 0, tzinfo=timezone.utc),
                          budget=PolitenessBudget(max_requests=50, delay_seconds=3.0))
        assert plan["planned_requests"] <= 50
        assert plan["approved"], "seats polling in 4 days must produce work"

        approved = {(a["constituency"], a["stream"]): a for a in plan["approved"]}
        skipped = {(s["constituency"], s["stream"]): s for s in plan["skipped"]}

        # Datia's affidavits have never been fetched → maximal gap → scheduled.
        assert ("Datia", "affidavit") in approved, "never-fetched seat must be scheduled"

        # Bankipur's were fetched ~22h ago and the candidate field locked at the
        # withdrawal deadline, so the politeness floor must suppress a refetch
        # even though the seat polls in four days. This is the behaviour that
        # separates this scheduler from a daily cron, so it's asserted directly.
        assert ("Bankipur", "affidavit") in skipped, "recently-fetched seat must be held back"
        assert "min interval" in skipped[("Bankipur", "affidavit")]["reason"]

        # During CAMPAIGN, news is the volatile stream and must outrank
        # affidavits for the same seat — the field is locked, the coverage isn't.
        assert approved[("Datia", "news")]["priority"] > approved[("Datia", "affidavit")]["priority"], \
            "news must outrank affidavits once the candidate list is final"

    print("halka_refresh self-test passed.")
    print("  covers: calendar precedence (verified > discovered), state round-trip,")
    print("          budget cap, and never-fetched-outranks-recently-fetched.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--execute", action="store_true", help="Actually fetch. Without this, plan only.")
    ap.add_argument("--budget", type=int, default=200, help="Max HTTP requests this run.")
    ap.add_argument("--delay", type=float, default=3.0, help="Seconds between requests. Don't set to 0.")
    ap.add_argument("--calendar", nargs="+", default=[CURATED_CALENDAR_FILE, CALENDAR_FILE],
                    help="Calendar files, merged. Human-verified entries win over auto-discovered ones.")
    ap.add_argument("--state", default=STATE_FILE)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0
    return run(args.execute, args.budget, args.delay, list(args.calendar), args.state)


if __name__ == "__main__":
    sys.exit(main())
