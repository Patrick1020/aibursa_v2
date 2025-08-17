import { fmt, qs, qsa } from "../core/utils.js";
import { getPredictions, createPrediction, getQuotes } from "../core/api.js";
import { toast } from "../components/toast.js";

/* ---------- PERSIST PREFS ---------- */
const PREFS_KEY = "dashPrefs_v1";
function loadPrefs(){
  try { return JSON.parse(localStorage.getItem(PREFS_KEY) || "{}"); } catch { return {}; }
}
function savePrefs(p){ localStorage.setItem(PREFS_KEY, JSON.stringify(p)); }
const prefs = Object.assign({ sortKey:"ticker", sortDir:"asc", pageSize:15, search:"", page:1 }, loadPrefs());

/* ---------- STATE ---------- */
const state = {
  rows: [],
  quotes: {},
  sortKey: prefs.sortKey,
  sortDir: prefs.sortDir,
  page: prefs.page || 1,
  pageSize: prefs.pageSize,
  filtered() {
    const q = (qs("#searchSymbol")?.value || prefs.search || "").trim().toUpperCase();
    if (!q) return this.rows;
    return this.rows.filter(r => r.ticker.includes(q));
  }
};

/* ---------- DOMAIN RULES ---------- */
function decideSignal(prob, exp, rr) {
  if (prob >= 75 && exp >= 1.0 && rr >= 1.15) return { t: "Buy", cls: "badge-green" };
  if (exp <= -1.0 && prob >= 60) return { t: "Sell", cls: "badge-red" };
  return { t: "Hold", cls: "badge-yellow" };
}
function outcomeBadge(outcome) {
  if (outcome === "win") return { t: "Win", cls: "badge-green" };
  if (outcome === "loss") return { t: "Loss", cls: "badge-red" };
  return { t: "Breakeven", cls: "badge-slate" };
}
function probCell(pct) {
  const v = Math.max(0, Math.min(100, pct || 0));
  return `<div class="prob"><span class="pill">${Math.round(v)}%</span><span class="meter"><i style="width:${v}%"></i></span></div>`;
}

/* ---------- KPIs ---------- */
function renderKPIs(data) {
  qs("#kpi-total").textContent = String(data.length || 0);
  qs("#kpi-prob").textContent  = data.length ? `${(data.reduce((a,b)=>a+b.probability_pct,0)/data.length).toFixed(1)}%` : "-";
  qs("#kpi-rr").textContent    = data.length ? (data.reduce((a,b)=>a+b.reward_to_risk,0)/data.length).toFixed(2) : "-";
}
function renderSignalKPIs(data) {
  let buy=0, hold=0, sell=0;
  for (const p of data){
    const sig = decideSignal(p.probability_pct, p.expected_change_pct || 0, p.reward_to_risk);
    if (sig.t === "Buy") buy++;
    else if (sig.t === "Sell") sell++;
    else hold++;
  }
  const kb = qs("#kpi-buy"), kh = qs("#kpi-hold"), ks = qs("#kpi-sell");
  if (kb) kb.textContent = `Buy: ${buy}`;
  if (kh) kh.textContent = `Hold: ${hold}`;
  if (ks) ks.textContent = `Sell: ${sell}`;
}

/* ---------- SORT & PAGE HELPERS ---------- */
function preparedRows() {
  return state.filtered().map(p => {
    const price = state.quotes[p.ticker] ?? null;
    const expected = p.expected_change_pct || 0;
    const mid   = price != null ? price * (1 + expected/100) : null;
    const delta = price != null ? Math.max(price * 0.015, Math.abs(expected)/100 * price * 0.20) : null;
    const estLo = mid != null ? mid - delta : null;
    const estHi = mid != null ? mid + delta : null;
    const estPriceMid = mid;
    const signal = decideSignal(p.probability_pct, expected, p.reward_to_risk).t;
    const outcomeRank = p.outcome === "win" ? 2 : (p.outcome === "loss" ? 0 : 1);
    return { p, price, expected, estLo, estHi, estPriceMid, signal, outcomeRank };
  });
}
function sortRows(rows) {
  const dir = state.sortDir === "asc" ? 1 : -1;
  const key = state.sortKey;
  rows.sort((A, B) => {
    const cmp = (x, y) => (x > y) - (x < y);
    switch (key) {
      case "ticker":      return dir * cmp(A.p.ticker, B.p.ticker);
      case "price":       return dir * cmp(A.price ?? -Infinity, B.price ?? -Infinity);
      case "prediction":  return dir * cmp(A.expected, B.expected);
      case "estprice":    return dir * cmp(A.estPriceMid ?? -Infinity, B.estPriceMid ?? -Infinity);
      case "probability": return dir * cmp(A.p.probability_pct, B.p.probability_pct);
      case "outcome":     return dir * cmp(A.outcomeRank, B.outcomeRank);
      case "rr":          return dir * cmp(A.p.reward_to_risk, B.p.reward_to_risk);
      case "signal":      return dir * cmp(A.signal, B.signal);
      case "date":        return dir * cmp(new Date(A.p.created_at).getTime(), new Date(B.p.created_at).getTime());
      default:            return 0;
    }
  });
  return rows;
}
function pageSlice(rows) {
  const start = (state.page - 1) * state.pageSize;
  const end = start + state.pageSize;
  return rows.slice(start, end);
}

/* ---------- TABLE RENDER ---------- */
function updateSortARIA() {
  qsa("thead th").forEach(th => th.setAttribute("aria-sort", "none"));
  const th = Array.from(qsa("thead th")).find(th => {
    const btn = th.querySelector(".sort-btn"); return btn && btn.dataset.sort === state.sortKey;
  });
  if (th) th.setAttribute("aria-sort", state.sortDir === "asc" ? "ascending" : "descending");
}
function renderPager() {
  const all = preparedRows();
  const total = all.length;
  const totalPages = Math.max(1, Math.ceil(total / state.pageSize));
  if (state.page > totalPages) state.page = totalPages;
  const startIdx = total ? (state.page - 1) * state.pageSize + 1 : 0;
  const endIdx = Math.min(total, state.page * state.pageSize);
  qs("#rowsInfo").textContent = `Showing ${startIdx}–${endIdx} of ${total}`;
  qs("#pageInfo").textContent = `Page ${state.page} / ${totalPages}`;
  qs("#prevPage").disabled = state.page <= 1;
  qs("#nextPage").disabled = state.page >= totalPages;
  qs("#rowsPerPage").value = String(state.pageSize);
}
function renderTable() {
  const tb = qs("#tableBody"); if (!tb) return;
  tb.innerHTML = "";
  const rows = pageSlice(sortRows(preparedRows()));
  for (const r of rows) {
    const { p, price, expected, estLo, estHi } = r;
    const sig = decideSignal(p.probability_pct, expected, p.reward_to_risk);
    const out = outcomeBadge(p.outcome);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="font-bold">${p.ticker}</td>
      <td>${price==null?"-":fmt.price(price)}</td>
      <td class="${expected >= 0 ? "text-green" : "text-red"}">${fmt.pct(expected)}</td>
      <td>${(estLo==null||estHi==null)?"-":`${fmt.price(estLo)} – ${fmt.price(estHi)}`}</td>
      <td>${probCell(p.probability_pct)}</td>
      <td><span class="${out.cls} badge">${out.t}</span></td>
      <td><span class="badge badge-rr">${Number(p.reward_to_risk).toFixed(2)}</span></td>
      <td><span class="${sig.cls} badge">${sig.t}</span></td>
      <td class="muted">${fmt.date(p.created_at)}</td>
      <td class="text-center"><a class="link" href="#">Details</a></td>
    `;
    tb.appendChild(tr);
  }
  renderPager();
  updateSortARIA();
  persistNow();
}

/* ---------- DATA FLOW ---------- */
async function refreshAll() {
  const data = await getPredictions();
  state.rows = data;
  renderKPIs(data);
  renderSignalKPIs(data);
  state.quotes = await getQuotes(data.map(x => x.ticker));
  state.page = 1; // reset la noul set
  renderTable();
}

/* ---------- EVENTS ---------- */
function persistNow(){
  const search = qs("#searchSymbol")?.value || "";
  savePrefs({ sortKey:state.sortKey, sortDir:state.sortDir, pageSize:state.pageSize, page:state.page, search });
}
function bindEvents() {
  const reRender = () => renderTable();

  // sort
  qsa(".sort-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const key = btn.dataset.sort;
      if (state.sortKey === key) state.sortDir = (state.sortDir === "asc" ? "desc" : "asc");
      else { state.sortKey = key; state.sortDir = "asc"; }
      state.page = 1; reRender();
    });
  });

  // pager
  qs("#prevPage")?.addEventListener("click", () => { if (state.page>1){ state.page--; reRender(); } });
  qs("#nextPage")?.addEventListener("click", () => { state.page++; reRender(); });
  qs("#rowsPerPage")?.addEventListener("change", (e) => {
    state.pageSize = parseInt(e.target.value, 10) || 15;
    state.page = 1; reRender();
  });

  // refresh + search
  const doRefresh = () => refreshAll().catch(e => toast(e.message, "error"));
  qs("#btnRefresh")?.addEventListener("click", doRefresh);
  qs("#btnSearch")?.addEventListener("click", doRefresh);
  const si = qs("#searchSymbol");
  if (si){ si.value = prefs.search || ""; si.addEventListener("input", doRefresh); }

  // predict
  qs("#btnPredict")?.addEventListener("click", async () => {
    const t = qs("#tickerInput")?.value.trim().toUpperCase();
    const h = parseInt(qs("#horizonInput")?.value || "7", 10);
    if (!t) { toast("Ticker required", "error"); return; }
    try {
      await createPrediction(t, h);
      toast(`Prediction added: ${t}`, "success");
      if (qs("#tickerInput")) qs("#tickerInput").value = "";
      await refreshAll();
    } catch(e){ toast(e.message, "error"); }
  });

  // HOTKEYS
  let gPressedAt = 0;
  document.addEventListener("keydown", (ev) => {
    const tag = (ev.target && ev.target.tagName) || "";
    const editing = tag === "INPUT" || tag === "TEXTAREA";
    // "/" focus search
    if (ev.key === "/" && !editing) {
      ev.preventDefault(); qs("#searchSymbol")?.focus(); return;
    }
    // Enter: dacă e în inputs Predict, trimite; dacă e în search, refresh
    if (ev.key === "Enter") {
      if (ev.target === qs("#tickerInput") || ev.target === qs("#horizonInput")) { qs("#btnPredict")?.click(); }
      else if (ev.target === qs("#searchSymbol")) { qs("#btnSearch")?.click(); }
      return;
    }
    if (editing) return; // nu captura navegația dacă editează un input

    // navigație paginare
    if (ev.key === "ArrowLeft") { ev.preventDefault(); qs("#prevPage")?.click(); }
    if (ev.key === "ArrowRight"){ ev.preventDefault(); qs("#nextPage")?.click(); }

    // gg / G
    const now = performance.now();
    if (ev.key.toLowerCase() === "g") {
      if (now - gPressedAt < 350) { window.scrollTo({top:0,behavior:"smooth"}); gPressedAt = 0; }
      else gPressedAt = now;
    }
    if (ev.key === "G" && ev.shiftKey) { window.scrollTo({top:document.body.scrollHeight, behavior:"smooth"}); }
  });
}

/* ---------- BOOT ---------- */
bindEvents();
refreshAll().catch(e => toast(e.message, "error"));
