/* ---------------------------------------------------------------------------
 * UI layer
 * ------------------------------------------------------------------------- */

let currentKey = null, expandedId = null, activeTab = {}, activeCat = 'all';
let matrixSort = { col: 'sno', dir: 1 };

function toggleAbout(){ document.getElementById('aboutPanel').classList.toggle('open'); }
function currentCandidates(){ return currentKey ? CONSTITUENCIES[currentKey].candidates : []; }
function esc(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

/* Parse a declared-asset string into a number for the comparison bars.
 *
 * Returns null — not 0 — when there is no figure. That distinction is
 * load-bearing: "Not available in this data pull" means we don't know, while
 * "Nil" means the candidate declared nothing. Collapsing the first into zero
 * would rank an unknown candidate as the poorest on the ballot, which is a
 * fabricated fact about a real person. The matrix renders the two differently
 * and sorts unknowns to the end regardless of direction. */
function parseAmount(str){
  if (str == null) return null;
  const s = String(str);
  if (/^\s*nil\s*$/i.test(s)) return 0;
  if (/not available|not captured|not researched/i.test(s)) return null;
  const m = s.replace(/[ \s]/g, '').match(/(?:Rs|₹)?([\d,]{4,})/);
  if (!m) return null;
  const n = Number(m[1].replace(/,/g, ''));
  return Number.isFinite(n) ? n : null;
}

function fmtAmount(str){
  const n = parseAmount(str);
  if (n === null) return null;
  if (n === 0) return 'Nil';
  if (n >= 1e7) return '₹' + (n / 1e7).toFixed(2).replace(/\.00$/, '') + ' Cr';
  if (n >= 1e5) return '₹' + (n / 1e5).toFixed(1).replace(/\.0$/, '') + ' L';
  return '₹' + n.toLocaleString('en-IN');
}

/* Party symbol chip. The symbol NAME is always rendered — the glyph is an
 * illustration and the name is the authoritative part. See party_symbols.js. */
/* Renders the ACTUAL symbol image (never an emoji stand-in). The name is
 * always shown alongside the picture — for a party with no confirmed image,
 * that's the honest "symbol not confirmed" state instead of a guessed glyph. */
function symChip(party, opts){
  const sym = partySymbol(party);
  const showName = !opts || opts.showName !== false;
  if (!sym.verified || !sym.image){
    return '<span class="sym unverified" title="' + esc(SYMBOL_UNVERIFIED.note) + '">' +
           '<span class="g">—</span>' + (showName ? t('symbolUnconfirmed') : '') + '</span>';
  }
  const title = sym.name + (sym.note ? ' — ' + sym.note : '');
  return '<span class="sym" title="' + esc(title) + '">' +
         '<img class="g" src="' + sym.image + '" alt="' + esc(sym.name) + ' symbol">' +
         (showName ? esc(sym.name) : '') + '</span>';
}

function catByKey(key){ return PROMISE_CATEGORIES.find(c => c.key === key) || { key:key, label:key, icon:'📌', blurb:'' }; }

/* Promises for a candidate, from the categorised manifesto data. Candidates
 * whose party has no published manifesto correctly get an empty list — the UI
 * says so explicitly rather than showing a blank panel. */
function promisesFor(cand){
  if (!cand.manifestoKey || !CATEGORIZED_PROMISES[cand.manifestoKey]) return [];
  return CATEGORIZED_PROMISES[cand.manifestoKey];
}

function onHalkaChange(val){
  const area = document.getElementById('resultArea');
  expandedId = null; currentKey = null;
  if (val === ''){
    area.innerHTML = '';
    document.getElementById('topBanner').textContent = t('bannerDefault');
    return;
  }
  if (val === 'other'){
    area.innerHTML = '<div class="empty-state">We don\'t have this constituency loaded yet.<br>' +
      'The three constituencies below are live right now — support for more is on the way.</div>';
    return;
  }
  currentKey = val;
  document.getElementById('topBanner').textContent = CONSTITUENCIES[val].banner;
  matrixSort = { col:'sno', dir:1 };
  renderList();
}

function renderList(){
  const c = CONSTITUENCIES[currentKey], list = c.candidates;
  let html = '<div class="actions">' +
    '<button class="action-btn" onclick="openMatrix()">▦ ' + t('compareAll') + ' ' + list.length + '</button>' +
    '<button class="action-btn secondary" onclick="openPromises()">📋 ' + t('comparePromises') + '</button>' +
    '</div>';
  html += '<div class="list-meta"><span>' + list.length + ' ' + t('candidatesWord') + '</span><span>' + esc(c.label) + '</span></div>';
  if (c.note) html += '<div class="election-note">' + c.note + '</div>';

  list.forEach(cand => {
    const isOpen = expandedId === cand.id;
    html += '<div class="card' + (isOpen ? ' expanded' : '') + '" id="card-' + cand.id + '">' +
      '<div class="card-row" onclick="toggleExpand(' + cand.id + ')">' +
      '<div class="ballot-badge">' + cand.sno + '</div>' +
      '<div class="card-main">' +
      '<div class="card-name-row"><span class="card-name">' + esc(cand.name) + '</span>' +
      (cand.winner ? '<span class="winner-badge">' + t('winnerBadge') + '</span>' : '') +
      '<span class="tag ' + cand.tag + '">' + esc(cand.party) + '</span>' +
      symChip(cand.party) + '</div>' +
      '<div class="card-sub">' + esc(cand.profession) + '</div>' +
      '<div class="quick">' + quickChips(cand) + '</div>' +
      '</div><span class="chev">▾</span></div>' +
      '<div class="detail">' + (isOpen ? renderDetail(cand) : '') + '</div></div>';
  });
  document.getElementById('resultArea').innerHTML = html;
}

/* At-a-glance row under each name. Deliberately shows "not recorded" as its own
 * amber state rather than blank — an unchecked criminal record and a clean one
 * must never look the same. */
function quickChips(c){
  let out = '';
  if (c.criminalCount == null) out += '<span class="qchip unk"><span class="ic">▲</span>' + t('chipCasesUnrecorded') + '</span>';
  else if (c.criminalCount > 0) out += '<span class="qchip warn"><span class="ic">⚖</span>' + c.criminalCount + ' ' + (c.criminalCount > 1 ? t('chipCasesPlural') : t('chipCaseSingular')) + '</span>';
  else out += '<span class="qchip ok"><span class="ic">✓</span>' + t('chipNoCases') + '</span>';

  if (c.age != null) out += '<span class="qchip"><span class="ic">🎂</span>' + c.age + '</span>';
  const a = fmtAmount(c.assets);
  if (a) out += '<span class="qchip"><span class="ic">💰</span>' + a + '</span>';
  return out;
}

function toggleExpand(id){ expandedId = (expandedId === id) ? null : id; renderList(); }
function setTab(id, key){ activeTab[id] = key; renderList(); document.getElementById('card-' + id).scrollIntoView({ block:'nearest' }); }
function tabBtn(id, key, label, cur){
  return '<button class="tab-btn' + (cur === key ? ' active' : '') + '" onclick="event.stopPropagation(); setTab(' + id + ", '" + key + "')\">" + label + '</button>';
}
function kv(k, v){ return '<div class="kv"><span class="k">' + k + '</span><span class="v">' + v + '</span></div>'; }

function renderDetail(c){
  // Named tabKey, not "t" — "t" is the global translation function, and
  // shadowing it here silently broke every t() call for the rest of this
  // function's scope. Caught before shipping only because it was checked.
  const tabKey = activeTab[c.id] || 'credentials';
  let html = '<div class="tabs">' +
    tabBtn(c.id, 'credentials', t('tabCredentials'), tabKey) +
    tabBtn(c.id, 'declarations', t('tabDeclarations'), tabKey) +
    tabBtn(c.id, 'promises', t('tabPromises'), tabKey) +
    tabBtn(c.id, 'background', t('tabBackground'), tabKey) + '</div>';

  html += '<div class="tab-panel' + (tabKey === 'credentials' ? ' active' : '') + '">';
  html += kv(t('age'), c.age == null ? '<span class="m-missing">Not available</span>' : c.age);
  html += kv(t('education'), esc(c.education));
  html += kv(t('profession'), esc(c.profession));
  html += kv(t('termsServed'), c.terms);
  html += kv(t('ballotSymbol'), symChip(c.party));
  html += '</div>';

  html += '<div class="tab-panel' + (tabKey === 'declarations' ? ' active' : '') + '">';
  html += '<div class="stamp">SWORN<br>AFFIDAVIT</div>';
  const fc = c.criminalCount == null ? 'flag-unknown' : (c.criminalCount > 0 ? 'flag-some' : 'flag-none');
  const ft = c.criminalCount == null ? "We don't have this information yet"
    : (c.criminalCount > 0 ? c.criminalCount + ' criminal case' + (c.criminalCount > 1 ? 's' : '') + ' declared' : t('noCriminalCases'));
  html += '<div class="criminal-flag ' + fc + '">' + ft + '</div>';
  html += '<div style="clear:both;font-size:12px;color:var(--text-muted);margin-bottom:8px">' + c.criminalNote + '</div>';
  html += kv(t('declaredAssets'), esc(c.assets));
  html += kv(t('declaredLiabilities'), esc(c.liabilities));
  if (c.assetHistory) html += '<div class="note">' + c.assetHistory + '</div>';
  html += c.sourceUrl
    ? '<div class="src-link">Source: <a href="' + c.sourceUrl + '" target="_blank" rel="noopener">' + esc(c.name) + ' — ADR/MyNeta affidavit record</a></div>'
    : "<div class=\"src-link\" style=\"color:var(--text-faint)\">We don't have a source link for this candidate yet.</div>";
  html += '</div>';

  /* Promises: grouped by category so a voter can find the one topic they care
   * about instead of reading a whole manifesto. */
  html += '<div class="tab-panel' + (tabKey === 'promises' ? ' active' : '') + '">';
  const proms = promisesFor(c);
  if (!proms.length){
    html += '<div style="font-size:12px;color:var(--text-muted)">' + (c.manifestoNote || t('noManifesto')) + '</div>';
  } else {
    const groups = {};
    proms.forEach(p => { (groups[p.category] = groups[p.category] || []).push(p); });
    PROMISE_CATEGORIES.forEach(cat => {
      if (!groups[cat.key]) return;
      html += '<div class="promise-group"><h4><span class="pcat"><span class="pi">' + cat.icon + '</span>' + categoryLabel(cat.key) + '</span></h4>';
      groups[cat.key].forEach(p => {
        html += '<div class="plist-item"><span class="bullet">•</span><span>' + esc(p.text) +
          (p.needsReview ? "<span class=\"review-flag\" title=\"We're not fully sure this is the right topic for this promise.\">topic unsure</span>" : '') +
          '</span></div>';
      });
      html += '</div>';
    });
    html += '<div class="note">' + t('promiseDisclaimer') + '</div>';
  }
  html += '</div>';

  /* News: key points first (what we actually found), then links out. */
  html += '<div class="tab-panel' + (tabKey === 'background' ? ' active' : '') + '">';
  if (c.newsStatus === 'not-researched'){
    html += '<div style="font-size:12px;color:var(--text-muted)">' + NOT_RESEARCHED_NOTE + '</div>';
  } else if (c.newsStatus === 'no-coverage'){
    html += '<div style="font-size:12px;color:var(--text-muted)">' + NO_COVERAGE_NOTE + '</div>';
  }
  if (c.background && c.background.length){
    html += '<div class="promise-group"><h4>Key points</h4>';
    c.background.forEach((b, i) => {
      if (b.flag){
        html += '<div class="bg-item flag"><span class="flag-label">' + b.flagLabel + '</span>' + b.text + '</div>';
      } else {
        html += '<div class="keypoint"><span class="kp-num">' + (i + 1) + '</span><span>' + b.text + '</span></div>';
      }
    });
    html += '</div>';
  }
  if (c.newsLinks && c.newsLinks.length){
    html += '<div class="promise-group"><h4>Read the full coverage</h4>';
    c.newsLinks.forEach(n => {
      html += '<a class="news-card" href="' + n.url + '" target="_blank" rel="noopener">' +
        '<div class="nc-title">' + esc(n.title) + '</div><div class="nc-domain">' + esc(n.domain) + ' ↗</div></a>';
    });
    html += '</div>';
  }
  html += '</div>';
  return html;
}

/* --- Compare-all matrix ---------------------------------------------------
 * Every candidate, every parameter, one screen. Replaces the old two-candidate
 * limit, which forced a voter facing 22 names to run dozens of pairwise
 * comparisons to answer "who here has no criminal cases?".
 *
 * It sorts but never scores: there is no computed "best candidate" column,
 * because collapsing criminal cases, education and wealth into one number is a
 * values judgment, not a fact, and it is not this app's to make. */
/* labelKey is resolved through t() at render time (not baked in here) so
 * column headers switch language immediately when renderMatrix() re-runs
 * after a language change. */
const MATRIX_COLS = [
  { key:'sno',      labelKey:'colHash',       type:'num',  get:c => c.sno },
  { key:'name',     labelKey:'colCandidate',  type:'str',  get:c => c.name, sticky:true },
  { key:'age',      labelKey:'age',           type:'num',  get:c => c.age },
  { key:'edu',      labelKey:'education',     type:'num',  get:c => c.eduLevel },
  { key:'crime',    labelKey:'colCriminalCases', type:'num', get:c => c.criminalCount },
  { key:'assets',   labelKey:'declaredAssets', type:'num', get:c => parseAmount(c.assets) },
  { key:'liab',     labelKey:'colLiabilities', type:'num', get:c => parseAmount(c.liabilities) },
  { key:'terms',    labelKey:'colTerms',      type:'num',  get:c => c.terms },
  { key:'prof',     labelKey:'profession',    type:'str',  get:c => c.profession }
];

const EDU_LABELS = { 1:'8th', 2:'10th', 3:'12th', 4:'Graduate', 5:'Post-grad', 6:'Doctorate' };

function openMatrix(){
  renderMatrix();
  document.getElementById('matrixOverlay').classList.add('show');
  document.body.style.overflow = 'hidden';
}
function closeCanvas(id){
  document.getElementById(id).classList.remove('show');
  document.body.style.overflow = '';
}
function sortMatrix(col){
  matrixSort = (matrixSort.col === col) ? { col:col, dir:-matrixSort.dir } : { col:col, dir:1 };
  renderMatrix();
}

function renderMatrix(){
  const c = CONSTITUENCIES[currentKey];
  const list = c.candidates.slice();
  const col = MATRIX_COLS.find(x => x.key === matrixSort.col) || MATRIX_COLS[0];

  /* Unknowns always sink to the bottom, in both sort directions. Sorting a
   * missing value as if it were zero would put every candidate whose record we
   * failed to parse at the "cleanest" end of the criminal-cases column — the
   * single most misleading thing this table could do. */
  list.sort((a, b) => {
    const va = col.get(a), vb = col.get(b);
    const na = va == null || va === '', nb = vb == null || vb === '';
    if (na && nb) return 0;
    if (na) return 1;
    if (nb) return -1;
    if (col.type === 'num') return (va - vb) * matrixSort.dir;
    return String(va).localeCompare(String(vb)) * matrixSort.dir;
  });

  const maxAssets = Math.max(...c.candidates.map(x => parseAmount(x.assets) || 0), 1);

  let html = '<div class="matrix-wrap"><table class="matrix"><thead><tr>';
  MATRIX_COLS.forEach(mc => {
    const arrow = matrixSort.col === mc.key ? '<span class="arrow">' + (matrixSort.dir > 0 ? '▲' : '▼') + '</span>' : '';
    html += '<th' + (mc.sticky ? ' class="cname"' : '') + ' onclick="sortMatrix(\'' + mc.key + '\')">' + t(mc.labelKey) + arrow + '</th>';
  });
  html += '</tr></thead><tbody>';

  list.forEach(cand => {
    html += '<tr>';
    html += '<td><span class="amt">' + cand.sno + '</span></td>';
    html += '<td class="cname"><span class="m-name">' + esc(cand.name) + (cand.winner ? ' <span class="winner-badge">' + t('winnerBadge') + '</span>' : '') + '</span>' +
            '<span class="m-party">' + symChip(cand.party, { showName:false }) + esc(cand.party) + '</span></td>';
    html += '<td>' + (cand.age == null ? '<span class="m-missing">' + t('matrixNotRecorded') + '</span>' : cand.age) + '</td>';

    if (cand.eduLevel == null){
      html += '<td><span class="m-missing">' + t('matrixNotRecorded') + '</span></td>';
    } else {
      let pips = '';
      for (let i = 1; i <= 6; i++) pips += '<span class="edu-pip' + (i <= cand.eduLevel ? ' on' : '') + '"></span>';
      html += '<td><span class="edu-pips" title="' + esc(cand.education) + '">' + pips + '</span>' +
              '<div style="font-size:10px;color:var(--text-muted);margin-top:2px">' + (EDU_LABELS[cand.eduLevel] || '') + '</div></td>';
    }

    if (cand.criminalCount == null){
      html += "<td><span class=\"crime-unk\" title=\"We don't have this information yet — that's different from zero cases.\">" + t('matrixNotRecorded') + "</span></td>";
    } else if (cand.criminalCount === 0){
      html += '<td><span class="crime-zero">✓ ' + t('matrixNone') + '</span></td>';
    } else {
      let dots = '';
      for (let i = 0; i < Math.min(cand.criminalCount, 10); i++) dots += '<span class="crime-dot"></span>';
      html += '<td><span class="crime-dots" title="' + esc(cand.criminalNote || '') + '">' + dots +
              '<span style="margin-left:5px;font-family:var(--mono);font-size:11px;color:var(--stamp-red)">' + cand.criminalCount + '</span></span></td>';
    }

    const av = parseAmount(cand.assets), af = fmtAmount(cand.assets);
    html += '<td>' + (af === null ? '<span class="m-missing">' + t('matrixNotRecorded') + '</span>'
      : '<span class="amt">' + af + '</span><span class="abar"><i style="width:' + Math.max(2, (av / maxAssets) * 100) + '%"></i></span>') + '</td>';

    const lf = fmtAmount(cand.liabilities);
    html += '<td>' + (lf === null ? '<span class="m-missing">' + t('matrixNotRecorded') + '</span>' : '<span class="amt">' + lf + '</span>') + '</td>';
    html += '<td>' + cand.terms + '</td>';
    html += '<td style="max-width:190px;font-size:11.5px">' + esc(cand.profession) + '</td>';
    html += '</tr>';
  });

  html += '</tbody></table></div>';
  html += '<div class="legend-row">' +
    '<span><span class="crime-dot"></span> ' + t('legendCrimeDot') + '</span>' +
    '<span><span class="edu-pip on"></span><span class="edu-pip on"></span><span class="edu-pip"></span> ' + t('legendEduLevel') + '</span>' +
    '<span class="m-missing">' + t('legendNotRecorded') + '</span>' +
    '</div>';
  html += '<div class="disclaimer-note">' + t('matrixDisclaimer') + '</div>';

  document.getElementById('matrixSub').textContent =
    c.label + ' · ' + c.candidates.length + ' ' + t('candidatesWord') + ' · ' + t('sortedBy') + ' ' + t(col.labelKey);
  document.getElementById('matrixContent').innerHTML = html;
}

/* --- Promise canvas -------------------------------------------------------
 * Pick a category, see what every candidate on the ballot has said about it,
 * side by side — including, importantly, who has said nothing. */
function openPromises(){
  activeCat = 'all';
  renderPromiseCanvas();
  document.getElementById('promiseOverlay').classList.add('show');
  document.body.style.overflow = 'hidden';
}
function setCat(k){ activeCat = k; renderPromiseCanvas(); }

function renderPromiseCanvas(){
  const c = CONSTITUENCIES[currentKey];
  const list = c.candidates;

  const counts = {};
  list.forEach(cand => {
    promisesFor(cand).forEach(p => { counts[p.category] = (counts[p.category] || 0) + 1; });
  });
  const present = PROMISE_CATEGORIES.filter(cat => counts[cat.key]);

  let html = '<div class="cat-bar">';
  html += '<button class="cat-btn' + (activeCat === 'all' ? ' active' : '') + '" onclick="setCat(\'all\')">' + t('allTopics') + '</button>';
  present.forEach(cat => {
    html += '<button class="cat-btn' + (activeCat === cat.key ? ' active' : '') + '" onclick="setCat(\'' + cat.key + '\')">' +
      '<span>' + cat.icon + '</span>' + categoryLabel(cat.key) + '<span class="cnt">' + counts[cat.key] + '</span></button>';
  });
  html += '</div>';

  // A separate description line under the selected topic isn't shown here:
  // promise_taxonomy.py's blurb text is English-only, and repeating it under
  // an already-translated button label in another language read as broken
  // (half English, half not) rather than helpful — the label alone is enough.

  /* One column per candidate that has a manifesto. Candidates without one are
   * summarised below rather than rendered as a wall of empty cards — but they
   * are never dropped, because "this candidate published nothing" is itself
   * information a voter should have. */
  const withManifesto = list.filter(cand => promisesFor(cand).length);
  const without = list.filter(cand => !promisesFor(cand).length);

  html += '<div class="pcols">';
  withManifesto.forEach(cand => {
    const proms = promisesFor(cand).filter(p => activeCat === 'all' || p.category === activeCat);
    html += '<div class="pcol"><h5>' + esc(cand.name) + '</h5>' +
      '<div class="pc-party">' + symChip(cand.party, { showName:false }) + esc(cand.party) + '</div>';
    if (!proms.length){
      html += '<div class="none">' + t('noPledgeInTopic') + '</div>';
    } else {
      proms.forEach(p => {
        const cat = catByKey(p.category);
        html += '<div class="plist-item"><span class="bullet">' + (activeCat === 'all' ? cat.icon : '•') + '</span><span>' +
          esc(p.text) + (p.needsReview ? '<span class="review-flag">' + t('topicUnsure') + '</span>' : '') + '</span></div>';
      });
    }
    html += '</div>';
  });
  html += '</div>';

  if (without.length){
    html += '<div class="disclaimer-note"><b>' + t('noManifestoCount').replace('{n}', without.length).replace('{total}', list.length) +
      '</b> — ' + esc(without.map(x => x.name).join(', ')) + '. ' + t('noManifestoExplain') + '</div>';
  }
  html += '<div class="disclaimer-note">' + t('promiseDisclaimer') + '</div>';

  document.getElementById('promiseSub').textContent =
    c.label + ' · ' + present.length + ' ' + t('topicsCoveredAcross') + ' ' + withManifesto.length + ' ' + t('manifestosWord');
  document.getElementById('promiseContent').innerHTML = html;
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape'){ closeCanvas('matrixOverlay'); closeCanvas('promiseOverlay'); }
});
