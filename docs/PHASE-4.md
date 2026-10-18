# Phase 4: research for all eleven companies

All eleven configured companies have a source-pack identity and tailored research
questions: NBIS, META, DLO, FTAI, LMND, SNDK, IREN, Next Vision, Enlight, BrainsWay
and Gilat Telecom. The four Israeli entries retain distinct company IDs without
inventing or verifying exchange symbols. Gilat Telecom is not Gilat Satellite
Networks. Existing editable watchlists and holdings remain separate from this
reviewed source registry. A user-added company can use document reading and
research import under its local security identity; this does not provision an
automatic official source.

Each reviewed company source is attempted in the public collector, bounded to
240 seconds for the total pilot source step, eight index links per source and
three detail checks for NBIS/IREN/DLO or one for other companies. A timeout leaves
an explicit failed status and retains prior items. Known official portals can
return 403 or require JavaScript; coverage must not be inferred from a successful
workflow. Gilat Telecom's corporate page is a source for review, not a claim to
complete exchange-announcement coverage. Public collection still saves metadata,
not full release bodies. Up to 24 retained items per company (264 total).

The document reader works on a user-selected local PDF or TXT. PDF.js is bundled
and loaded on demand with its same-origin worker. Maximum file size is 8 MiB;
PDF extraction is limited to an explicit range of 1–20 pages per request, 100,000
characters and a 45-second task timer. No OCR or PDF layout analysis is offered.
Tables, units and Hebrew text order must be checked against the original. Text
is displayed for review and is neither uploaded nor saved automatically. The
prompt includes the exact extraction range and a user-supplied source URL (or
an explicit missing-source statement). Source text is untrusted data, not model
instructions. There is no API inference, automatic chat submission or paid data.

Source packs, existing research prompts and document prompts request the same
version-1 JSON exchange format: `companyId`, `asOf`, all eleven string research
fields, HTTPS `sourceUrls`, and `missing`. A matching identity, real calendar date,
field limits, URL safety and payload bounds are checked. Schema validity does
not verify financial facts or source access. The preview compares old/new text;
only selected nonempty fields change. Notes and unselected fields remain intact.

Applying an import changes the draft; the existing save/autosave flow persists it.
The last import is labeled user-imported with its declared research date, local
import timestamp, applied fields, claimed sources and missing information. Three
previous field snapshots are retained and may be loaded into the draft. Notes
are shared personal annotations, not rolled back with field versions. Metadata
and history are included in the existing full-state JSON backup and validated on
reload; old version-1 backups without these optional fields remain supported.
A failed storage write does not claim persistence.

Tests cover all eleven identities and contracts, company mismatch, invalid dates,
unsafe URLs, oversized payloads, selective nonempty application, notes, history,
backup reload, explicit preview/apply, local document prompts and bounded file
reading. PR and publication mobile checks exercise a real in-memory PDF through
the bundled worker, research import, preview/apply/save and local persistence at
320/390/430 widths, in addition to existing RTL and keyboard emulation. These are
headless Chromium checks, not physical Android/OCR fidelity certification.
