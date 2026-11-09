# Resume project — agent notes

Single-page HTML resume (Tailwind via CDN, Inter font) that is also exported to PDF.

- `Jon Zeolla Resume.html` — the canonical resume. Edit this one. It lives outside `public/` and
  `src/` on purpose: only the PDF is published on jonzeolla.com, never the HTML.
- `../public/resume.pdf` — generated from the HTML (see below). Never hand-edit.

## Layout constraints

- The page is a fixed US-Letter sheet: `body`/`.page-container` are `8.5in` × `11in`.
- Everything must fit on **one page**. Content past `11in` is clipped, not paginated.
- After any content/spacing change, verify it still fits (render and measure, don't eyeball).

## Generating the PDF

Use `print-pdf.mjs` (Node, no deps — drives headless Chrome over the DevTools Protocol). Its one
real advantage over the plain CLI is that it **waits for the live contribution-graph image**
(`ghchart.rshah.org`) to finish loading before printing, so the graph is never blank:

```bash
node resume/print-pdf.mjs   # from the repo root; writes public/resume.pdf
```

It takes an optional `<file-url> <out.pdf>` pair to print something else.

`@page { size: letter; margin: 0 }` in the HTML controls page size/margins.

The script prints with `generateTaggedPDF: false` (an untagged PDF). This is a leftover from
debugging and has **no effect on the data-detector box** (gotcha #3 — that box is purely
text-level; the box appeared on tagged and untagged PDFs alike). Tagged vs untagged is only an
accessibility/ATS consideration; the plain `--print-to-pdf` CLI (which tags) would be fine too
if you also pass `--virtual-time-budget` so the graph loads.

## PDF gotchas — READ BEFORE TOUCHING LINKS, IMAGES, OR OVERFLOW

**Gotcha #3 (macOS data detectors) is the one that actually caused the dotted hover box, and it
caused it repeatedly. Start there.** #1 and #2 below are smaller, real-but-cosmetic precautions —
they did NOT cause the dotted box (we proved that: removing the oversized annotation and switching
to `overflow: clip` both left the box untouched).

### 1. Do NOT wrap large/full-width elements in an `<a>`

Wrapping a big block (e.g. the full-width contribution-graph `<img class="w-full">`) in an
anchor makes Chrome's print-to-PDF emit a **full-width link annotation** — and here Chrome also
emitted a *duplicate* annotation with a stray neighboring `href`, so the graph would have linked
to the wrong URL. This is a link-annotation hygiene issue, NOT the dotted hover box (that's
gotcha #3).

- **Deliberate exception (Sep 2026):** the contribution graph `<img>` IS wrapped in
  `<a href="https://github.com/jonzeolla" class="block">` at the user's request, so clicking the
  graph in the PDF opens GitHub. This was verified clean: exactly ONE large (~401x62pt) `/Link`
  annotation, whose `/URI` is `https://github.com/jonzeolla`, and no duplicate with a stray href.
  So the scan below will report one large annotation — that one is expected. Anything else large,
  or a large one with a different URI, is the bug. Don't "fix" this by unwrapping the graph.
- For any other large block, keep it non-clickable and link from small text instead.
- Symptom to watch for: an unexpected oversized link annotation in the PDF. Quick check (prints
  the URI so you can tell the expected graph link from a stray one):

  ```bash
  python3 - <<'PY'
  import re
  d=open("public/resume.pdf","rb").read()
  for m in re.finditer(rb'<<[^>]*?/Subtype\s*/Link[^>]*?>>', d, flags=re.S):
      obj=m.group(0)
      r=re.search(rb'/Rect\s*\[([^\]]+)\]',obj); u=re.search(rb'/URI\s*\(([^)]*)\)',obj)
      if not r: continue
      rr=[float(x) for x in r.group(1).split()]; w=round(rr[2]-rr[0]); h=round(rr[3]-rr[1])
      if w>200 and h>30: print("LARGE", f"{w}x{h}", u.group(1).decode() if u else "(no inline URI)")
  PY
  ```

  Expected output: exactly one `LARGE ... https://github.com/jonzeolla` line (the graph). Normal
  inline text links are small (tens of points). Any other wide-AND-tall annotation is the bug.

### 2. Prefer `overflow: clip` over `overflow: hidden` on layout containers (precaution only)

A known Chrome behavior: an `overflow: hidden` element whose content overflows can be exported
as a scroll container with a scrollable-region annotation. We use `overflow: clip` (clips the
same, no scroll container) on `.page-container`, `aside`, `main`, `body` and the `@media print`
block as a precaution. **Note:** no such annotation was ever actually found in this project, and
this was NOT the cause of the dotted box (gotcha #3). Harmless to keep; don't expect it to fix
anything.

### 3. The dotted box + chevron = macOS data detectors on the TEXT LAYER

This was the persistent one, and the cause is NOT annotations or tags — it's macOS Preview's
**Data Detectors** reading the PDF's text layer, finding anything that looks like a date,
address, phone number, link, or flight, and drawing a **dotted box with a chevron** with
actions ("Add to Calendar", etc.) on hover. (It is a Preview/Quick Look hover feature; it never
prints and doesn't appear in Acrobat/Chrome. But it looks broken, so kill it.) Dead ends that
did NOT fix it: `overflow: clip`, removing oversized link annotations, and generating an
untagged PDF — the box survived all three.

**Check ALL detector types, not just dates.** The first pass only checked `.date` and missed a
`.link` false-positive ("Senior Sec·uri·t·y Engineer"), so a box came back. Preview uses date +
address + phone + link + transit — check all five.

**Reproduce / verify with the exact engine Preview uses** — Apple's `NSDataDetector` (Swift, no
deps). Target is **0 matches**:

```bash
cat > /tmp/d.swift <<'SWIFT'
import Foundation; import PDFKit
let t = PDFDocument(url: URL(fileURLWithPath: CommandLine.arguments[1]))!.string ?? ""
let types: NSTextCheckingResult.CheckingType = [.date, .address, .phoneNumber, .link, .transitInformation]
let det = try! NSDataDetector(types: types.rawValue)
let m = det.matches(in: t, range: NSRange(t.startIndex..., in: t))
print("matches:", m.count)
for x in m { if let r = Range(x.range, in: t) { print("  [\(x.resultType.rawValue)] \"\(t[r])\"") } }
SWIFT
swift /tmp/d.swift public/resume.pdf
```

Trigger types seen here (note: the experience `2023 to Present` ranges were NOT among them):

1. **Real words.** `"Today"` (the summary's "Today, Jon is…") reads as a date.
2. **Word fragments — the sneaky one.** Chrome splits PDF text runs mid-word, and a stray
   fragment reads as a date/link: `GitHub` → `Gi tHu b` (the `tHu` → *Thursday*, the box over
   Experience), and `Security` → `Sec uri t y` (read as a *link*). The clean, unfragmented words
   do NOT match — only the fragments do, so you can't predict them by eye; you must run the
   detector. CSS can't stop the fragmentation (`font-kerning`, `font-feature-settings`,
   `text-rendering`, `letter-spacing` were all tried and did nothing).
3. **The contribution graph's text.** The live `ghchart` SVG embeds selectable vector text
   (`Mon`/`Wed`/`Fri` day labels, month labels); `Fri` reads as *Friday*.

**Fixes (verified to take the all-types detector to 0):**

- Real words and fragmentation-prone words: insert a **zero-width space** (`&#8203;`) inside the
  token. Invisible, still reads/copies as the word, but breaks the match. Used here:
  `To&#8203;day`, `Git&#8203;Hub`, `Sec&#8203;urity` (in "Senior Security Engineer"). After ANY
  text change, re-run the all-types detector and ZWSP any new hit.
- The graph image: add `style="filter: saturate(1.001)"` to the `<img>`. A near-identity filter
  forces Chrome to flatten the SVG to a bitmap, so its label text leaves the PDF text layer
  entirely (and the graph still loads live). Do NOT wrap the graph in an `<a>` (gotcha #1).

`print-pdf.mjs` also emits an **untagged** PDF (`generateTaggedPDF: false`); harmless and tidy,
but it was not the cure — the date-text fixes above are.

## Verifying a change

1. Render the HTML (e.g. headless Chrome / a browser) and confirm content ends before `11in`
   with the footer clear — it must stay one page.
2. Regenerate the PDF with `print-pdf.mjs` and re-run the checks: oversized-annotation scan
   (expect 0) and the all-types `NSDataDetector` swift check from gotcha #3 (expect **0 matches**
   — this is the one that catches the dotted-box regression).
3. Confirm real hyperlinks survive (each external URL should be a small `/Link` annotation).
