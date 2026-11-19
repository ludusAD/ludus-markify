export function formatBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${Math.round(n / 1024)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export function countWords(text) {
  const t = text.trim();
  return t ? t.split(/\s+/).length : 0;
}

export function mdName(inputName) {
  return inputName.replace(/\.[^.]+$/, "") + ".md";
}

export function formatTokens(n) {
  return `≈ ${n.toLocaleString()} tokens`;
}

// Browser download of text as a file (hosted mode has no save-to-folder).
export function downloadText(name, text) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/markdown;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}
