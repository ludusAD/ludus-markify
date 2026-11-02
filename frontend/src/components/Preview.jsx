import Markdown from "react-markdown";

export default function Preview({ result }) {
  if (!result) {
    return (
      <div className="preview-empty">
        <p>Select a converted file to preview its Markdown</p>
      </div>
    );
  }

  return (
    <div className="preview-content">
      <div className="preview-header">{result.input_name}</div>
      <div className="preview-body">
        <Markdown>{result.markdown}</Markdown>
      </div>
    </div>
  );
}
