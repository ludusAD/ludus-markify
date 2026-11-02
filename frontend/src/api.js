const BASE = "http://localhost:8000";

export async function convertFiles(files) {
  const form = new FormData();
  for (const f of files) form.append("files", f);
  const res = await fetch(`${BASE}/convert`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}

export async function saveFile(inputName, markdown, outputDir) {
  const res = await fetch(`${BASE}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input_name: inputName, markdown, output_dir: outputDir }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `Server error: ${res.status}`);
  return data;
}
