import { openModal } from "./modal.js";
import { renderSparkline } from "./sparkline.js";
import { fmt } from "../core/utils.js";
import { getPredictionDetails } from "../core/api.js";
import { toast } from "./toast.js";

export async function openDetails(ticker){
  try {
    const data = await getPredictionDetails(ticker, { period:"6mo", interval:"1d", limit:12 });

    const root = document.createElement("div");
    root.innerHTML = `
      <div class="details-grid">
        <div class="card-soft">
          <div class="flex-col">
            <div class="muted" style="margin-bottom:.4rem;">${data.period} • ${data.interval}</div>
            <div class="sparkline-wrap" id="spark-wrap"></div>
          </div>
        </div>
        <div class="card-soft">
          <div class="kpis">
            <div class="kpi-chip">
              <div class="lab">Ultimul preț</div>
              <div class="val">${data.last_price == null ? "-" : fmt.price(data.last_price)}</div>
            </div>
            <div class="kpi-chip">
              <div class="lab">Probabilitate</div>
              <div class="val">${data.prediction ? `${data.prediction.probability_pct.toFixed(2)}%` : "-"}</div>
            </div>
            <div class="kpi-chip">
              <div class="lab">Expected change</div>
              <div class="val ${data.prediction && data.prediction.expected_change_pct>=0 ? "text-green":"text-red"}">
                ${data.prediction ? fmt.pct(data.prediction.expected_change_pct) : "-"}
              </div>
            </div>
          </div>
          <div class="kpi-chip" style="margin-top:.5rem;">
            <div class="lab">Reward / Risk</div>
            <div class="val">${data.prediction ? data.prediction.reward_to_risk.toFixed(2) : "-"}</div>
          </div>
        </div>
      </div>

      <div class="pred-list card-soft">
        <div class="muted" style="margin-bottom:.35rem;">Predicții anterioare</div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Data</th>
                <th>Horizon</th>
                <th>Prob.</th>
                <th>Exp. %</th>
                <th>R:R</th>
                <th>Outcome</th>
              </tr>
            </thead>
            <tbody id="pred-rows"></tbody>
          </table>
        </div>
      </div>
    `;

    // Sparkline
    const prices = (data.candles || []).map(c => c.close);
    renderSparkline(root.querySelector("#spark-wrap"), prices);

    // Rows
    const tb = root.querySelector("#pred-rows");
    const rows = [data.prediction, ...(data.previous || [])].filter(Boolean);
    if (!rows.length){
      tb.innerHTML = `<tr><td colspan="6" class="muted">Nu există predicții pentru acest ticker.</td></tr>`;
    } else {
      for (const r of rows){
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${r.created_at ? new Date(r.created_at).toLocaleString() : "-"}</td>
          <td>${r.horizon_days}d</td>
          <td>${r.probability_pct.toFixed(2)}%</td>
          <td class="${r.expected_change_pct>=0?"text-green":"text-red"}">${fmt.pct(r.expected_change_pct)}</td>
          <td>${r.reward_to_risk.toFixed(2)}</td>
          <td>${r.outcome || "-"}</td>
        `;
        tb.appendChild(tr);
      }
    }

    openModal({ title: `${data.ticker} • Detalii`, content: root, size: "lg" });
  } catch (e){
    toast(String(e.message || e), "error");
  }
}
