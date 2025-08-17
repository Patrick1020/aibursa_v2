export function renderSparkline(el, data, { strokeWidth = 2 } = {}){
  if (!el) return;
  const w = el.clientWidth || 600;
  const h = el.clientHeight || 220;
  if (!Array.isArray(data) || data.length < 2){
    el.innerHTML = `<div class="muted">Insuficiente puncte pentru grafic.</div>`;
    return;
  }
  const min = Math.min(...data), max = Math.max(...data);
  const padTop = 8, padBottom = 14, padX = 8;
  const x = (i) => padX + (i / (data.length - 1)) * (w - 2*padX);
  const y = (v) => {
    const r = max - min || 1;
    return padTop + (1 - (v - min) / r) * (h - padTop - padBottom);
  };

  const points = data.map((v, i) => `${x(i)},${y(v)}`).join(" ");
  const up = data[data.length - 1] >= data[0];

  const svg = `
  <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <defs>
      <linearGradient id="sgFill" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${up ? "#22c55e" : "#ef4444"}" stop-opacity="0.18"/>
        <stop offset="100%" stop-color="${up ? "#22c55e" : "#ef4444"}" stop-opacity="0.00"/>
      </linearGradient>
      <filter id="sgShadow"><feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.4"/></filter>
    </defs>
    <polyline points="${points}" fill="none" stroke="${up ? "#22c55e" : "#ef4444"}" stroke-width="${strokeWidth}" filter="url(#sgShadow)" />
    <polygon points="${points} ${x(data.length-1)},${h-padBottom} ${x(0)},${h-padBottom}" fill="url(#sgFill)"/>
  </svg>`;
  el.innerHTML = svg;
}
