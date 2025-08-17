export function toast(msg, type="info"){
  const root = document.getElementById("toast-root");
  if (!root) return;
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${msg}</span>`;
  root.appendChild(el);
  setTimeout(()=>{ el.classList.add("show"); }, 10);
  setTimeout(()=>{ el.classList.remove("show"); setTimeout(()=>el.remove(), 250); }, 2500);
}
