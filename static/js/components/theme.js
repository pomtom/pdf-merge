// Light/dark theme toggle. index.html applies the initial theme pre-paint;
// this component owns the toggle button and OS-scheme changes.

const SUN = `<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>`;
const MOON = `<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>`;

export function initTheme() {
  const btn = document.getElementById("btn-theme");
  const apply = (theme) => {
    document.documentElement.dataset.theme = theme;
    btn.innerHTML = theme === "dark" ? SUN : MOON;
  };
  apply(document.documentElement.dataset.theme);

  btn.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    localStorage.setItem("theme", next);
    apply(next);
  });

  // Follow OS scheme changes only while the user hasn't chosen manually.
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
    if (!localStorage.getItem("theme")) apply(e.matches ? "dark" : "light");
  });
}
