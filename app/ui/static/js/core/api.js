export async function getPredictions() {
  const r = await fetch("/api/predictions");
  if (!r.ok) {
    const t = await r.text().catch(()=> "");
    throw new Error(`GET /api/predictions failed: ${r.status} ${r.statusText} ${t?.slice(0,120)}`);
  }
  return r.json();
}

export async function createPrediction(ticker, horizon_days=7) {
  const r = await fetch("/api/predictions", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ ticker, horizon_days })
  });
  if (!r.ok) {
    const t = await r.text().catch(()=> "");
    throw new Error(`POST /api/predictions failed: ${r.status} ${r.statusText} ${t?.slice(0,120)}`);
  }
  return r.json();
}

export async function getQuotes(tickers) {
  const uniq = [...new Set(tickers.map(t => t.toUpperCase()))];
  if (!uniq.length) return {};
  const r = await fetch(`/api/market/quotes?tickers=${encodeURIComponent(uniq.join(","))}`);
  if (!r.ok) {
    const t = await r.text().catch(()=> "");
    throw new Error(`GET /api/market/quotes failed: ${r.status} ${r.statusText} ${t?.slice(0,120)}`);
  }
  const j = await r.json();
  const map = {};
  for (const q of (j.quotes||[])) map[q.ticker] = q.price;
  return map;
}

export async function getPredictionDetails(ticker, { period="6mo", interval="1d", limit=12 } = {}){
  const url = `/api/predictions/${encodeURIComponent(ticker)}?period=${encodeURIComponent(period)}&interval=${encodeURIComponent(interval)}&limit=${limit}`;
  const r = await fetch(url);
  if (!r.ok){
    const t = await r.text().catch(()=> "");
    throw new Error(`GET ${url} failed: ${r.status} ${r.statusText} ${t?.slice(0,120)}`);
  }
  return r.json();
}
