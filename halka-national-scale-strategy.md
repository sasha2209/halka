# Halka at national scale: a strategy for real, sourced, continuously-refreshed candidate data

This is the plan for taking Halka from two hand-researched constituencies (Digha, Bankipur) to real coverage across India's 543 Lok Sabha and roughly 4,100 state assembly seats — without ever fabricating a data point. It assumes the schema and UX already validated in the prototype; this document is about the pipeline behind it.

## 1. Reframe "real-time" before designing for it

Not everything about a candidate changes at the same speed, so a single refresh promise for all of it would either waste effort or mislead people. The honest design has different data types on different clocks:

- **Affidavits** are filed once per nomination window and are then essentially static — except during the window itself, when candidates can be swapped (as happened in Bankipur days before filing).
- **Manifestos** are published once per election cycle and almost never revised.
- **News** is genuinely continuous, but overwhelmingly concentrated on a small number of high-profile races — most candidates generate no coverage at all, as the Digha research showed directly.
- **Results** are only live in the narrow sense — updated in rounds, as returning officers upload Form 20 — on counting day itself.
- **Legislator track record** (attendance, bills, questions raised) updates on a parliamentary/assembly session cadence, a handful of times a year.

Trying to poll all of this on one uniform "real-time" schedule would mean hammering ADR's servers checking affidavits that haven't changed in months, while still being too slow to catch a candidate substitution the day it happens. The fix is a tiered refresh model (Section 4), not a faster uniform one.

## 2. Data sources: extend the existing ecosystem instead of rebuilding it

India already has a real civic-tech data ecosystem for this. The strategic decision that matters most is building *on* it rather than duplicating it from scratch — that's faster, more reliable, and doesn't add unnecessary scraping load to organizations already doing this work.

| Data type | Best source | Nature | Status |
|---|---|---|---|
| Candidate affidavits (current cycle) | [ADR / MyNeta](https://www.myneta.info) | Structured, per-candidate, per-constituency URLs | Secondary — sourced by ADR from the ECI |
| Raw affidavit scans | [affidavitarchive.nic.in](https://affidavitarchive.nic.in) (ECI) | Scanned PDFs, needs OCR | Primary, authoritative |
| Historical affidavits/results (2004 onward) | [TCPD LokDhaba](https://lokdhaba.ashoka.edu.in) (Ashoka University), [datameet/india-election-data](https://github.com/datameet/india-election-data) | Pre-built, structured, downloadable | Secondary, already solved |
| Live counting-day results | [results.eci.gov.in](https://results.eci.gov.in) | Round-by-round, Form 20 based | Primary, authoritative |
| Sitting legislator performance | [PRS Legislative Research](https://prsindia.org) | Attendance, bills, questions asked | Secondary, well-established think tank |
| Party manifestos | Party websites/PDFs | Low volume — roughly 50–100 parties nationally | Primary |
| News | News APIs, scheduled search | Unstructured, needs per-candidate querying | Primary via outlets |
| Election calendar | ECI notifications ([eci.gov.in](https://www.eci.gov.in)) | Phases, nomination windows, by-poll triggers | Primary, authoritative |

ADR has no public API, but their own FAQ says they welcome direct contact for research use, and organizations like LokDhaba have already built structured, citable datasets on top of their affidavit archive going back over 20 years. The realistic path is: request data access from ADR directly for the current cycle, lean on LokDhaba/datameet for everything historical, and reserve direct ECI-archive scraping plus OCR for the gap — candidates ADR hasn't processed yet, exactly the scenario the OCR pipeline from earlier in this project was built for.

## 3. Architecture: five layers

1. **Election calendar registry.** The master list of every constituency plus the live ECI election schedule — phases, nomination windows, by-poll triggers. This is the clock that drives everything else: a by-poll announcement (like Bankipur's) should automatically open an ingestion window for that one seat, not require someone to notice and point the system at it manually.
2. **Structured ingestion.** Pulls affidavit data from ADR/MyNeta (or LokDhaba/datameet mirrors for historical data), falls back to the raw ECI archive plus OCR when a candidate isn't on ADR yet, and pulls sitting-legislator track record from PRS.
3. **Unstructured ingestion (news).** Scheduled, per-candidate search jobs, prioritized by the tiered cadence below, deduplicated, and stored with source and timestamp — never full article text, only citable links and short excerpts, consistent with standard copyright practice.
4. **Provenance and verification layer.** The part that actually prevents fabrication — detailed in Section 5.
5. **Serving layer.** The API the Halka app queries: constituency lookup by name, PIN code, or geolocation; versioned candidate records so trends (like an asset trajectory across three elections) keep working as new data arrives.

## 4. Refresh cadence: tiered, not uniform

| Data type | How often it actually changes | Recommended refresh |
|---|---|---|
| Affidavits, outside a nomination window | Essentially never | Monthly (catches corrections) |
| Affidavits, during a nomination window | Can change daily — withdrawals, substitutions | Daily |
| Manifestos | Once, rarely revised | Weekly during campaign season, dormant otherwise |
| News, high-profile/competitive races | Continuous | Every few hours |
| News, the long tail of candidates | Sparse to none | Weekly |
| Legislator performance | Per session | A few times a year |
| Live results | Minutes — but only on one day | Every few minutes, counting day only |
| Election calendar | Rare but high-impact | Daily check against ECI notifications |

## 5. What actually prevents fabrication, structurally

This can't be a matter of trying hard — it needs to be enforced by the data model itself:

- **Every field carries its source URL and retrieval timestamp**, shown in the UI exactly as in the prototype. This is a schema requirement, not a display choice, so it survives scaling instead of getting quietly dropped under time pressure.
- **No field is ever backfilled with an inferred value.** "Not available" is a permanent, valid state — as with Neeraj Sinha's missing asset figures in the Bankipur build — never a placeholder waiting to be guessed later.
- **Cross-source disagreement is flagged, never silently resolved.** The Divya Gautam BPSC detail is the template: show both versions and say so, rather than picking one.
- **A visible correction-request channel**, modeled on ADR's own, reviewed by a human before anything changes.
- **Ongoing human QA sampling**, weighted toward high-profile races and anything OCR-derived, with an error rate tracked over time as an operating metric — not a one-time launch check.

## 6. Rollout: follow the election calendar, not a uniform national push

- **Phase 1 — one live state.** Build the full pipeline end-to-end for whichever state has an election or by-poll window open right now, at real scale (hundreds of candidates), not demo scale.
- **Phase 2 — the next 6–12 months of the calendar.** Expand state by state, prioritized by what's actually coming up. There's no value in "freshening" a state that just voted and won't vote again for years.
- **Phase 3 — steady-state national coverage**, plus the less glamorous ongoing work: tracking defections, by-polls, and court case status changes between elections — the part that actually keeps the data honest over time, illustrated already by Ritesh Ranjan Singh's party switch and Bankipur's own by-poll trigger.

## 7. What this actually costs

This is comparable in scope to what ADR has built over roughly 20 years, or what an academic effort like TCPD/LokDhaba represents — not a weekend build. The infrastructure (scraping/ETL compute, storage, a news API subscription) is the cheap part. The expensive part is the human verification and correction workflow, which can't be automated away given what's at stake in being wrong about a real person's criminal record. Realistically, this is either a partnership with an existing player like ADR or TCPD rather than a duplicate build, or a funded, multi-person, multi-month engineering effort — not something to scope as a side project.

**Concrete next step:** pick one constituency currently in an active nomination window and build Phase 1 for that single seat, end to end — calendar trigger, structured ingestion, news ingestion, provenance layer, correction channel — before touching a second seat. That proves the pipeline the same way Digha and Bankipur proved the schema: for real, not at demo scale.
