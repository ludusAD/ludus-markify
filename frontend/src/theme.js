import { useEffect, useState } from "react";

const KEY = "ludus-theme";

// "system" follows the OS; "light" and "dark" force a theme.
function readStored() {
  try {
    const v = localStorage.getItem(KEY);
    return v === "light" || v === "dark" ? v : "system";
  } catch {
    return "system";
  }
}

export function useTheme() {
  const [theme, setTheme] = useState(readStored);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
    try {
      if (theme === "system") localStorage.removeItem(KEY);
      else localStorage.setItem(KEY, theme);
    } catch {
      // Storage can be blocked; the choice then lasts for this visit only.
    }
  }, [theme]);

  return [theme, setTheme];
}
