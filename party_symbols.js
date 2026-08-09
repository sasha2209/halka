/* party_symbols.js
 *
 * ECI-allotted election symbols, shown as the actual real image of the symbol
 * — the mark a voter looks for on the EVM — not an approximation of one.
 *
 * WHY THIS FILE IS CAUTIOUS
 * -------------------------
 * A wrong symbol here is the most dangerous error this whole product could
 * make. Every other field — age, education, assets — is information a voter
 * weighs. The symbol is the thing they physically press. So this file never
 * substitutes a stand-in picture for the real one: a party either has a
 * verified real image of its actual reserved symbol, or the app plainly says
 * the symbol isn't confirmed. Nothing in between.
 *
 * WHAT "VERIFIED" MEANS HERE
 * --------------------------
 * The symbol is RESERVED for that party by the ECI, and the image is the
 * real published symbol — sourced from Wikimedia Commons, checked by
 * actually looking at each image before use (not just trusting a filename),
 * and license-cleared for reuse. See assets/symbols/SOURCES.md for exactly
 * which file came from where, and the one case (BSP) where the obvious
 * top search result was rejected because it was the party's colored logo,
 * not the black-and-white symbol that actually appears on a ballot.
 *
 * WHAT IS DELIBERATELY NOT HERE
 * -----------------------------
 * 1. Registered-but-unrecognised parties and independents. They're allotted
 *    a "free symbol" per election, per constituency — the same party can
 *    carry different symbols in different seats, so hard-coding one here
 *    would show a real voter the wrong mark for their specific ballot.
 * 2. Jan Suraaj Party's "School Bag" symbol. It's real (ECI-allotted, 2025)
 *    but no verified image of it could be found anywhere public as of
 *    2026-07-27. Rather than draw one, this app says so.
 *
 * Both cases resolve to SYMBOL_UNVERIFIED, which tells a voter to check
 * their own ballot instead of showing them a picture that might be wrong.
 *
 * IMAGE_MAP is filled in at build time (build_app.py) with base64 data URIs
 * of the real source files, so the shipped app is one self-contained file
 * with no external image requests.
 */

const SYMBOL_UNVERIFIED = {
  name: null,
  image: null,
  verified: false,
  note: "This party's symbol isn't confirmed. Parties that aren't nationally " +
        "recognised, and independents, get a different symbol assigned for each " +
        "constituency — so please check your own ballot paper or EVM for the exact mark."
};

/* IMAGE_MAP: logical key -> base64 data URI. Placeholder strings below are
 * replaced by build_app.py, which reads the real files out of
 * assets/symbols/ and inlines them. If you're reading this file directly
 * (not the built halka-app.html), these placeholders are literally what's
 * here — run build_app.py to get an app with real images. */
const SYMBOL_IMAGES = {
  bjp_lotus: "__IMG_bjp_lotus__",
  inc_hand: "__IMG_inc_hand__",
  bsp_elephant: "__IMG_bsp_elephant__",
  cpi_corn_sickle: "__IMG_cpi_corn_sickle__",
  cpim_hammer_sickle_star: "__IMG_cpim_hammer_sickle_star__",
  ncp_clock: "__IMG_ncp_clock__",
  aitc_flower_grass: "__IMG_aitc_flower_grass__",
  rjd_lantern: "__IMG_rjd_lantern__",
  jdu_arrow: "__IMG_jdu_arrow__",
  cpiml_l_flag_three_stars: "__IMG_cpiml_l_flag_three_stars__"
};

const PARTY_SYMBOLS = {
  // --- National parties: symbols reserved nationwide ---
  "BJP": {
    name: "Lotus", image: "bjp_lotus", verified: true,
    fullName: "Bharatiya Janata Party",
    source: "Wikimedia Commons, CC BY-SA 3.0 — see assets/symbols/SOURCES.md"
  },
  "INC": {
    name: "Hand", image: "inc_hand", verified: true,
    fullName: "Indian National Congress",
    source: "Wikimedia Commons, public domain (India) — see assets/symbols/SOURCES.md"
  },
  "BSP": {
    name: "Elephant", image: "bsp_elephant", verified: true,
    fullName: "Bahujan Samaj Party",
    source: "Wikimedia Commons, CC BY-SA 3.0 — see assets/symbols/SOURCES.md",
    note: "The black-and-white ballot rendering, not BSP's own colored party logo."
  },
  "CPI": {
    name: "Ears of Corn and Sickle", image: "cpi_corn_sickle", verified: true,
    fullName: "Communist Party of India",
    source: "Wikimedia Commons, CC BY-SA 3.0 — see assets/symbols/SOURCES.md"
  },
  "CPI(M)": {
    name: "Hammer, Sickle and Star", image: "cpim_hammer_sickle_star", verified: true,
    fullName: "Communist Party of India (Marxist)",
    source: "Wikimedia Commons, CC BY-SA 4.0 — see assets/symbols/SOURCES.md"
  },
  "NCP": {
    name: "Clock", image: "ncp_clock", verified: true,
    fullName: "Nationalist Congress Party",
    source: "Wikimedia Commons, CC BY-SA 4.0 — see assets/symbols/SOURCES.md"
  },
  "AITC": {
    name: "Flowers and Grass", image: "aitc_flower_grass", verified: true,
    fullName: "All India Trinamool Congress",
    source: "Wikimedia Commons, CC BY-SA 3.0 — see assets/symbols/SOURCES.md"
  },

  // --- State parties: reserved in the relevant state ---
  "RJD": {
    name: "Hurricane Lamp", image: "rjd_lantern", verified: true,
    fullName: "Rashtriya Janata Dal",
    source: "Wikimedia Commons, CC BY-SA 4.0 — see assets/symbols/SOURCES.md"
  },
  "JDU": {
    name: "Arrow", image: "jdu_arrow", verified: true,
    fullName: "Janata Dal (United)",
    source: "Wikimedia Commons, CC BY-SA 3.0 / GFDL — see assets/symbols/SOURCES.md"
  },
  "CPI(ML)(L)": {
    name: "Flag with Three Stars", image: "cpiml_l_flag_three_stars", verified: true,
    fullName: "Communist Party of India (Marxist–Leninist) Liberation",
    source: "Wikimedia Commons, CC BY-SA 4.0 — see assets/symbols/SOURCES.md"
  }

  // Jan Suraaj Party's real symbol (School Bag) is deliberately absent — see
  // the file header. It resolves to SYMBOL_UNVERIFIED, not a drawn stand-in.
  //
  // Everything else appearing in this dataset has NO reserved symbol at all —
  // Bharatiya Gan Warta Party, Bharatiya Momin Front, Jagrook Janta Party,
  // Rashtriya Jansambhavna Party, Rashtriya Lok Janshakti Party, Right to
  // Recall Party, The Plurals Party, Vocal India Party, and every Independent
  // (free symbol, allotted per candidate per seat).
};

/* Resolve a party name to its symbol record, with the image data URI already
 * attached. Matching is exact-then-normalised, never fuzzy: turning "Rashtriya
 * Lok Janshakti Party" into "Rashtriya Janata Dal" would attach the wrong
 * ballot symbol to a real candidate, which is exactly what this file exists
 * to prevent. */
function partySymbol(party) {
  const resolve = (rec) => rec.image ? { ...rec, image: SYMBOL_IMAGES[rec.image] } : rec;
  if (!party) return SYMBOL_UNVERIFIED;
  if (PARTY_SYMBOLS[party]) return resolve(PARTY_SYMBOLS[party]);
  const norm = String(party).trim().toUpperCase().replace(/[\s.]/g, "");
  for (const key of Object.keys(PARTY_SYMBOLS)) {
    if (key.toUpperCase().replace(/[\s.]/g, "") === norm) return resolve(PARTY_SYMBOLS[key]);
  }
  return SYMBOL_UNVERIFIED;
}
