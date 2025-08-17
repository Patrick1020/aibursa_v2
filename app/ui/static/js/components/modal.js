let activeModal = null;

function ensureRoot(){
  let root = document.getElementById("modal-root");
  if (!root){
    root = document.createElement("div");
    root.id = "modal-root";
    root.className = "modal-root";
    document.body.appendChild(root);
  }
  return root;
}

function trapFocus(modalEl){
  const focusable = modalEl.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  const first = focusable[0], last = focusable[focusable.length - 1];
  function onKey(e){
    if (e.key === "Escape") closeModal();
    if (e.key !== "Tab") return;
    if (e.shiftKey && document.activeElement === first){ e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last){ e.preventDefault(); first.focus(); }
  }
  modalEl.addEventListener("keydown", onKey);
  return () => modalEl.removeEventListener("keydown", onKey);
}

export function openModal({ title = "", content, size = "lg" }){
  if (activeModal) closeModal();
  const root = ensureRoot();

  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";

  const modal = document.createElement("div");
  modal.className = `modal modal-${size}`;
  modal.setAttribute("role", "dialog");
  modal.setAttribute("aria-modal", "true");

  const header = document.createElement("div");
  header.className = "modal-header";
  header.innerHTML = `<div class="modal-title">${title}</div>`;
  const closeBtn = document.createElement("button");
  closeBtn.className = "modal-close";
  closeBtn.setAttribute("aria-label", "Close");
  closeBtn.innerHTML = "✕";
  header.appendChild(closeBtn);

  const body = document.createElement("div");
  body.className = "modal-body";
  if (content instanceof HTMLElement) body.appendChild(content);
  else if (typeof content === "string") body.innerHTML = content;

  const container = document.createElement("div");
  container.appendChild(overlay);
  container.appendChild(modal);
  modal.appendChild(header);
  modal.appendChild(body);
  root.appendChild(container);

  const removeTrap = trapFocus(modal);

  const onClose = () => {
    container.classList.remove("show");
    setTimeout(() => {
      removeTrap();
      container.remove();
      activeModal = null;
    }, 160);
  };
  overlay.addEventListener("click", onClose);
  closeBtn.addEventListener("click", onClose);

  // animație
  setTimeout(() => container.classList.add("show"), 10);

  // focus în dialog
  setTimeout(() => closeBtn.focus(), 60);

  activeModal = { container, onClose };
  return onClose;
}

export function closeModal(){
  if (activeModal) activeModal.onClose();
}
