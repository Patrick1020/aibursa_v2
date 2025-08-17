function setTheme(theme){
  const root = document.documentElement;
  if (theme === "light"){ root.classList.add("light"); root.classList.remove("dark"); }
  else { root.classList.add("dark"); root.classList.remove("light"); }
  localStorage.setItem("theme", theme);
  const btn = document.getElementById("themeToggle");
  if (btn){
    const isLight = root.classList.contains("light");
    btn.setAttribute("aria-pressed", String(isLight));
    const lbl = btn.querySelector(".theme-label");
    if (lbl) lbl.textContent = isLight ? "Dark Mode" : "Light Mode";
  }
}
setTheme(localStorage.getItem("theme") || "dark");
const btn = document.getElementById("themeToggle");
if (btn) btn.addEventListener("click", () => {
  const next = document.documentElement.classList.contains("dark") ? "light" : "dark";
  setTheme(next);
});
