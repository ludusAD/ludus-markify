export default function FileRow({ result, selected, onSelect, onSave, saving }) {
  const ok = result.status === "ok";

  return (
    <div className={`file-row${selected ? " selected" : ""}${!ok ? " has-error" : ""}`}
      onClick={ok ? onSelect : undefined}
    >
      <span className={`status-dot ${ok ? "ok" : "error"}`} />
      <span className="file-name" title={result.input_name}>{result.input_name}</span>
      {ok ? (
        <button
          className="btn-save"
          onClick={(e) => { e.stopPropagation(); onSave(); }}
          disabled={saving}
        >
          {saving ? "Saving…" : "Save"}
        </button>
      ) : (
        <span className="error-msg" title={result.error}>{result.error}</span>
      )}
    </div>
  );
}
