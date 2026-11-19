import { useEffect, useRef, useState } from "react";
import { MoonIcon, SettingsIcon, SunIcon, SystemIcon } from "./Icons";

const OPTIONS = [
  { value: "system", label: "System", Icon: SystemIcon },
  { value: "light", label: "Light", Icon: SunIcon },
  { value: "dark", label: "Dark", Icon: MoonIcon },
];

export default function Settings({ theme, onTheme }) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    function onKey(e) { if (e.key === "Escape") setOpen(false); }
    function onClick(e) { if (!wrapRef.current?.contains(e.target)) setOpen(false); }
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClick);
    };
  }, [open]);

  return (
    <div className="settings" ref={wrapRef}>
      <button
        type="button"
        className="icon-btn"
        aria-label="Settings"
        aria-expanded={open}
        aria-controls="settings-panel"
        onClick={() => setOpen((o) => !o)}
      >
        <SettingsIcon />
      </button>
      {open && (
        <div className="settings-panel" id="settings-panel" role="group" aria-label="Settings">
          <p className="settings-title" id="theme-label">Appearance</p>
          <div className="seg" role="radiogroup" aria-labelledby="theme-label">
            {OPTIONS.map(({ value, label, Icon }) => (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={theme === value}
                className="seg-opt"
                onClick={() => onTheme(value)}
              >
                <Icon />
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
