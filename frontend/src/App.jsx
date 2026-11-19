import { useState } from "react";
import DropZone from "./components/DropZone";
import FileRow from "./components/FileRow";
import Preview from "./components/Preview";
import ProgressRing from "./components/ProgressRing";
import Capabilities from "./components/Capabilities";
import Settings from "./components/Settings";
import { useTheme } from "./theme";
import { bundleFiles, convertFiles, saveFile } from "./api";
import { downloadText, formatBytes, formatTokens } from "./format";
import "./App.css";

const HOSTED = import.meta.env.VITE_HOSTED === "true";

export default function App() {
  const [theme, setTheme] = useTheme();
  const [queued, setQueued] = useState([]);   // File objects waiting to convert
  const [results, setResults] = useState([]); // ConversionResult[]
  const [selected, setSelected] = useState(null); // index into results
  const [outputDir, setOutputDir] = useState("");
  const [converting, setConverting] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [convertError, setConvertError] = useState("");
  const [trim, setTrim] = useState(false);       // show and save the token-trimmed text
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState({});      // input_name -> saved path
  const [saveMsg, setSaveMsg] = useState({ text: "", error: false });

  function addFiles(files) {
    setQueued((prev) => {
      const existing = new Set(prev.map((f) => f.name));
      return [...prev, ...files.filter((f) => !existing.has(f.name))];
    });
    setConvertError("");
  }

  function removeQueued(name) {
    setQueued((prev) => prev.filter((f) => f.name !== name));
  }

  const textOf = (r) => (trim ? r.trimmed_markdown : r.markdown);

  function startOver() {
    setQueued([]);
    setResults([]);
    setSelected(null);
    setSaved({});
    setSaveMsg({ text: "", error: false });
    setConvertError("");
  }

  async function handleConvert() {
    if (!queued.length) return;
    setConverting(true);
    setConvertError("");
    setProgress({ done: 0, total: queued.length });
    // One request per file: the ring shows real progress, and one failure never stops the rest.
    const res = [];
    for (const file of queued) {
      try {
        const [r] = await convertFiles([file]);
        res.push(r);
      } catch (e) {
        res.push({
          input_name: file.name, status: "error", markdown: "", error: `The app did not answer (${e.message}). Check that it is still running.`,
          tokens: 0, trimmed_markdown: "", trimmed_tokens: 0,
        });
      }
      setProgress((p) => ({ ...p, done: p.done + 1 }));
    }
    setResults(res);
    setSaved({});
    setSaveMsg({ text: "", error: false });
    const firstOk = res.findIndex((r) => r.status === "ok");
    setSelected(firstOk >= 0 ? firstOk : null);
    setConverting(false);
  }

  async function saveMany(indexes) {
    if (!outputDir.trim()) {
      setSaveMsg({ text: "Type the folder to save into first.", error: true });
      return;
    }
    setSaving(true);
    setSaveMsg({ text: "", error: false });
    const done = {};
    let failed = "";
    for (const i of indexes) {
      const r = results[i];
      try {
        const data = await saveFile(r.input_name, textOf(r), outputDir.trim());
        done[r.input_name] = data.saved_path;
      } catch (e) {
        failed = e.message;
        break;
      }
    }
    setSaved((prev) => ({ ...prev, ...done }));
    const n = Object.keys(done).length;
    if (failed) {
      setSaveMsg({ text: `${n ? `Saved ${n}, then stopped. ` : ""}${failed}`, error: true });
    } else {
      const last = Object.values(done).at(-1);
      setSaveMsg({
        text: n === 1 ? `Saved to ${last}` : `Saved ${n} files to ${outputDir.trim()}`,
        error: false,
      });
    }
    setSaving(false);
  }

  async function saveBundle() {
    const items = okIndexes.map((i) => ({ input_name: results[i].input_name, markdown: textOf(results[i]) }));
    setSaveMsg({ text: "", error: false });
    try {
      const bundle = await bundleFiles(items);
      if (HOSTED) {
        downloadText(bundle.filename, bundle.markdown);
        setSaveMsg({ text: `Downloaded ${bundle.filename} (${formatTokens(bundle.tokens)})`, error: false });
        return;
      }
      if (!outputDir.trim()) {
        setSaveMsg({ text: "Type the folder to save into first.", error: true });
        return;
      }
      setSaving(true);
      const data = await saveFile(bundle.filename, bundle.markdown, outputDir.trim());
      setSaveMsg({ text: `Saved to ${data.saved_path} (${formatTokens(bundle.tokens)})`, error: false });
    } catch (e) {
      setSaveMsg({ text: e.message, error: true });
    } finally {
      setSaving(false);
    }
  }

  const stage = results.length ? "review" : queued.length ? "ready" : "empty";
  const okIndexes = results.flatMap((r, i) => (r.status === "ok" ? [i] : []));
  const totalTokens = okIndexes.reduce((sum, i) => sum + (trim ? results[i].trimmed_tokens : results[i].tokens), 0);

  return (
    <div className="app">
      <header className="top">
        <span className="wordmark">Ludus Markify</span>
        <div className="top-right">
          <span className="top-note">
            {HOSTED ? "Files are converted in memory and discarded immediately." : "Runs on this computer. Nothing is uploaded."}
          </span>
          <Settings theme={theme} onTheme={setTheme} />
        </div>
      </header>

      {stage !== "review" && (
        <main className="intake">
          <h1 className="intake-title">Turn documents into Markdown.</h1>
          <p className="intake-sub">
            {HOSTED
              ? "Nothing is stored or visible, not to us, not to anyone."
              : "Choose your files, convert them, then save plain .md files in any folder."}
          </p>

          {stage === "empty" ? (
            <>
              <DropZone onFiles={addFiles} />
              <Capabilities />
            </>
          ) : (
            <>
              <ul className="queue">
                {queued.map((f) => (
                  <li key={f.name}>
                    <span className="queue-name">{f.name}</span>
                    <span className="queue-size">{formatBytes(f.size)}</span>
                    <button type="button" className="btn-quiet" onClick={() => removeQueued(f.name)} aria-label={`Remove ${f.name}`}>
                      Remove
                    </button>
                  </li>
                ))}
              </ul>

              <div className="intake-actions">
                <button type="button" className="btn-primary" onClick={handleConvert} disabled={converting}>
                  {converting ? "Converting…" : `Convert ${queued.length} ${queued.length === 1 ? "file" : "files"}`}
                </button>
                {!converting && <DropZone onFiles={addFiles} compact />}
              </div>
              {converting && <ProgressRing done={progress.done} total={progress.total} />}
            </>
          )}

          {convertError && <p className="notice notice-error" role="alert">{convertError}</p>}
        </main>
      )}

      {stage === "review" && (
        <main className="review">
          <aside className="results">
            <h2 className="results-title">
              {okIndexes.length === results.length
                ? `${results.length} ${results.length === 1 ? "file" : "files"} converted`
                : `${okIndexes.length} of ${results.length} converted`}
            </h2>
            <p className="results-total">{formatTokens(totalTokens)} in total</p>
            <ul className="rows">
              {results.map((r, i) => (
                <FileRow
                  key={r.input_name}
                  result={r}
                  selected={selected === i}
                  saved={Boolean(saved[r.input_name])}
                  trim={trim}
                  onSelect={() => setSelected(i)}
                />
              ))}
            </ul>

            {okIndexes.length > 0 && (
              <label className="check">
                <input type="checkbox" checked={trim} onChange={(e) => setTrim(e.target.checked)} />
                <span>
                  Trim for AI
                  <small>Removes embedded images, page numbers, repeated headers and extra spacing. Saves tokens.</small>
                </span>
              </label>
            )}

            <div className="results-foot">
              {!HOSTED && okIndexes.length > 0 && (
                <>
                  <label className="field-label" htmlFor="out-dir">Save into this folder</label>
                  <input
                    id="out-dir"
                    className="field"
                    type="text"
                    placeholder="~/Documents"
                    value={outputDir}
                    onChange={(e) => setOutputDir(e.target.value)}
                    spellCheck={false}
                  />
                  <button type="button" className="btn-primary" onClick={() => saveMany(okIndexes)} disabled={saving}>
                    {saving ? "Saving…" : okIndexes.length > 1 ? "Save all Markdown" : "Save Markdown"}
                  </button>
                  {okIndexes.length > 1 && (
                    <button type="button" className="btn-quiet" onClick={saveBundle} disabled={saving}>
                      Save as one file
                    </button>
                  )}
                  <p className={`notice${saveMsg.error ? " notice-error" : ""}`} role="status">{saveMsg.text}</p>
                </>
              )}
              {HOSTED && okIndexes.length > 1 && (
                <button type="button" className="btn-quiet" onClick={saveBundle}>Download as one file</button>
              )}
              {HOSTED && <p className={`notice${saveMsg.error ? " notice-error" : ""}`} role="status">{saveMsg.text}</p>}
              <button type="button" className="btn-quiet" onClick={startOver}>Start over</button>
            </div>
          </aside>

          <Preview
            result={selected !== null ? results[selected] : null}
            text={selected !== null ? textOf(results[selected]) : ""}
            hosted={HOSTED}
            saving={saving}
            onSave={() => saveMany([selected])}
          />
        </main>
      )}
    </div>
  );
}
