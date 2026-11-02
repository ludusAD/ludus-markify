import { useState } from "react";
import DropZone from "./components/DropZone";
import FileRow from "./components/FileRow";
import Preview from "./components/Preview";
import { convertFiles, saveFile } from "./api";
import "./App.css";

export default function App() {
  const [queued, setQueued] = useState([]);   // File objects waiting to convert
  const [results, setResults] = useState([]); // ConversionResult[]
  const [selected, setSelected] = useState(null); // index into results
  const [outputDir, setOutputDir] = useState("");
  const [converting, setConverting] = useState(false);
  const [convertError, setConvertError] = useState("");
  const [savingIdx, setSavingIdx] = useState(null);
  const [savedMsg, setSavedMsg] = useState("");

  function addFiles(files) {
    setQueued((prev) => {
      const existing = new Set(prev.map((f) => f.name));
      return [...prev, ...files.filter((f) => !existing.has(f.name))];
    });
    setResults([]);
    setSelected(null);
    setConvertError("");
    setSavedMsg("");
  }

  function removeQueued(name) {
    setQueued((prev) => prev.filter((f) => f.name !== name));
  }

  async function handleConvert() {
    if (!queued.length) return;
    setConverting(true);
    setConvertError("");
    setResults([]);
    setSelected(null);
    setSavedMsg("");
    try {
      const res = await convertFiles(queued);
      setResults(res);
      const firstOk = res.findIndex((r) => r.status === "ok");
      setSelected(firstOk >= 0 ? firstOk : null);
    } catch (e) {
      setConvertError(e.message);
    } finally {
      setConverting(false);
    }
  }

  async function handleSave(idx) {
    if (!outputDir.trim()) {
      setSavedMsg("Please enter an output folder path first.");
      return;
    }
    setSavingIdx(idx);
    setSavedMsg("");
    try {
      const r = results[idx];
      const data = await saveFile(r.input_name, r.markdown, outputDir.trim());
      setSavedMsg(`Saved: ${data.saved_path}`);
    } catch (e) {
      setSavedMsg(`Error: ${e.message}`);
    } finally {
      setSavingIdx(null);
    }
  }

  const hasResults = results.length > 0;

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1 className="app-title">MarkItDown</h1>
        <p className="app-sub">Convert documents to Markdown locally</p>

        <DropZone onFiles={addFiles} />

        {queued.length > 0 && !hasResults && (
          <ul className="queued-list">
            {queued.map((f) => (
              <li key={f.name} className="queued-item">
                <span className="queued-name">{f.name}</span>
                <button className="btn-remove" onClick={() => removeQueued(f.name)}>✕</button>
              </li>
            ))}
          </ul>
        )}

        {queued.length > 0 && (
          <button
            className="btn-convert"
            onClick={handleConvert}
            disabled={converting}
          >
            {converting ? "Converting…" : `Convert ${queued.length} file${queued.length > 1 ? "s" : ""}`}
          </button>
        )}

        {convertError && <p className="error-banner">{convertError}</p>}

        {hasResults && (
          <>
            <div className="section-label">Results</div>
            <div className="file-list">
              {results.map((r, i) => (
                <FileRow
                  key={r.input_name}
                  result={r}
                  selected={selected === i}
                  onSelect={() => setSelected(i)}
                  onSave={() => handleSave(i)}
                  saving={savingIdx === i}
                />
              ))}
            </div>

            <label className="output-label">Output folder</label>
            <input
              className="output-input"
              type="text"
              placeholder="/path/to/output"
              value={outputDir}
              onChange={(e) => setOutputDir(e.target.value)}
            />
            {savedMsg && (
              <p className={`saved-msg${savedMsg.startsWith("Error") ? " saved-error" : ""}`}>
                {savedMsg}
              </p>
            )}

            <button className="btn-new" onClick={() => { setQueued([]); setResults([]); setSelected(null); setSavedMsg(""); }}>
              Convert more files
            </button>
          </>
        )}
      </aside>

      <main className="preview-pane">
        <Preview result={selected !== null ? results[selected] : null} />
      </main>
    </div>
  );
}
