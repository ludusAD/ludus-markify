const R = 28;
const C = 2 * Math.PI * R;

// Fills as files finish. With a single file there is no honest percentage, so it spins instead.
export default function ProgressRing({ done, total }) {
  const spinning = total <= 1;
  const pct = total ? Math.round((done / total) * 100) : 0;
  const label = spinning ? "Converting…" : `Converting file ${Math.min(done + 1, total)} of ${total}`;

  return (
    <div
      className="ring"
      role="progressbar"
      aria-label="Conversion progress"
      aria-valuemin={spinning ? undefined : 0}
      aria-valuemax={spinning ? undefined : 100}
      aria-valuenow={spinning ? undefined : pct}
    >
      <svg viewBox="0 0 64 64" width="64" height="64" aria-hidden="true">
        <circle className="ring-track" cx="32" cy="32" r={R} />
        <circle
          className={`ring-arc${spinning ? " ring-spin" : ""}`}
          cx="32"
          cy="32"
          r={R}
          strokeDasharray={C}
          strokeDashoffset={spinning ? C * 0.72 : C * (1 - pct / 100)}
          transform="rotate(-90 32 32)"
        />
      </svg>
      {!spinning && <span className="ring-pct">{pct}%</span>}
      <span className="ring-label">{label}</span>
    </div>
  );
}
