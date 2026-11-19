import { countWords, formatTokens } from "../format";

export default function FileRow({ result, selected, saved, trim, onSelect }) {
  const ok = result.status === "ok";
  const text = trim ? result.trimmed_markdown : result.markdown;
  const words = ok ? countWords(text) : 0;
  const tokens = trim ? result.trimmed_tokens : result.tokens;
  const cut = trim && result.tokens > 0 ? Math.round((1 - result.trimmed_tokens / result.tokens) * 100) : 0;

  return (
    <li className={`row${selected ? " row-selected" : ""}${ok ? "" : " row-failed"}`}>
      {ok ? (
        <button type="button" className="row-main" onClick={onSelect} aria-pressed={selected}>
          <span className="row-name"><mark>{result.input_name}</mark></span>
          <span className="row-meta">
            {saved ? "Saved" : "Converted"} · {words.toLocaleString()} {words === 1 ? "word" : "words"} · {formatTokens(tokens)}
            {cut > 0 && ` (${cut}% less)`}
          </span>
        </button>
      ) : (
        <div className="row-main">
          <span className="row-name">{result.input_name}</span>
          <span className="row-meta row-error">Could not convert. {result.error}</span>
        </div>
      )}
    </li>
  );
}
