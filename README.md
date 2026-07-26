# Halka

Know who's on your ballot, before you mark it.

Candidate credentials, sworn ECI declarations and party promises for Indian
elections — sourced, cited, and never fabricated. Open `halka-app.html` in a
browser; it has no build step and no dependencies at runtime.

---

## What's real right now

Three constituencies, all with live-fetched affidavit data:

| Seat | State | Status | Candidates |
|---|---|---|---|
| Bankipur | Bihar | By-poll, voting 30 Jul 2026 | 23 of 23, complete |
| Datia | Madhya Pradesh | By-poll, voting 30 Jul 2026 | 18 |
| Manjalpur | Gujarat | By-poll, voting 30 Jul 2026 | 2 (straight INC–BJP fight) |
| Digha | Bihar | Concluded Nov 2025 | 11, hand-researched |

Every candidate record carries its own MyNeta affidavit URL. Nothing is
inferred, and "not recorded" is a permanent, valid state that is never quietly
converted into a zero.

---

## The refresh system

The scheduling problem is not "how often do we scrape." It is **"which single
fetch, right now, most improves what a voter about to vote actually knows."**

### Two stages, deliberately asymmetric

```
calendar_discovery.py   ~1 request per state    what elections exist
refresh_policy.py       0 requests (pure)       what's worth fetching now
halka_refresh.py        budgeted                do it, carefully
```

Discovering that nothing changed across India costs about **30 requests**.
Blindly re-scraping every seat costs about **100,000**. That ratio is the whole
argument for event-driven refresh.

### How priority is decided

```
value = urgency × volatility × gap
```

- **urgency** — how much a voter needs this *now*. Peaks in the final fortnight,
  collapses the moment polls close. Nobody can un-cast a ballot.
- **volatility** — how likely the data actually changed. Affidavits are frozen
  outside a nomination window and change daily inside one. Same field, two
  orders of magnitude difference, decided purely by the calendar.
- **gap** — how deficient our record is. A missing criminal-case count outranks
  a missing profession, because it is the highest-stakes field in the dataset.

Multiplying rather than adding matters: if any factor is ~0 the fetch is
worthless, and the arithmetic says so without a special case.

On top of that: a **politeness floor** (minimum interval per phase) that a high
score cannot override, a **hard request budget** per run, and **backoff** for
targets that keep returning identical data.

### Election lifecycle

`DORMANT → ANNOUNCED → NOMINATION → SCRUTINY → WITHDRAWAL → CAMPAIGN → SILENCE
→ POLL_DAY → COUNTING → CONCLUDED`

Each phase sets its own per-stream volatility and minimum interval. Four days
before a poll the system correctly prioritises **news** over **affidavits** —
the candidate list locked at the withdrawal deadline, so only coverage moves.

---

## Constraints this was built around

All verified live, not assumed:

1. **myneta.info is reachable**, and its `robots.txt` only disallows
   `*printer=true` / `*print=true` — not the pages used here.
2. **eci.gov.in returns 403** to automated requests, browser User-Agent
   included. The calendar therefore comes from MyNeta's own index pages, which
   label every seat with its polling date, plus a human-verified file for
   nomination/scrutiny/withdrawal dates that MyNeta doesn't publish.
3. **MyNeta sends no ETag or Last-Modified** and ignores `If-Modified-Since`
   (returns a full 200 + 98KB). There is no cheap "did it change?" probe, which
   is exactly why the budget exists.
4. **Raw-HTML hashing does not work.** Two back-to-back fetches of the same page
   differ, because CSS is served with a rotating cache-buster (`?r=1` / `?r=2`)
   from different backends. Change detection hashes **extracted fields**.
5. **MyNeta's `constituency_id` is not the ECI constituency number.** Datia is
   ECI 22 but MyNeta 234. Every ID here was confirmed by fetching the page.

---

## Party symbols

The most dangerous possible error in this app. Every other field is information
a voter weighs; the symbol is the thing they physically press.

So `party_symbols.js` never guesses. A party either has an **ECI-reserved
symbol** (verified — lotus, hand, elephant, lantern, arrow, flag with three
stars, school bag…) or is shown as **"symbol unconfirmed"** with an explanation.
Unrecognised parties and independents get a *free symbol allotted per
constituency*, so the same party can carry different symbols in different seats
— hard-coding those would be inventing facts.

Matching is exact-then-normalised, never fuzzy: a fuzzy match turning
"Rashtriya Lok Janshakti Party" into "Rashtriya Janata Dal" would attach the
wrong ballot symbol to a real person.

The emoji is an **illustration**; the symbol's official **name** is always shown
alongside it and is the authoritative part.

---

## Promises

15 fixed categories (jobs, education, health, women, agriculture,
infrastructure, housing, welfare, social justice, economy, law & order,
governance, prohibition, environment, misc), chosen from what Indian manifestos
actually promise — a taxonomy without **prohibition** would have dumped a
defining Bihar issue into misc.

Categories are fixed rather than free-form because the whole point is
cross-candidate comparison: "what does each of these people say about jobs?"
only works if every party's jobs pledge lands in the same bucket.

Bundled bullets are split on semicolons first — *"Reservation raised to 60%;
Old Pension Scheme restored"* is two pledges in two categories and is
unclassifiable as a unit. Classification is **assistive, not authoritative**:
every guess carries a confidence, and anything below the bar renders a visible
`category unsure` flag rather than being quietly accepted.

---

## The interface

- **Candidate cards** — ballot number, party symbol, at-a-glance chips for
  criminal cases / age / declared assets.
- **Compare all** — every candidate, every parameter, one sortable matrix.
  Replaces an earlier two-candidate limit that forced a voter facing 23 names
  into dozens of pairwise comparisons. It **sorts but never scores**: there is
  no computed "best candidate" anywhere, because weighing criminal cases
  against education is a values judgment that belongs to the voter.
  Unknowns sink to the bottom in both sort directions — sorting a missing value
  as zero would put every unparsed candidate at the "cleanest" end of the
  criminal-cases column.
- **Compare promises** — pick a topic, see every manifesto side by side,
  including who has said nothing. Candidates with no manifesto are named, not
  hidden: "made no written promises" is a real fact about a candidate.

---

## Running it

```bash
python3 halka_refresh.py                 # dry run — plan only, no network
```

```bash
python3 halka_refresh.py --execute --budget 200 --delay 3.0
```

```bash
python3 calendar_discovery.py --states Bihar2025 MadhyaPradesh2023 Gujarat2022
```

```bash
python3 build_app.py                     # regenerate halka-app.html
```

Every module has an offline self-test — run the file with no arguments (or
`--self-test`). They cover real captured MyNeta markup, so they fail if the
site's template drifts rather than silently producing malformed records.

```bash
python3 myneta_scraper.py && python3 refresh_policy.py && python3 promise_taxonomy.py
```

---

## Before turning on the schedule

`.github/workflows/run-scraper.yml` has its `schedule:` block **commented out on
purpose**. `workflow_dispatch` works, so it is genuinely runnable — just not
running unattended against a nonprofit's servers yet.

`ADR-permission-email-DRAFT.md` is written but **not sent**. Worth noting the
ask is now much smaller than it was: this pipeline fetches candidate data only
during an active election window, for the affected seats, rather than polling
everything daily.

---

## Files

| File | What it is |
|---|---|
| `halka-app.html` | The app. Generated — edit the sources, not this. |
| `refresh_policy.py` | Scheduling brain. Pure functions, no I/O. |
| `calendar_discovery.py` | Cheap election-calendar poll. |
| `halka_refresh.py` | Executor: plan → fetch → change-detect → write. |
| `myneta_scraper.py` | Fetch + parse one constituency. |
| `promise_taxonomy.py` | 15-category promise classifier. |
| `party_symbols.js` | ECI symbols. Verified-or-nothing. |
| `build_app.py` | Assembles the app; merges scraped + researched records. |
| `election_calendar_curated.json` | Human-verified ECI dates. Wins on conflict. |
| `data/` | Fetched candidate records + `changelog.jsonl`. |

Build inputs prefixed `_` (`_ui_shell.html`, `_ui_code.js`, `_candidate_data.js`)
are consumed by `build_app.py`.
