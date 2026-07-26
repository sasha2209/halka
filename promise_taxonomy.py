"""
promise_taxonomy.py

A category system for Indian election promises, so a manifesto stops being a
wall of bullet points and becomes something a voter can compare across
candidates on the thing they personally care about.

WHY A FIXED TAXONOMY AND NOT FREE TAGS
--------------------------------------
The whole point is cross-candidate comparison: "what does each of these people
say about jobs?" That only works if every party's jobs pledge lands in the same
bucket. Free-form tags would give "employment", "jobs", "rozgar" and
"livelihood" as four separate columns, and the comparison silently breaks.

So the categories below are fixed, and MISC is a real destination rather than
an admission of failure — a genuinely novel pledge belongs there, visibly,
instead of being crammed into a category it doesn't fit.

HOW CATEGORIES WERE CHOSEN
--------------------------
From what Indian manifestos actually promise, not from a generic civic
template. Bihar 2025 is the worked example already in this project: the NDA and
Mahagathbandhan documents between them cover jobs, cash transfers to women,
reservation, pensions, electricity, housing, industry and prohibition. A
taxonomy without PROHIBITION would have dumped a defining Bihar issue into
MISC; one without WOMEN would have split the ₹2,500/month pledge and the
Lakhpati Didi pledge across unrelated buckets.

CLASSIFICATION IS ASSISTIVE, NOT AUTHORITATIVE
----------------------------------------------
`classify()` is keyword-based and returns a confidence with every guess. It
exists to draft, not to decide. Anything it isn't confident about is meant to
be reviewed by a person before it reaches a voter — consistent with the rest
of this project, where a machine's guess is never silently promoted to a fact.
`needs_review` on the result is the flag that carries that.

Self-test: `python3 promise_taxonomy.py` (no network).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Category:
    key: str
    label: str
    # Short, plain-language description. Shown in the UI as a tooltip, so it's
    # written for a voter, not for a developer.
    blurb: str
    # Emoji used as the category glyph. Deliberately emoji rather than custom
    # icons: they render identically without an asset pipeline, survive being
    # pasted into a WhatsApp forward (which is how this information actually
    # travels in India), and carry no party symbolism that could be mistaken
    # for a ballot mark.
    icon: str
    keywords: tuple[str, ...] = ()


CATEGORIES: tuple[Category, ...] = (
    Category(
        "jobs", "Jobs & employment",
        "Government jobs, private-sector employment, unemployment allowance, skills training.",
        "💼",
        ("job", "jobs", "employment", "unemployed", "unemployment", "rozgar", "naukri",
         "recruitment", "vacanc*", "skill", "training", "apprentice*", "livelihood",
         "self-employment", "startup", "entrepreneur"),
    ),
    Category(
        "education", "Education",
        "Schools, colleges, teachers, scholarships, fees, exam reform.",
        "📚",
        ("education", "school", "college", "university", "student", "teacher", "scholarship",
         "fee waiver", "syllabus", "exam", "literacy*", "anganwadi", "mid-day meal",
         "vidyalaya", "shiksha", "library"),
    ),
    Category(
        "health", "Health & healthcare",
        "Hospitals, doctors, insurance, medicines, maternal and child health.",
        "🏥",
        ("health", "hospital", "doctor", "nurse", "medical", "medicine", "clinic",
         "insurance", "ayushman", "maternal", "vaccination", "primary health",
         "phc", "swasthya", "malnutrition", "nutrition"),
    ),
    Category(
        "women", "Women & child welfare",
        "Cash transfers to women, safety, reservation for women, childcare, girl-child schemes.",
        "👩",
        ("women", "woman", "mahila", "behin", "didi", "girl", "daughter", "beti",
         "child care", "childcare", "creche", "widow", "dowry", "safety of women",
         "self-help group", "shg", "lakhpati"),
    ),
    Category(
        "agriculture", "Farmers & agriculture",
        "MSP, loan waivers, irrigation, crop insurance, fertiliser, mandis.",
        "🌾",
        ("farmer", "farm", "agricultur*", "kisan", "crop", "msp", "minimum support price",
         "irrigation", "fertiliser", "fertilizer", "mandi", "loan waiver", "harvest",
         "seed", "tractor", "dairy", "livestock", "fisher"),
    ),
    Category(
        "infrastructure", "Roads, power & water",
        "Roads, bridges, electricity, drinking water, sanitation, transport.",
        "🛣️",
        ("road", "bridge", "highway", "electricity", "power", "solar",
         "drinking water", "water supply", "sanitation", "toilet", "sewer*", "drain",
         "transport", "bus", "rail", "metro", "airport", "connectivity", "handpump"),
    ),
    Category(
        "housing", "Housing & land",
        "Housing schemes, land titles, slum redevelopment, homestead land.",
        "🏠",
        ("housing", "house", "awas", "makan", "slum", "land reform", "land title",
         "homestead", "patta", "shelter", "rent"),
    ),
    Category(
        "welfare", "Welfare & cash support",
        "Pensions, direct cash transfers, rations, subsidies for the poor and elderly.",
        "🤝",
        ("pension", "cash transfer", "direct benefit", "dbt", "ration", "subsid*",
         "old age", "elderly", "senior citizen", "bpl", "poverty", "free electricity",
         "free bus", "allowance", "financial assistance", "yojana", "old pension scheme"),
    ),
    Category(
        "social_justice", "Reservation & social justice",
        "Caste and community reservation, SC/ST/OBC/EBC welfare, minority rights.",
        "⚖️",
        ("reservation*", "quota", "scheduled caste", "scheduled tribe", "obc", "ebc",
         "backward class", "dalit", "adivasi", "tribal", "minority", "caste census",
         "social justice", "atrocit"),
    ),
    Category(
        "economy", "Industry & economy",
        "Industrial parks, investment, trade, small business, tourism, taxes.",
        "🏭",
        ("industr*", "factory", "investment", "manufactur*", "msme", "small business",
         "trade", "export", "tourism", "gst", "tax", "economic zone", "business",
         "market", "textile"),
    ),
    Category(
        "law_order", "Law, order & safety",
        "Policing, crime, women's safety enforcement, courts, communal harmony.",
        "🛡️",
        ("police", "crime", "law and order", "law & order", "security", "safety",
         "court", "justice delivery", "fir", "goonda", "mafia", "trafficking",
         "communal", "riot"),
    ),
    Category(
        "governance", "Governance & corruption",
        "Anti-corruption, transparency, service delivery, decentralisation, e-governance.",
        "🏛️",
        ("corruption", "transparen*", "accountab*", "lokayukta", "lokpal", "rti",
         "e-governance", "digital governance", "panchayat", "decentralis*",
         "bureaucra*", "administration", "grievance", "single window"),
    ),
    Category(
        "prohibition", "Liquor & prohibition",
        "Alcohol bans, lifting or reviewing prohibition, related enforcement.",
        "🚫",
        ("liquor", "alcohol", "prohibition", "sharab", "daru", "excise", "toddy"),
    ),
    Category(
        "environment", "Environment & climate",
        "Pollution, rivers, forests, flooding, climate resilience, clean energy.",
        "🌱",
        ("environment", "pollution", "river", "forest", "tree", "climate", "flood",
         "drought", "waste management", "clean air", "green", "wildlife", "ganga"),
    ),
    Category(
        "misc", "Other promises",
        "Real pledges that don't fit the categories above — kept visible rather than forced.",
        "📌",
        (),
    ),
)

CATEGORY_BY_KEY = {c.key: c for c in CATEGORIES}
MISC = CATEGORY_BY_KEY["misc"]

# Multi-word keywords are far stronger evidence than single words, so they're
# weighted higher. "minimum support price" is unambiguously agriculture;
# "market" on its own is barely a signal.
def _keyword_spans(text: str, kw: str) -> tuple[float, list[tuple[int, int]]]:
    """Weight and matched character spans for one keyword.

    A trailing '*' marks a deliberate stem ("agricultur*" catches
    agriculture/agricultural/agriculturist). Everything else is matched as a
    whole word. That distinction is load-bearing: without it, the single-word
    keyword "unit" (for "125 units of electricity") fires on "unity" and files
    a communal-harmony pledge under infrastructure. Real case, caught in test.
    """
    stem = kw.endswith("*")
    core = kw[:-1] if stem else kw
    if core not in text:
        return 0.0, []
    words = core.count(" ") + 1
    weight = 3.0 if words >= 3 else (2.0 if words == 2 else 1.0)
    if stem:
        pattern = rf"\b{re.escape(core)}"
    else:
        # Tolerate a simple plural. Manifestos are written in plurals almost
        # throughout — "50 lakh new houses", "10 industrial parks", "1 crore
        # jobs" — and strict whole-word matching sent "50 lakh new houses" to
        # MISC because the keyword was "house". Caught in test; it would have
        # quietly mis-filed a large share of every real manifesto.
        suffix = "" if core.endswith("s") else "(?:s)?"
        pattern = rf"\b{re.escape(core)}{suffix}\b"
    spans = [m.span() for m in re.finditer(pattern, text)]
    return (weight, spans) if spans else (0.0, [])


def _score_category(text: str, keywords: tuple[str, ...]) -> tuple[float, list[str]]:
    """Total evidence for one category, counting each stretch of text once.

    Overlapping keywords must not stack. "Old Pension Scheme restored" matches
    both "old pension scheme" (3.0) and "pension" (1.0); naively summing gives
    4.0 from a single phrase, which made a two-topic promise ("Reservation
    raised to 60%; Old Pension Scheme restored") score 0.88 confidence for
    welfare and skip human review — exactly the promise that most needed it.

    Longest keywords are consumed first, and any shorter keyword landing on
    already-counted characters is ignored. Confidence then reflects how much
    of the promise actually supports the category, not how many synonyms the
    keyword list happens to contain for one phrase.
    """
    scored: list[tuple[float, list[tuple[int, int]], str]] = []
    for kw in keywords:
        weight, spans = _keyword_spans(text, kw)
        if spans:
            scored.append((weight, spans, kw))
    # Longest/strongest first so the specific phrase claims the text.
    scored.sort(key=lambda t: (-t[0], -len(t[2])))

    consumed: list[tuple[int, int]] = []
    total = 0.0
    hits: list[str] = []
    for weight, spans, kw in scored:
        fresh = [s for s in spans if not any(s[0] < c[1] and c[0] < s[1] for c in consumed)]
        if not fresh:
            continue
        total += weight
        consumed.extend(fresh)
        hits.append(kw)
    return total, hits


@dataclass
class Classification:
    category: str
    confidence: float
    matched: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    needs_review: bool = True

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "confidence": round(self.confidence, 3),
            "matched": self.matched,
            "alternatives": self.alternatives,
            "needsReview": self.needs_review,
        }


def classify(promise: str) -> Classification:
    """Best-guess category for one promise, with confidence and runners-up.

    Returns MISC at zero confidence when nothing matches — the honest answer,
    and one a human reviewer can act on. Never invents a category to avoid
    an empty result.
    """
    text = promise.lower()
    scores: dict[str, float] = {}
    matched: dict[str, list[str]] = {}

    for cat in CATEGORIES:
        if cat.key == "misc":
            continue
        total, hits = _score_category(text, cat.keywords)
        if total > 0:
            scores[cat.key] = total
            matched[cat.key] = hits

    if not scores:
        return Classification(MISC.key, 0.0, [], [], needs_review=True)

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    best_key, best_score = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0.0

    # Confidence reflects both how much evidence there is and how cleanly the
    # winner beat the runner-up. A promise matching two categories equally is
    # genuinely ambiguous — often because it really does span both — and should
    # say so rather than pick one and look certain.
    margin = (best_score - runner_up) / best_score if best_score else 0.0
    evidence = min(1.0, best_score / 4.0)
    confidence = round(0.5 * evidence + 0.5 * margin, 3)

    return Classification(
        category=best_key,
        confidence=confidence,
        matched=matched[best_key],
        alternatives=[k for k, _ in ranked[1:3]],
        # 0.6 is a deliberately cautious bar: below it, a person looks at it.
        needs_review=confidence < 0.6,
    )


# Manifesto bullets routinely bundle several unrelated pledges into one line:
#   "Reservation raised to 60%; Old Pension Scheme restored"
#   "1 crore women to become Lakhpati Didi; free electricity up to 125 units;
#    50 lakh new houses"
# Categorising those as a unit is impossible in principle — the second example
# is genuinely three promises across three categories. Splitting first makes
# each clause cleanly classifiable, and reads better in the UI besides: a voter
# scanning "Roads, power & water" should see the electricity pledge on its own,
# not buried mid-sentence behind a women's-welfare pledge.
#
# Semicolons only. Splitting on "and" or commas would shred legitimate single
# promises ("roads, bridges and culverts in every ward" is one pledge), and a
# wrong split is worse than no split — it invents promises nobody made.
_CLAUSE_SPLIT = re.compile(r"\s*;\s*")


def split_promise(promise: str) -> list[str]:
    """Split a bundled manifesto bullet into individual pledges.

    Parenthetical attribution — "(NDA "Sankalp Patra," released 31 Oct 2025)" —
    is left attached to the clause it follows, since it's provenance for that
    pledge rather than a pledge of its own.
    """
    parts = [p.strip() for p in _CLAUSE_SPLIT.split(promise) if p.strip()]
    # A trailing fragment too short to be a real pledge is almost certainly a
    # continuation, not a promise; keep it joined rather than emitting a stub.
    merged: list[str] = []
    for part in parts:
        if merged and len(part) < 12:
            merged[-1] = merged[-1] + "; " + part
        else:
            merged.append(part)
    return merged or [promise.strip()]


def classify_manifesto(promises: list[str], split: bool = True) -> list[dict]:
    """Classify a manifesto. Bundled bullets are split into separate pledges
    by default; `source_text` preserves the original line so nothing looks
    fabricated when a voter compares against the published manifesto."""
    out = []
    for p in promises:
        clauses = split_promise(p) if split else [p]
        for clause in clauses:
            c = classify(clause)
            entry = {"text": clause, **c.to_dict()}
            if len(clauses) > 1:
                entry["source_text"] = p
            out.append(entry)
    return out


def group_by_category(classified: list[dict]) -> dict[str, list[dict]]:
    """Group classified promises by category, in the taxonomy's own order so
    every candidate's promise list reads in the same sequence — which is what
    makes side-by-side comparison possible."""
    grouped: dict[str, list[dict]] = {c.key: [] for c in CATEGORIES}
    for item in classified:
        grouped.setdefault(item["category"], []).append(item)
    return {k: v for k, v in grouped.items() if v}


def export_taxonomy_js() -> str:
    """Emit the taxonomy as JS for the single-file frontend, so the categories
    and their order are defined once here rather than duplicated by hand."""
    payload = [
        {"key": c.key, "label": c.label, "blurb": c.blurb, "icon": c.icon}
        for c in CATEGORIES
    ]
    return "const PROMISE_CATEGORIES = " + json.dumps(payload, indent=2, ensure_ascii=False) + ";"


# --- Self-test (no network) ----------------------------------------------

if __name__ == "__main__":
    # Real promises from the manifestos already in halka-prototype.html.
    NDA = [
        "1 crore jobs pledged over five years (NDA “Sankalp Patra,” released 31 Oct 2025)",
        "₹10 lakh assistance for Extremely Backward Classes, plus an EBC commission led by a retired Supreme Court judge",
        "10 new industrial parks / factories in every district",
        "1 crore women to become “Lakhpati Didi”; free electricity up to 125 units; 50 lakh new houses",
    ]
    MGB = [
        "Government job for one member of every family — law promised within 20 days of forming government",
        "₹2,500/month to women under the Mai-Behin Maan Yojana",
        "Reservation raised to 60%; Old Pension Scheme restored",
        "Liquor prohibition law to be reviewed",
    ]

    nda_c = classify_manifesto(NDA)
    mgb_c = classify_manifesto(MGB)

    def cat_of(classified, marker):
        """Look promises up by content, not position — splitting changes indices."""
        hits = [c for c in classified if marker.lower() in c["text"].lower()]
        assert len(hits) == 1, f"expected exactly one promise matching {marker!r}, got {len(hits)}"
        return hits[0]["category"]

    assert cat_of(nda_c, "1 crore jobs") == "jobs"
    assert cat_of(nda_c, "Extremely Backward Classes") == "social_justice"
    assert cat_of(nda_c, "industrial parks") == "economy"
    assert cat_of(mgb_c, "Government job for one member") == "jobs"
    assert cat_of(mgb_c, "Mai-Behin Maan Yojana") == "women"
    assert cat_of(mgb_c, "Liquor prohibition") == "prohibition"

    # Cross-candidate comparison is the whole point: both coalitions' jobs
    # pledges must land in the same bucket despite completely different wording.
    assert cat_of(nda_c, "1 crore jobs") == cat_of(mgb_c, "Government job for one member") == "jobs"

    # Overlapping keywords must not stack. "Old Pension Scheme restored" matches
    # both "pension" and "old pension scheme"; summing both gave 4.0 from one
    # phrase and inflated confidence.
    _score, hits = _score_category("old pension scheme restored", CATEGORY_BY_KEY["welfare"].keywords)
    assert hits == ["old pension scheme"], f"overlapping keywords must count once, got {hits}"

    # Bundled bullets split into separate pledges, so each lands in its own
    # category cleanly instead of being an unclassifiable two-topic blob.
    split = classify_manifesto(["Reservation raised to 60%; Old Pension Scheme restored"])
    assert len(split) == 2, f"semicolon-joined pledges must split, got {split}"
    assert {s["category"] for s in split} == {"social_justice", "welfare"}, split
    assert all(s["source_text"].startswith("Reservation raised") for s in split), \
        "split clauses must retain the original manifesto line as provenance"

    # The three-part NDA bullet is the strongest case for splitting.
    triple = classify_manifesto(["1 crore women to become Lakhpati Didi; free electricity up to 125 units; 50 lakh new houses"])
    assert len(triple) == 3, triple
    # "free electricity" sits in WELFARE deliberately — as a subsidy/benefit,
    # which is how a voter encounters it — rather than under power infrastructure.
    # Both readings are defensible; the taxonomy commits to one so the same
    # pledge lands in the same bucket for every party, which is what makes the
    # cross-candidate comparison work at all.
    assert [t["category"] for t in triple] == ["women", "welfare", "housing"], \
        [t["category"] for t in triple]

    # Plurals must match their singular keyword — "50 lakh new houses" went to
    # MISC before this was handled, and manifestos are written almost entirely
    # in plurals.
    assert classify("50 lakh new houses").category == "housing"
    assert classify("10 new industrial parks in every district").category == "economy"
    assert classify("Support for farmers and their crops").category == "agriculture"

    # A real single promise containing commas and "and" must NOT be split.
    assert len(split_promise("Roads, bridges and culverts in every ward")) == 1

    # Nothing recognisable → MISC at zero confidence, flagged. Never a bluff.
    odd = classify("A statue of the founder will be erected in the town square")
    assert odd.category == "misc" and odd.confidence == 0.0 and odd.needs_review, odd.to_dict()

    # Whole-word matching: "unity" must not trigger the electricity "unit" keyword.
    assert classify("Promoting communal unity and brotherhood").category != "infrastructure"

    grouped = group_by_category(nda_c + mgb_c)
    assert "jobs" in grouped and len(grouped["jobs"]) == 2, grouped.get("jobs")

    review_count = sum(1 for c in nda_c + mgb_c if c["needsReview"])

    print("promise_taxonomy self-test passed.")
    print(f"  {len(CATEGORIES)} categories; {len(nda_c + mgb_c)} real promises classified; "
          f"{review_count} flagged for human review.\n")
    for key, items in grouped.items():
        cat = CATEGORY_BY_KEY[key]
        print(f"  {cat.icon}  {cat.label}")
        for it in items:
            mark = "?" if it["needsReview"] else " "
            print(f"     {mark} [{it['confidence']:.2f}] {it['text'][:74]}")
