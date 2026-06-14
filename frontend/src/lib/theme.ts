export type Theme = "dark" | "light";
const KEY = "caret-theme";

export function initTheme(): void {
  const param = new URLSearchParams(window.location.search).get("theme");
  const fromUrl: Theme | null = param === "light" || param === "dark" ? param : null;
  const theme: Theme = fromUrl ?? ((localStorage.getItem(KEY) as Theme) || "dark");
  document.documentElement.dataset.theme = theme;
  if (fromUrl) localStorage.setItem(KEY, fromUrl);
}

export function getTheme(): Theme {
  return (document.documentElement.dataset.theme as Theme) || "dark";
}

export function setTheme(t: Theme): void {
  document.documentElement.dataset.theme = t;
  localStorage.setItem(KEY, t);
}
