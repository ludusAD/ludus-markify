import { useRef, useState } from "react";

const FORMATS = ["PDF", "Word", "Excel", "PowerPoint", "HTML", "Text", "Images"];

export default function DropZone({ onFiles, compact = false }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length) onFiles(files);
  }

  function handleChange(e) {
    const files = Array.from(e.target.files);
    if (files.length) onFiles(files);
    e.target.value = "";
  }

  return (
    <div
      className={`drop${compact ? " drop-compact" : ""}${dragging ? " drop-active" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <input ref={inputRef} id="file-input" type="file" multiple hidden onChange={handleChange} />
      {compact ? (
        <button type="button" className="btn-quiet" onClick={() => inputRef.current.click()}>
          Add more files
        </button>
      ) : (
        <>
          <p className="drop-title">Drop documents here</p>
          <button type="button" className="btn-primary" onClick={() => inputRef.current.click()}>
            Choose files
          </button>
          <p className="drop-formats">{FORMATS.join(", ")}, and more</p>
        </>
      )}
    </div>
  );
}
