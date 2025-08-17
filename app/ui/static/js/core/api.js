export async function getPredictions() {
  const r = await fetch("/api/predictions");
  if (!r.ok) throw new Error("Failed to fetch predictions");
  return r.json();
}

export async function createPrediction(ticker, horizon_days=7) {
  const r = await fetch("/api/predictions", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ ticker, horizon_days })
  });
  if (!r.ok) throw new Error("Failed to create prediction");
  return r.json();
}

export async function getQuotes(tickers) {
  const uniq = [...new Set(tickers.map(t => t.toUpperCase()))];
  if (!uniq.length) return {};
  const r = await fetch(`/api/market/quotes?tickers=${encodeURIComponent(uniq.join(","))}`);
  const j = await r.json();
  const map = {};
  for (const q of (j.quotes||[])) map[q.ticker] = q.price;
  return map;
}
