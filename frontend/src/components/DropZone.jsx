import { useRef, useState } from "react";

export default function DropZone({ onFiles }) {
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
      className={`dropzone${dragging ? " dragging" : ""}`}
      onClick={() => inputRef.current.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <input ref={inputRef} type="file" multiple hidden onChange={handleChange} />
      <span className="dropzone-icon">📄</span>
      <p>Choose files or drag them here</p>
      <p className="dropzone-sub">PDF, Word, Excel, PowerPoint, HTML, images, and more</p>
    </div>
  );
}
