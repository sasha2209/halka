/* party_symbols.js
 *
 * ECI-allotted election symbols, for showing voters the mark they will actually
 * look for on the EVM.
 *
 * WHY THIS FILE IS CAUTIOUS
 * -------------------------
 * A wrong symbol here is the most dangerous error this whole project could
 * make. Every other field — age, education, assets — is information a voter
 * weighs. The symbol is the thing they physically press. Showing a lotus next
 * to the wrong candidate could cause a real misvote, so this file never
 * guesses: a party either has a verified symbol or is explicitly marked
 * unverified, and the UI renders that difference plainly.
 *
 * WHAT "VERIFIED" MEANS HERE
 * --------------------------
 * The symbol is RESERVED for that party by the ECI nationally or in the
 * relevant state, and was confirmed against reporting or ECI-derived sources
 * during this project's research (2026-07-26). Reserved symbols are stable
 * across elections, which is what makes them safe to hard-code.
 *
 * WHAT IS DELIBERATELY NOT HERE
 * -----------------------------
 * Registered-but-unrecognised parties and independents do NOT have reserved
 * symbols. They are allotted a "free symbol" per election, per constituency,
 * from the ECI's free-symbols list — so the same party can carry different
 * symbols in different seats, and an independent's symbol is specific to that
 * one contest. Hard-coding those would be inventing facts. They resolve to
 * UNVERIFIED, and the UI tells the voter to check their ballot.
 *
 * ON THE GLYPHS
 * -------------
 * The emoji is an ILLUSTRATION, not the ballot artwork. Some are exact (lotus,
 * elephant, school bag, clock); others are approximations (the RJD's hurricane
 * lantern is not the same object as a red paper lantern). So the symbol's
 * OFFICIAL NAME is always rendered alongside the glyph, and the name — not the
 * picture — is the authoritative part. That ordering is deliberate: a voter who
 * reads "Lantern" and sees a lantern-ish glyph is correctly informed; one who
 * sees only an approximate picture might not be.
 */

const SYMBOL_UNVERIFIED = {
  name: null,
  glyph: "?",
  verified: false,
  note: "Symbol not confirmed for this party. Unrecognised parties and independents " +
        "are allotted a free symbol per constituency, so it can differ by seat — " +
        "check the ballot or the ECI candidate list for this constituency."
};

const PARTY_SYMBOLS = {
  // --- National parties: symbols reserved nationwide ---
  "BJP": {
    name: "Lotus", glyph: "🪷", verified: true,
    fullName: "Bharatiya Janata Party",
    source: "ECI reserved symbol (national party)"
  },
  "INC": {
    name: "Hand", glyph: "✋", verified: true,
    fullName: "Indian National Congress",
    source: "ECI reserved symbol (national party)"
  },
  "BSP": {
    name: "Elephant", glyph: "🐘", verified: true,
    fullName: "Bahujan Samaj Party",
    source: "ECI reserved symbol (national party)"
  },
  "CPI": {
    name: "Ears of Corn and Sickle", glyph: "🌾", verified: true,
    fullName: "Communist Party of India",
    source: "ECI reserved symbol (national party)"
  },
  "CPI(M)": {
    name: "Hammer, Sickle and Star", glyph: "☭", verified: true,
    fullName: "Communist Party of India (Marxist)",
    source: "ECI reserved symbol (national party)"
  },
  "NCP": {
    name: "Clock", glyph: "🕐", verified: true,
    fullName: "Nationalist Congress Party",
    source: "ECI reserved symbol (national party)"
  },
  "AITC": {
    name: "Flower and Grass", glyph: "🌿", verified: true,
    fullName: "All India Trinamool Congress",
    source: "ECI reserved symbol (national party)"
  },

  // --- State parties: reserved in the relevant state ---
  "RJD": {
    name: "Hurricane Lamp (Lantern)", glyph: "🏮", verified: true,
    fullName: "Rashtriya Janata Dal",
    source: "ECI reserved symbol (state party, Bihar & Jharkhand)",
    glyphCaveat: "Glyph is an approximation — the ballot symbol is a hurricane lamp."
  },
  "JDU": {
    name: "Arrow", glyph: "⬆️", verified: true,
    fullName: "Janata Dal (United)",
    source: "ECI reserved symbol (state party, Bihar)"
  },
  "CPI(ML)(L)": {
    name: "Flag with Three Stars", glyph: "🚩", verified: true,
    fullName: "Communist Party of India (Marxist–Leninist) Liberation",
    source: "ECI reserved symbol; contested on this symbol in Bihar & Jharkhand since 2019",
    glyphCaveat: "Glyph is an approximation — the ballot symbol is a flag bearing three stars."
  },

  // --- Registered party with a symbol allotted for this election cycle ---
  "Jan Suraaj Party": {
    name: "School Bag", glyph: "🎒", verified: true,
    fullName: "Jan Suraaj Party",
    source: "Allotted by the ECI for the Bihar 2025 assembly election",
    glyphCaveat: "Allotted for Bihar 2025 — a newly registered party's symbol is not " +
                 "reserved permanently and can change between elections."
  }

  // Everything below appears in this dataset but has NO confirmed symbol, and
  // is intentionally absent so it resolves to SYMBOL_UNVERIFIED rather than a
  // plausible-looking guess:
  //   Bharatiya Gan Warta Party, Bharatiya Momin Front, Jagrook Janta Party,
  //   Rashtriya Jansambhavna Party, Rashtriya Lok Janshakti Party,
  //   Right to Recall Party, The Plurals Party, Vocal India Party,
  //   Independent (free symbol, allotted per candidate per seat)
};

/* Resolve a party name to its symbol record. Matching is exact-then-normalised
 * rather than fuzzy: a fuzzy match that turns "Rashtriya Lok Janshakti Party"
 * into "Rashtriya Janata Dal" would attach the wrong ballot symbol to a real
 * candidate, which is precisely the failure this file exists to prevent. */
function partySymbol(party) {
  if (!party) return SYMBOL_UNVERIFIED;
  if (PARTY_SYMBOLS[party]) return PARTY_SYMBOLS[party];
  const norm = String(party).trim().toUpperCase().replace(/[\s.]/g, "");
  for (const key of Object.keys(PARTY_SYMBOLS)) {
    if (key.toUpperCase().replace(/[\s.]/g, "") === norm) return PARTY_SYMBOLS[key];
  }
  return SYMBOL_UNVERIFIED;
}
