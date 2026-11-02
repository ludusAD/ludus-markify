# CLAUDE.md
## Purpose
Build a local-first app that lets non-technical users select local documents, convert them to Markdown with MarkItDown, preview results, and save `.md` files locally. No cloud upload in the default flow.
## Product constraints
- Primary goal: simple, reliable local conversion.
- Secondary goal: clean open-source repo others can run and extend.
- Keep v1 narrow: pick files, convert, preview, save.
- Do not add LLM features, auth, sync, accounts, analytics, telemetry, or cloud storage unless explicitly requested.
## Architecture rules
Prefer a simple layered architecture:
1. UI layer: file picker, output picker, convert action, preview, save.
2. Application layer: orchestrates conversion jobs and error handling.
3. Conversion layer: thin wrapper around MarkItDown.
4. Filesystem layer: local read/write only.

Rules:
- Each layer should expose a small interface.
- UI must not contain conversion logic.
- Filesystem logic must not leak into UI components.
- Keep MarkItDown integration isolated behind one adapter.
- If packaging changes later, core conversion code should remain untouched.
## Data model first
Design around explicit data structures before writing UI behavior.
Prefer a small model such as:
- `InputFile`
- `ConversionJob`
- `ConversionResult`
- `AppState`
- `UserError`

If behavior feels complicated, simplify the data model first.[4][5]
## v1 scope
Build only this unless asked otherwise:
- Select one or more local files.
- Select output folder.
- Convert to Markdown locally.
- Preview converted Markdown.
- Save `.md` files locally.
- Show clear per-file success/error status.

Not in v1:
- OCR tuning UI
- remote URLs
- cloud processing
- user accounts
- vector DB
- embeddings
- background sync
- plugin marketplace
- complex settings
## UX rules
- Design for non-technical users.
- One main action per screen.
- Use plain language: “Choose files”, “Convert”, “Save Markdown”.
- Show progress and failures clearly.
- Default to safe local behavior.
- Prefer fewer options.
- Batch conversion must still feel simple.
## Testing
Test the simplest valuable behavior first:
- one supported file converts successfully
- multiple files convert independently
- invalid/unsupported file shows clear error
- output path/save behavior works
- app remains usable after a failed file

Prefer small focused tests near the changed code.
Do not build an elaborate test harness before the app works.
## Repo hygiene
- Keep README practical.
- Document how to run locally in as few steps as possible.
- Include a short architecture section.
- Include a screenshot once UI exists.
- Do not commit secrets, large binaries, or generated output.
