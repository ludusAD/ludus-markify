import { useMemo, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { mdName } from "../format";

export default function Preview({ result, text, hosted, onSave, saving }) {
  const [view, setView] = useState("rendered");
  const [copied, setCopied] = useState(false);
  const lineNumbers = useMemo(() => {
    if (!result) return "";
    const n = text.split("\n").length;
    return Array.from({ length: n }, (_, i) => i + 1).join("\n");
  }, [result, text]);

  if (!result) {
    return (
      <div className="preview-empty">
        <p>Choose a converted file to read its Markdown.</p>
      </div>
    );
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  const blank = text.trim() === "";

  return (
    <section className="preview" aria-label={`Preview of ${result.input_name}`}>
      <div className="preview-bar">
        <div className="tabs" role="tablist" aria-label="Preview style">
          <button type="button" role="tab" aria-selected={view === "rendered"} onClick={() => setView("rendered")}>
            Rendered
          </button>
          <button type="button" role="tab" aria-selected={view === "markdown"} onClick={() => setView("markdown")}>
            Markdown
          </button>
        </div>
        <div className="preview-actions">
          <button type="button" className="btn-quiet" onClick={copy}>
            {copied ? "Copied" : "Copy"}
          </button>
          {hosted ? (
            <a
              className="btn-quiet"
              href={`data:text/markdown;charset=utf-8,${encodeURIComponent(text)}`}
              download={mdName(result.input_name)}
            >
              Download .md
            </a>
          ) : (
            <button type="button" className="btn-quiet" onClick={onSave} disabled={saving}>
              {saving ? "Saving…" : "Save this file"}
            </button>
          )}
        </div>
      </div>

      <div className="sheet-wrap">
        {blank ? (
          <p className="preview-empty">No text found in this file. Scanned pages and photos need Tesseract installed.</p>
        ) : view === "rendered" ? (
          <article className="sheet prose">
            <Markdown remarkPlugins={[remarkGfm]}>{text}</Markdown>
          </article>
        ) : (
          <div className="sheet raw" tabIndex={0}>
            <pre className="raw-gutter" aria-hidden="true">{lineNumbers}</pre>
            <pre className="raw-text">{text}</pre>
          </div>
        )}
      </div>
    </section>
  );
}
