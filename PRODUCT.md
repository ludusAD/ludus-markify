# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Non-technical people with documents on their own computer (PDF, Word, Excel, PowerPoint, HTML, images) who need Markdown versions. They use the Markdown for AI tools, notes and wikis, and plain-text archives and search. They are not developers and should never meet a terminal after the first run command. A secondary audience is developers who run, extend, or self-host the open-source repo.

## Product Purpose

Local-first converter: choose files, convert with Microsoft MarkItDown, preview the Markdown, save `.md` files to a folder. Success means a batch converts without surprises, each file shows a clear success or failure, and a failed file never blocks the rest. No cloud upload in the default flow.

## Positioning

Conversion happens on the user's own machine, so documents never leave it. The hosted mode converts in memory and stores nothing, but local use is the primary promise.

## Operating Context

- Primary: `uvx ludus-markify` (PyPI package) starts a local server on 127.0.0.1 and opens the browser UI. Dev mode: FastAPI backend plus Vite frontend.
- Also: a hosted site (HOSTED mode, ludus-technology.com) for people who will not install anything. Hosted disables save-to-disk and offers a download button instead.
- Output folder is a typed path, since browsers cannot return a native folder path.

## Capabilities and Constraints

- v1 scope: select files, convert, preview, save `.md`, per-file success or error status. Save never overwrites (`report (1).md`).
- Not in v1: OCR tuning UI, remote URLs, cloud processing, accounts, vector DB, embeddings, sync, plugin marketplace, complex settings. No LLM features, auth, analytics, or telemetry.
- Architecture: UI, application, conversion (single MarkItDown adapter), filesystem layers. UI holds no conversion or filesystem logic.
- Image OCR needs Tesseract installed; it is optional.
- Plain language in the UI: "Choose files", "Convert", "Save Markdown". One main action per screen. Fewer options.

## Brand Commitments

Product name is "Ludus Markify". No binding visual identity: Ludus Technology logo, palette and voice are not required (confirmed by the user). Open-source (MIT).

## Evidence on Hand

No testimonials, customers, benchmarks, or usage data exist. Do not invent them. The repo, README and tests are the only proof assets.

## Product Principles

- Local by default; never imply a document leaves the machine unless in hosted mode, where say so plainly.
- One clear next step on every screen; a batch must feel as simple as one file.
- Failures are specific and recoverable; one bad file never stops the others.
- Show the actual Markdown the user will get, not only a pretty render.
- Narrow v1: resist options and features that are not pick, convert, preview, save.
