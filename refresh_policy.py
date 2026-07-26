"""
refresh_policy.py

The layer that decides WHAT to re-fetch and WHEN, instead of scraping
everything on a blind daily cron.

WHY THIS EXISTS
---------------
A uniform "refresh everything daily" job is wrong in both directions at once:
it hammers a nonprofit's servers re-reading affidavits that haven't changed in
eight months, and it's still too slow to catch a candidate withdrawing two days
before a poll. Neither failure mode is acceptable — the first is rude, the
second misinforms a voter at exactly the moment they're deciding.

So the scheduling question isn't "how often do we scrape." It's "which single
fetch, right now, most improves what a voter about to vote actually knows."
This module answers that question and nothing else — it computes a plan. It
does not fetch. `halka_refresh.py` executes the plan.

THE THREE THINGS THAT SET PRIORITY
----------------------------------
    value = urgency x volatility x gap

  urgency     How much a voter needs this data NOW. Rises as poll day
              approaches, and collapses to almost nothing the moment voting
              ends — after the poll closes, a fresh affidavit fetch cannot
              change anyone's vote. Refreshing a concluded seat at the same
              rate as a live one is the single biggest waste in a naive
              scheduler.

  volatility  How likely the data actually changed since we last looked.
              Affidavits are near-frozen outside a nomination window and
              change daily inside one. Same field, two-orders-of-magnitude
              difference in change rate depending only on the calendar.

  gap         How bad our current record is. A candidate whose criminal-case
              count we failed to parse outranks one whose record is complete,
              because that's the highest-stakes field in the whole dataset.
              Staleness counts here too, but incompleteness counts more.

Multiplying rather than adding matters: if any one factor is ~0 the fetch is
worthless, and that's correct. A complete record (gap~0) in a concluded
election (urgency~0) that never changes (volatility~0) should never be
re-fetched, and this arithmetic says so without a special case.

VERIFIED CONSTRAINTS THIS DESIGN IS BUILT AROUND
------------------------------------------------
Checked live from this machine on 2026-07-25/26, not assumed:

1. myneta.info is reachable and its robots.txt permits these paths (it only
   disallows *printer=true / *print=true).

2. MyNeta sends `Cache-Control: no-store, no-cache` and NO ETag or
   Last-Modified, and ignores If-Modified-Since (returns a full 200 + 98KB
   for a request that should have been a 304). So there is no cheap
   "did it change?" HTTP probe. Every check costs a full page fetch. That
   is precisely why the plan has to be budgeted — see PolitenessBudget.

3. Hashing raw HTML does NOT work for change detection. Two back-to-back
   fetches of the same candidate page differ, because MyNeta serves from
   backends with different CSS cache-buster values (?r=1 vs ?r=2). A raw
   hash would report "changed" on every single poll forever. Change
   detection therefore hashes the EXTRACTED FIELDS — see record_fingerprint().

4. eci.gov.in returns 403 to automated requests, including with a browser
   User-Agent. The election calendar therefore cannot be scraped from ECI
   directly by an unattended job; it is maintained as a reviewed data file
   (election_calendar.json) with each date marked verified or unverified.
   That is a real limitation, recorded here rather than papered over.

WHAT THIS MODULE DOES NOT DO
----------------------------
No network, no filesystem writes, no scheduling side effects. Pure functions
over a calendar and a state snapshot, so it can be unit-tested offline — and
so a human can read the plan before anything touches ADR's servers.

Self-test: `python3 refresh_policy.py` (no network needed).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Iterable


# --- Election lifecycle --------------------------------------------------
# Phases follow the actual ECI sequence for an Indian election. The dates
# that separate them come from the ECI's own notification for a given seat.

class Phase(str, Enum):
    DORMANT = "dormant"            # No election scheduled. Affidavits frozen.
    ANNOUNCED = "announced"        # Schedule out, nominations not yet open.
    NOMINATION = "nomination"      # Candidates filing. Highest churn of the cycle.
    SCRUTINY = "scrutiny"          # Returning officer accepting/rejecting filings.
    WITHDRAWAL = "withdrawal"      # Withdrawals allowed; final field forms here.
    CAMPAIGN = "campaign"          # Candidate list locked. News is what moves now.
    SILENCE = "silence"            # Last 48h. Campaigning banned; voters deciding.
    POLL_DAY = "poll_day"          # Voting.
    COUNTING = "counting"          # Results, round by round.
    CONCLUDED = "concluded"        # Archive. Nothing a voter can act on.


class Stream(str, Enum):
    """Independent data streams. They change at wildly different rates, so
    they get scheduled independently rather than as one 'refresh' unit."""
    AFFIDAVIT = "affidavit"        # MyNeta/ECI sworn declarations
    NEWS = "news"                  # Per-candidate press coverage
    MANIFESTO = "manifesto"        # Party platform documents
    RESULTS = "results"            # Counting-day tallies
    CALENDAR = "calendar"          # The ECI schedule itself


# How fast each stream's data actually changes, per phase, on a 0..1 scale.
# 0.0 means "re-fetching cannot possibly return anything new."
# These are judgments about the real world, not tuning knobs — a candidate
# genuinely cannot file a new affidavit after the withdrawal deadline passes.
VOLATILITY: dict[Phase, dict[Stream, float]] = {
    Phase.DORMANT:    {Stream.AFFIDAVIT: 0.01, Stream.NEWS: 0.05, Stream.MANIFESTO: 0.00, Stream.RESULTS: 0.0, Stream.CALENDAR: 0.30},
    Phase.ANNOUNCED:  {Stream.AFFIDAVIT: 0.05, Stream.NEWS: 0.40, Stream.MANIFESTO: 0.30, Stream.RESULTS: 0.0, Stream.CALENDAR: 0.60},
    Phase.NOMINATION: {Stream.AFFIDAVIT: 1.00, Stream.NEWS: 0.70, Stream.MANIFESTO: 0.50, Stream.RESULTS: 0.0, Stream.CALENDAR: 0.40},
    Phase.SCRUTINY:   {Stream.AFFIDAVIT: 0.90, Stream.NEWS: 0.70, Stream.MANIFESTO: 0.30, Stream.RESULTS: 0.0, Stream.CALENDAR: 0.30},
    Phase.WITHDRAWAL: {Stream.AFFIDAVIT: 0.85, Stream.NEWS: 0.75, Stream.MANIFESTO: 0.20, Stream.RESULTS: 0.0, Stream.CALENDAR: 0.30},
    # Field is locked after withdrawal closes. Affidavit volatility drops to
    # near zero — only ADR back-filling a candidate they hadn't indexed yet.
    Phase.CAMPAIGN:   {Stream.AFFIDAVIT: 0.15, Stream.NEWS: 1.00, Stream.MANIFESTO: 0.60, Stream.RESULTS: 0.0, Stream.CALENDAR: 0.15},
    Phase.SILENCE:    {Stream.AFFIDAVIT: 0.05, Stream.NEWS: 0.60, Stream.MANIFESTO: 0.05, Stream.RESULTS: 0.0, Stream.CALENDAR: 0.10},
    Phase.POLL_DAY:   {Stream.AFFIDAVIT: 0.02, Stream.NEWS: 0.50, Stream.MANIFESTO: 0.00, Stream.RESULTS: 0.0, Stream.CALENDAR: 0.10},
    Phase.COUNTING:   {Stream.AFFIDAVIT: 0.00, Stream.NEWS: 0.80, Stream.MANIFESTO: 0.00, Stream.RESULTS: 1.0, Stream.CALENDAR: 0.05},
    Phase.CONCLUDED:  {Stream.AFFIDAVIT: 0.02, Stream.NEWS: 0.10, Stream.MANIFESTO: 0.00, Stream.RESULTS: 0.02, Stream.CALENDAR: 0.05},
}

# Minimum spacing between fetches of the same target, per phase. A floor on
# politeness that the priority score cannot override: even if a record looks
# maximally valuable, we will not re-hit the same URL more often than this.
MIN_INTERVAL: dict[Phase, timedelta] = {
    Phase.DORMANT:    timedelta(days=30),
    Phase.ANNOUNCED:  timedelta(days=3),
    Phase.NOMINATION: timedelta(hours=8),
    Phase.SCRUTINY:   timedelta(hours=8),
    Phase.WITHDRAWAL: timedelta(hours=8),
    Phase.CAMPAIGN:   timedelta(days=2),
    Phase.SILENCE:    timedelta(days=1),
    Phase.POLL_DAY:   timedelta(days=1),
    Phase.COUNTING:   timedelta(minutes=10),
    Phase.CONCLUDED:  timedelta(days=180),
}

# Fields whose absence hurts a voter most. Weighted, because "we don't know
# if this person has criminal cases" is a categorically worse gap than "we
# don't know their profession."
CRITICAL_FIELDS: dict[str, float] = {
    "criminalCount": 1.00,   # highest-stakes field in the dataset
    "name": 0.90,
    "party": 0.70,
    "assets": 0.45,
    "education": 0.35,
    "age": 0.20,
    "profession": 0.20,
}


@dataclass
class ElectionEvent:
    """One seat's election calendar. Dates come from the ECI notification.

    `verified` records whether a human actually confirmed these dates against
    a primary source. Unverified entries still schedule work, but the plan
    flags them — consistent with the project rule that a guess is never
    silently promoted to a fact.
    """
    constituency: str
    state: str
    myneta_slug: str | None = None
    myneta_constituency_id: int | None = None
    notification: date | None = None
    nomination_last: date | None = None
    scrutiny: date | None = None
    withdrawal_last: date | None = None
    poll: date | None = None
    counting: date | None = None
    verified: bool = False
    source: str | None = None

    def phase_on(self, today: date) -> Phase:
        """Which lifecycle phase this seat is in on a given date."""
        if self.poll is None:
            return Phase.DORMANT
        counting = self.counting or self.poll
        if today > counting:
            return Phase.CONCLUDED
        if today == counting:
            return Phase.COUNTING
        if today == self.poll:
            return Phase.POLL_DAY
        if today > self.poll:
            # Between poll and counting — votes cast, results not out.
            return Phase.COUNTING
        # Silence period: the 48h before polling closes.
        if (self.poll - today).days <= 2:
            return Phase.SILENCE
        if self.withdrawal_last and today > self.withdrawal_last:
            return Phase.CAMPAIGN
        if self.withdrawal_last and self.scrutiny and self.scrutiny < today <= self.withdrawal_last:
            return Phase.WITHDRAWAL
        if self.scrutiny and today == self.scrutiny:
            return Phase.SCRUTINY
        if self.nomination_last and today <= self.nomination_last:
            if self.notification and today < self.notification:
                return Phase.ANNOUNCED
            return Phase.NOMINATION
        if self.notification and today < self.notification:
            return Phase.ANNOUNCED
        return Phase.CAMPAIGN

    def days_to_poll(self, today: date) -> int | None:
        return None if self.poll is None else (self.poll - today).days


@dataclass
class TargetState:
    """What we currently hold for one (constituency, stream) pair."""
    constituency: str
    stream: Stream
    last_fetched: datetime | None = None
    last_fingerprint: str | None = None
    records_total: int = 0
    records_missing_critical: dict[str, int] = field(default_factory=dict)
    consecutive_unchanged: int = 0

    def staleness_days(self, now: datetime) -> float:
        if self.last_fetched is None:
            return 999.0
        return max(0.0, (now - self.last_fetched).total_seconds() / 86400.0)


# --- The three factors ---------------------------------------------------

def urgency(phase: Phase, days_to_poll: int | None) -> float:
    """How much a voter needs this data right now.

    The shape that matters: urgency climbs steeply in the final fortnight
    (when people actually start paying attention and the information can
    still change a vote) and collapses after polls close. A voter cannot
    un-cast a ballot, so post-poll freshness has archival value only.
    """
    if phase is Phase.COUNTING:
        return 1.0          # results are the only thing anyone wants that day
    if phase is Phase.CONCLUDED:
        return 0.03         # archive/history value only
    if phase is Phase.POLL_DAY:
        return 0.85         # people still checking on the way to the booth
    if days_to_poll is None:
        return 0.10         # no election scheduled — background upkeep
    if days_to_poll < 0:
        return 0.03
    if days_to_poll <= 2:
        return 1.00         # silence period: last chance to inform a decision
    if days_to_poll <= 7:
        return 0.90
    if days_to_poll <= 14:
        return 0.75
    if days_to_poll <= 30:
        return 0.50
    if days_to_poll <= 90:
        return 0.25
    return 0.12


def gap(state: TargetState, now: datetime) -> float:
    """How deficient our current record is: incompleteness first, staleness
    second. Incompleteness dominates because a missing criminal-case count is
    a permanent hole in what a voter sees, while a day-old-but-complete record
    is usually still correct."""
    if state.last_fetched is None:
        return 1.0  # never fetched — maximum gap by definition

    incompleteness = 0.0
    if state.records_total > 0:
        for fname, weight in CRITICAL_FIELDS.items():
            missing = state.records_missing_critical.get(fname, 0)
            incompleteness += weight * (missing / state.records_total)
        incompleteness = min(1.0, incompleteness)

    # Staleness saturates at ~30 days; beyond that, older isn't more urgent.
    staleness = min(1.0, state.staleness_days(now) / 30.0)

    return min(1.0, 0.70 * incompleteness + 0.30 * staleness)


def decay_for_unchanged(consecutive_unchanged: int) -> float:
    """Back off from targets that keep coming back identical.

    If a seat's affidavits have been byte-identical for six consecutive
    checks, the seventh check is probably wasted. Halving each time (floored
    at 1/8) is deliberately gentle: it slows down, never stops, so a late
    correction is still eventually caught.
    """
    if consecutive_unchanged <= 1:
        return 1.0
    return max(0.125, 0.5 ** (consecutive_unchanged - 1))


def priority(event: ElectionEvent, state: TargetState, now: datetime) -> float:
    """Composite value of refreshing this one (constituency, stream) now."""
    today = now.date()
    phase = event.phase_on(today)
    vol = VOLATILITY[phase].get(state.stream, 0.0)
    if vol == 0.0:
        return 0.0
    return (
        urgency(phase, event.days_to_poll(today))
        * vol
        * gap(state, now)
        * decay_for_unchanged(state.consecutive_unchanged)
    )


def is_eligible(event: ElectionEvent, state: TargetState, now: datetime) -> tuple[bool, str]:
    """Politeness floor. Returns (eligible, reason_if_not).

    This is checked BEFORE priority and cannot be overridden by a high score —
    the whole point of a floor is that it holds when the scheduler is most
    tempted to breach it.
    """
    phase = event.phase_on(now.date())
    if state.last_fetched is None:
        return True, ""
    elapsed = now - state.last_fetched
    floor = MIN_INTERVAL[phase]
    if elapsed < floor:
        return False, f"min interval {floor} not elapsed (last fetch {elapsed} ago, phase={phase.value})"
    return True, ""


# --- Budgeted planning ---------------------------------------------------

@dataclass
class PolitenessBudget:
    """A hard ceiling on requests per run, and the pacing between them.

    Not a performance setting. MyNeta is run by a nonprofit and has no
    conditional-request support (verified — see module docstring), so every
    check we make costs them a full page render. The budget is the mechanism
    that turns 'be respectful' from an intention into an enforced property.
    """
    max_requests: int = 200
    delay_seconds: float = 3.0

    def estimated_runtime_minutes(self, planned_requests: int) -> float:
        return (min(planned_requests, self.max_requests) * self.delay_seconds) / 60.0


@dataclass
class PlannedFetch:
    constituency: str
    state: str
    stream: Stream
    phase: Phase
    priority: float
    estimated_requests: int
    reason: str
    verified_calendar: bool
    myneta_slug: str | None = None
    myneta_constituency_id: int | None = None

    def to_dict(self) -> dict:
        return {
            "constituency": self.constituency,
            "state": self.state,
            "stream": self.stream.value,
            "phase": self.phase.value,
            "priority": round(self.priority, 4),
            "estimated_requests": self.estimated_requests,
            "reason": self.reason,
            "verified_calendar": self.verified_calendar,
            "myneta_slug": self.myneta_slug,
            "myneta_constituency_id": self.myneta_constituency_id,
        }


def estimate_requests(stream: Stream, state: TargetState) -> int:
    """How many HTTP requests this fetch will actually cost.

    Affidavits cost 1 (constituency list) + 1 per candidate. Getting this
    roughly right matters: a 23-candidate seat is 24 requests, so a budget of
    200 covers about eight seats, not two hundred.
    """
    if stream is Stream.AFFIDAVIT:
        return 1 + (state.records_total if state.records_total else 25)
    if stream is Stream.NEWS:
        return max(1, state.records_total or 1)
    return 1


def build_plan(
    events: Iterable[ElectionEvent],
    states: dict[tuple[str, Stream], TargetState],
    now: datetime,
    budget: PolitenessBudget | None = None,
    streams: Iterable[Stream] = (Stream.AFFIDAVIT, Stream.NEWS, Stream.MANIFESTO, Stream.RESULTS),
) -> dict:
    """Produce a ranked, budget-capped work plan. Pure — no side effects.

    Returns both what to do and what was deliberately skipped, because a plan
    that silently drops work reads as 'we covered everything' when it didn't.
    """
    budget = budget or PolitenessBudget()
    candidates_for_work: list[PlannedFetch] = []
    skipped: list[dict] = []

    for event in events:
        phase = event.phase_on(now.date())
        for stream in streams:
            key = (event.constituency, stream)
            state = states.get(key) or TargetState(constituency=event.constituency, stream=stream)

            eligible, why_not = is_eligible(event, state, now)
            if not eligible:
                skipped.append({
                    "constituency": event.constituency, "stream": stream.value,
                    "phase": phase.value, "reason": why_not,
                })
                continue

            score = priority(event, state, now)
            if score <= 0.01:
                skipped.append({
                    "constituency": event.constituency, "stream": stream.value,
                    "phase": phase.value,
                    "reason": f"priority {score:.4f} below threshold "
                              f"(volatility={VOLATILITY[phase].get(stream, 0.0)}, "
                              f"urgency={urgency(phase, event.days_to_poll(now.date())):.2f})",
                })
                continue

            candidates_for_work.append(PlannedFetch(
                constituency=event.constituency, state=event.state, stream=stream,
                phase=phase, priority=score,
                estimated_requests=estimate_requests(stream, state),
                reason=(f"phase={phase.value}, days_to_poll={event.days_to_poll(now.date())}, "
                        f"gap={gap(state, now):.2f}, staleness={state.staleness_days(now):.1f}d"),
                verified_calendar=event.verified,
                myneta_slug=event.myneta_slug,
                myneta_constituency_id=event.myneta_constituency_id,
            ))

    candidates_for_work.sort(key=lambda p: p.priority, reverse=True)

    approved: list[PlannedFetch] = []
    deferred: list[PlannedFetch] = []
    spent = 0
    for item in candidates_for_work:
        if spent + item.estimated_requests <= budget.max_requests:
            approved.append(item)
            spent += item.estimated_requests
        else:
            deferred.append(item)

    return {
        "generated_at": now.isoformat(),
        "budget": {"max_requests": budget.max_requests, "delay_seconds": budget.delay_seconds},
        "planned_requests": spent,
        "estimated_runtime_minutes": round(budget.estimated_runtime_minutes(spent), 1),
        "approved": [p.to_dict() for p in approved],
        # Surfaced, never silently dropped — a truncated plan must look truncated.
        "deferred_over_budget": [p.to_dict() for p in deferred],
        "skipped": skipped,
        "unverified_calendar_warnings": [
            p.constituency for p in approved if not p.verified_calendar
        ],
    }


# --- Change detection ----------------------------------------------------

def record_fingerprint(records: list[dict]) -> str:
    """Stable hash over EXTRACTED FIELDS, deliberately not raw HTML.

    Verified reason (see module docstring, point 3): two back-to-back fetches
    of the same live MyNeta candidate page produce different bytes, because
    the site serves CSS with a rotating cache-buster (?r=1 / ?r=2) from
    different backends. A raw-HTML hash reports a change on every poll and
    makes change detection useless. Field-level hashing is immune to that,
    and to any other cosmetic template edit ADR makes.

    Volatile bookkeeping keys (fetch timestamps) are excluded for the same
    reason — otherwise every fetch trivially "changes" the fingerprint.
    """
    VOLATILE = {"fetched_at", "retrieved_at", "_fetch_ts"}
    normalized = []
    for r in sorted(records, key=lambda x: str(x.get("sourceUrl") or x.get("name") or "")):
        normalized.append({k: v for k, v in sorted(r.items()) if k not in VOLATILE})
    blob = json.dumps(normalized, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def count_missing_critical(records: list[dict]) -> dict[str, int]:
    """How many records lack each critical field — feeds the `gap` term."""
    out: dict[str, int] = {}
    for fname in CRITICAL_FIELDS:
        out[fname] = sum(1 for r in records if r.get(fname) in (None, "", []))
    return out


# --- Self-test (no network) ----------------------------------------------

if __name__ == "__main__":
    # Real dates for the three by-elections voting 2026-07-30, from the ECI
    # schedule as reported by PIB and carried by national outlets:
    # nominations closed 13 Jul, scrutiny 14 Jul, withdrawal 16 Jul,
    # poll 30 Jul, counting 3 Aug 2026.
    bankipur = ElectionEvent(
        constituency="Bankipur", state="Bihar",
        myneta_slug="Bihar2025", myneta_constituency_id=252,
        nomination_last=date(2026, 7, 13), scrutiny=date(2026, 7, 14),
        withdrawal_last=date(2026, 7, 16), poll=date(2026, 7, 30),
        counting=date(2026, 8, 3), verified=True,
        source="ECI schedule via PIB release 2245597",
    )
    digha = ElectionEvent(
        constituency="Digha", state="Bihar",
        myneta_slug="Bihar2025", myneta_constituency_id=163,
        poll=date(2025, 11, 11), counting=date(2025, 11, 14), verified=True,
        source="Bihar 2025 general election",
    )

    now = datetime(2026, 7, 26, 9, 0, tzinfo=timezone.utc)

    # 1. Phase boundaries across the whole lifecycle.
    assert bankipur.phase_on(date(2026, 7, 10)) is Phase.NOMINATION
    assert bankipur.phase_on(date(2026, 7, 14)) is Phase.SCRUTINY
    assert bankipur.phase_on(date(2026, 7, 15)) is Phase.WITHDRAWAL
    assert bankipur.phase_on(date(2026, 7, 20)) is Phase.CAMPAIGN
    assert bankipur.phase_on(date(2026, 7, 29)) is Phase.SILENCE
    assert bankipur.phase_on(date(2026, 7, 30)) is Phase.POLL_DAY
    assert bankipur.phase_on(date(2026, 8, 3)) is Phase.COUNTING
    assert bankipur.phase_on(date(2026, 8, 10)) is Phase.CONCLUDED
    assert digha.phase_on(date(2026, 7, 26)) is Phase.CONCLUDED

    # 2. The core claim: a live seat 4 days out must outrank a concluded one.
    live_state = TargetState("Bankipur", Stream.AFFIDAVIT,
                             last_fetched=datetime(2026, 7, 25, 11, 24, tzinfo=timezone.utc),
                             records_total=23, records_missing_critical={"criminalCount": 0})
    done_state = TargetState("Digha", Stream.AFFIDAVIT,
                             last_fetched=datetime(2026, 7, 1, tzinfo=timezone.utc),
                             records_total=11, records_missing_critical={})
    p_live = priority(bankipur, live_state, now)
    p_done = priority(digha, done_state, now)
    assert p_live > p_done, f"live seat must outrank concluded ({p_live} vs {p_done})"

    # 3. A missing criminal-case count must raise priority over a complete record.
    holey = TargetState("Bankipur", Stream.AFFIDAVIT,
                        last_fetched=datetime(2026, 7, 25, 11, 24, tzinfo=timezone.utc),
                        records_total=23, records_missing_critical={"criminalCount": 12})
    assert priority(bankipur, holey, now) > p_live, "incomplete record must outrank complete one"

    # 4. Politeness floor holds even at maximum priority.
    just_fetched = TargetState("Bankipur", Stream.AFFIDAVIT,
                               last_fetched=now - timedelta(hours=1), records_total=23)
    ok, why = is_eligible(bankipur, just_fetched, now)
    assert not ok and "min interval" in why, "politeness floor must block a too-recent refetch"

    # 5. Fingerprint ignores volatile keys but catches a real data change.
    recs_a = [{"name": "REKHA KUMARI", "criminalCount": 1, "fetched_at": "2026-07-25T11:24:00Z"}]
    recs_b = [{"name": "REKHA KUMARI", "criminalCount": 1, "fetched_at": "2026-07-26T09:00:00Z"}]
    recs_c = [{"name": "REKHA KUMARI", "criminalCount": 2, "fetched_at": "2026-07-25T11:24:00Z"}]
    assert record_fingerprint(recs_a) == record_fingerprint(recs_b), "timestamp must not count as a change"
    assert record_fingerprint(recs_a) != record_fingerprint(recs_c), "a real field change must be detected"

    # 6. Budget caps the plan and reports the overflow instead of hiding it.
    plan = build_plan(
        events=[bankipur, digha],
        states={("Bankipur", Stream.AFFIDAVIT): live_state, ("Digha", Stream.AFFIDAVIT): done_state},
        now=now, budget=PolitenessBudget(max_requests=30, delay_seconds=3.0),
    )
    assert plan["planned_requests"] <= 30
    assert plan["approved"], "expected at least one approved fetch four days before a poll"
    assert plan["approved"][0]["constituency"] == "Bankipur", "live seat must rank first"

    # 7. Backoff actually reduces priority for repeatedly-unchanged targets.
    quiet = TargetState("Bankipur", Stream.AFFIDAVIT,
                        last_fetched=datetime(2026, 7, 20, tzinfo=timezone.utc),
                        records_total=23, consecutive_unchanged=6)
    noisy = TargetState("Bankipur", Stream.AFFIDAVIT,
                        last_fetched=datetime(2026, 7, 20, tzinfo=timezone.utc),
                        records_total=23, consecutive_unchanged=0)
    assert priority(bankipur, quiet, now) < priority(bankipur, noisy, now)

    print("refresh_policy self-test passed.\n")
    print(f"Plan for {now.date()} (4 days before the Bankipur poll):")
    print(json.dumps(plan, indent=2)[:1400])
