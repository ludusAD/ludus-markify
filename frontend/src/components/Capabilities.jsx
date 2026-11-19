// What the converter reads, what to expect, and what it cannot do.
// Kept in step with ludus_markify/conversion.py (_UNSUPPORTED) and MarkItDown's converters.
const WORKS = [
  ["PDF", "Text and tables, page by page."],
  ["Word (.docx)", "Headings, lists, tables, bold, italics and links."],
  ["PowerPoint (.pptx)", "One section per slide: titles, text, tables and speaker notes."],
  ["Excel (.xlsx, .xls) and CSV", "Each sheet becomes a table. Merged cells are filled in. Formulas show their last saved value."],
  ["HTML, text, JSON, XML", "Content kept as is. HTML becomes headings, links and tables."],
  ["Images (.jpg, .png)", "Text read from the picture, only when Tesseract is installed. A photo with no text gives nothing."],
  ["ZIP, EPUB, Outlook (.msg)", "Every file in a ZIP is converted. Books and emails come out as text."],
];

const EXPECT = [
  "You get the words and structure, not the look. Fonts, colours, columns and page layout are dropped.",
  "Pictures inside a document are not saved as image files.",
  "Complicated tables may come out simpler than the original.",
  "Check the preview before you rely on numbers or names. The text is copied, never corrected.",
  "Nothing is summarised or rewritten. No AI is used.",
];

const CANNOT = [
  "Scanned PDFs (a picture of each page) come out empty. There is no text to read.",
  "Old Word and PowerPoint files (.doc, .ppt), RTF, Apple Pages, Numbers and Keynote, and OpenDocument files. Save them as .docx, .pptx, .xlsx or PDF first.",
  "Audio and video.",
  "Password-protected files. Remove the password first.",
  "Web addresses. Files on this computer only.",
];

export default function Capabilities() {
  return (
    <section className="guide" aria-labelledby="guide-title">
      <h2 className="guide-title" id="guide-title">What it can convert</h2>
      <dl className="guide-list">
        {WORKS.map(([format, result]) => (
          <div key={format}>
            <dt>{format}</dt>
            <dd>{result}</dd>
          </div>
        ))}
      </dl>

      <h2 className="guide-title">What to expect</h2>
      <ul className="guide-bullets">
        {EXPECT.map((t) => <li key={t}>{t}</li>)}
      </ul>

      <h2 className="guide-title">What it cannot do</h2>
      <ul className="guide-bullets">
        {CANNOT.map((t) => <li key={t}>{t}</li>)}
      </ul>
    </section>
  );
}
