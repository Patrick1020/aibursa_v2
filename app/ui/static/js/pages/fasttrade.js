import { fmt, qs } from "../core/utils.js";
import { getPredictions, getQuotes } from "../core/api.js";
import { toast } from "../components/toast.js";

function decideSignal(prob, exp, rr){
  if (prob >= 75 && exp >= 1.0 && rr >= 1.15) return { t:"Buy", cls:"badge-green" };
  if (exp <= -1.0 && prob >= 60) return { t:"Sell", cls:"badge-red" };
  return { t:"Hold", cls:"badge-yellow" };
}
function outcomeBadge(outcome){
  if (outcome === "win") return { t:"Win", cls:"badge-green" };
  if (outcome === "loss") return { t:"Loss", cls:"badge-red" };
  return { t:"Breakeven", cls:"badge-slate" };
}
function probCell(pct){
  const v = Math.max(0, Math.min(100, pct || 0));
  return `<div class="prob"><span class="pill">${Math.round(v)}%</span><span class="meter"><i style="width:${v}%"></i></span></div>`;
}

async function loadOnce(){
  const body = qs("#ftBody"); if (!body) return;
  const data = await getPredictions();
  const quotes = await getQuotes(data.map(x=>x.ticker));
  body.innerHTML = "";
  for (const p of data.slice(0, 25)){
    const price = quotes[p.ticker] ?? null;
    const out = outcomeBadge(p.outcome);
    const sig = decideSignal(p.probability_pct, p.expected_change_pct, p.reward_to_risk);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="font-bold">${p.ticker}</td>
      <td>${price==null?"-":fmt.price(price)}</td>
      <td class="${p.expected_change_pct>=0?"text-green":"text-red"}">${fmt.pct(p.expected_change_pct)}</td>
      <td>${probCell(p.probability_pct)}</td>
      <td><span class="${out.cls} badge">${out.t}</span></td>
      <td><span class="badge badge-rr">${Number(p.reward_to_risk).toFixed(2)}</span></td>
      <td><span class="${sig.cls} badge">${sig.t}</span></td>
      <td class="muted">${fmt.date(p.created_at)}</td>
    `;
    body.appendChild(tr);
  }
}

let timer = null;
qs("#ftStart").addEventListener("click", () => {
  if (!timer){ loadOnce().catch(()=>{}); timer = setInterval(loadOnce, 5000); toast("Fast Trade: started", "success"); }
});
qs("#ftStop").addEventListener("click", () => {
  if (timer){ clearInterval(timer); timer = null; toast("Fast Trade: stopped", "info"); }
});
loadOnce().catch(e => toast(e.message, "error"));
