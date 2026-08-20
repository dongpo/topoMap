# BUILD-06 — Independent Building DEMO Verification, Freeze & Presentation Completion Report

Completion date: 2026-08-20 (Asia/Taipei)

## 1. Verdict

**PASS — BUILD-06 IS COMPLETE AS AN INDEPENDENT, IMMUTABLE, DEMO-ONLY VERIFICATION AND FREEZE**

BUILD-06 independently revalidated the exact BUILD-05 execution package and canonical consumption
ledger without importing the BUILD-05 executor or using its private-source reader. It froze the
package, artifact, consumption, receipt, source commitments, privacy boundary, replay state, and a
new offline presentation under one Core-owned canonical identity.

A static browser DEMO now presents only the normalized non-geographic artifact. It begins at the
approved 45-degree hatch angle and permits user adjustment from 0 through 179 degrees in 1-degree
steps. The page is explicitly labeled non-official and DEMO-only, has no external network or
private-source dependency, and cannot execute or consume the BUILD-04 capability.

## 2. Exact predecessor and branch

| Item | Value | Result |
|---|---|---|
| Canonical repository | `https://github.com/dongpo/topoMap.git` | PASS |
| Required predecessor branch | `build/build-05-controlled-demo-execution` | PASS |
| Required predecessor SHA | `290625111ab7a4ecb8af41be168ca186d55d949c` | PASS |
| BUILD-05 package | `10c22339abb8d2eed489ae56a54214948213bad51a135e00f74e309931c98c97` | PASS |
| BUILD-05 consumption | `44ab99947d9cb196de6a4f5a5238b4af33eb306a911a104224774425c7ebb108` | PASS |
| BUILD-06 branch | `build/build-06-demo-verification-freeze` | PASS |
| Starting tracked worktree | clean | PASS |

## 3. Independent verification boundary

The BUILD-06 verifier reads exactly three tracked, non-private inputs:

1. the frozen BUILD-05 redacted execution package;
2. the independent BUILD-05 consumed-once ledger;
3. the static BUILD-06 DEMO presentation.

It does not import `build_contracts.demo_execution`, the BUILD resolution/source module, or any
OGR, subprocess, temporary-extraction, network, filesystem-write, or production runtime facility.
The verifier cannot repeat BUILD-05 execution and has no private archive path.

The implementation independently recomputes the package, artifact, consumption, receipt, ledger,
and BUILD-06 verification hashes with `nma.core.canonical_sha256`. It does not trust a BUILD-05
validator result as evidence for its own freeze.

## 4. Frozen input identities

| Input | File SHA-256 | Record SHA-256 |
|---|---|---|
| BUILD-05 execution package | `508e3378a698f869255485c5008fdb80ed670ce174a3b72092aab5160df7431c` | `10c22339abb8d2eed489ae56a54214948213bad51a135e00f74e309931c98c97` |
| BUILD-05 consumption ledger | `715a5445827b77308ec32a67efe74ac8e5ed29b9037ee543285270a4da1c9d47` | `44ab99947d9cb196de6a4f5a5238b4af33eb306a911a104224774425c7ebb108` |
| BUILD-06 static presentation | `de5f6d567810e42af915bdff167fb21e202967b98817e2ef8d2d494d0b47be2d` | n/a |

Any byte change in any input fails before a freeze can be accepted. Re-basing a file fingerprint
does not bypass semantic verification: changed privacy, coordinates, angle policy, ledger state,
or authority boundary still fails closed.

## 5. Artifact and privacy verification

The freeze independently confirms:

- artifact SHA-256:
  `9131df533365e2f42e01edb8988804b850b65e69b932c55b672e0addd3400d84`;
- receipt SHA-256:
  `c4ff4017c01aa3ef861530a91204fcd8357387a8400f4a47fcd637033f445573`;
- one closed ring with 65 vertices;
- exactly two derived coordinate dimensions;
- every derived coordinate lies within `[0, 1]`;
- coordinate space is `normalized-local-demo-not-geographic`;
- source geometry commitment remains
  `23f7d5adacfb468bf0105ed66bb6f64ac44b50e22c47a2399a4787f6051bb22f`;
- source attribute commitment remains
  `ddfa112586b9c2bc3a61bdf2638b7994ba1200bfce5d8ad34988f2a24da96078`;
- source geometry identity remains `PolygonZ`, 1 ring, 65 vertices;
- no raw geographic coordinate, raw source field, WKB, source annotation, or raw idempotency key
  appears in the frozen presentation path.

The canonical consumption ledger exactly equals the package consumption record and remains
`consumed-once` with `replay_allowed: false`.

## 6. Offline non-production DEMO presentation

`buildDemoV06.html` is a self-contained SVG presentation that fetches only the exact same-origin
BUILD-05 package and ledger. Before enabling the angle control, the browser verifies both files'
raw SHA-256 values, their exact record identities, ledger equality, consumed-once state, privacy
flags, normalized coordinate range, vertex count, and closed ring.

Presentation behavior:

- initial hatch angle: 45 degrees;
- adjustable range: 0 degrees inclusive to 180 degrees exclusive;
- step: 1 degree;
- boundary: solid `#111111`, one CSS pixel;
- hatch spacing: `7.559055118110236` CSS pixels;
- annotation: approved `樓層＋結構` placeholder;
- explicit `DEMO ONLY · 非正式圖式` authority banner;
- Content Security Policy restricted to same-origin resources;
- external scripts, styles, fonts, maps, network APIs, and production adapters: none.

Changing the angle updates only the SVG pattern transform in the page. It does not modify the
BUILD-05 package, create a new ledger entry, read a source, or persist a new decision.

## 7. Browser acceptance

The presentation was served from a sanitized temporary directory containing only the HTML,
redacted BUILD-05 package, and consumption ledger. The repository root and ignored private archive
were never exposed by the preview server. The temporary server and directory were removed after
acceptance.

Observed acceptance:

- package and ledger verification status: passed;
- initial control value: 45 degrees;
- change to 120 degrees: output `120°`, SVG pattern `rotate(120)`;
- reset: output `45°`, SVG pattern `rotate(45)`;
- desktop layout: passed;
- 390-pixel responsive layout: passed, no horizontal overflow;
- slider enabled only after verification: passed;
- browser console warnings: 0;
- browser console errors: 0.

## 8. Freeze identity and policy

Golden BUILD-06 verification/freeze SHA-256:

`bc636eb1eed7e055306b7271d2cf169c05a4990ab37cebf0b9f89288d53e7857`

The freeze is `accepted-frozen-demo-only` and immutable. It permits only verification or
presentation of this exact normalized DEMO artifact without source access. It forbids:

- re-consuming the BUILD-04 authorization;
- repeating BUILD-05 execution;
- private-source dependency;
- raw coordinate or attribute disclosure;
- network dependency;
- production runtime wiring or activation;
- promotion of DEMO semantics to official authority.

Any broader change requires a new explicit human gate.

## 9. Acceptance results

Environment:

- Python 3.13.5;
- pytest 9.1.1;
- Ruff static acceptance passed;
- JSON and Draft 2020-12 schema validation passed;
- in-app browser desktop and responsive acceptance passed.

Results:

- BUILD-06 focused acceptance: **31 passed**;
- BUILD-00A through BUILD-06 chain acceptance: **273 passed**;
- complete repository regression: **875 collected; 872 passed; 3 failed**.

The three failures are the exact known, pre-existing Agentic/demo drift:

1. `tests/test_agentic_demo_catalog.py::test_pmtiles_capability_catalog_is_reproducible`
2. `tests/test_agentic_freeze.py::test_agentic_v03_freeze_verifies_current_and_historical_boundaries`
3. `tests/test_agentic_v03_pages.py::test_agentic_v03_pages_candidate_preserves_v02_and_passes_every_gate`

No BUILD, Core, ROAD, School Hero, Agent contract, source-integrity, freeze-provider, or production
runtime regression was introduced.

## 10. Exact changed files

1. `BUILD-06-Completion-Report.md` — independent verification, browser acceptance, freeze policy, tests, and readiness.
2. `buildDemoV06.html` — offline, clearly labeled, normalized-artifact-only interactive DEMO.
3. `build_contracts/__init__.py` — BUILD-06 public verifier/freeze exports.
4. `build_contracts/demo_freeze.py` — independent read-only verification and immutable freeze construction.
5. `data/specifications/nma-build-06-golden-verification-freeze-v1.0.json` — frozen BUILD-06 identity and evidence.
6. `schemas/build-demo-verification-freeze-v1.0.schema.json` — closed Draft 2020-12 exact freeze schema.
7. `tests/test_build_demo_verification_freeze_build06.py` — identity, privacy, drift, authority, presentation, and no-source acceptance.

Existing production `src/nma` changed: **no**.

BUILD-00A through BUILD-05 golden artifacts, frozen Core, ROAD, School Hero, Agent, production
runtime, official portrayal evidence, and private archive files changed: **no**.

## 11. Next-stage recommendation

**HOLD — NO AUTOMATIC BUILD-07 OR PRODUCTION ENTRY. A NEW EXPLICIT HUMAN GATE IS REQUIRED.**

The existing BUILD authorization chain ends with this immutable DEMO-only freeze. A future phase
may continue only after the human project owner explicitly defines whether its purpose is DEMO
evaluation, portrayal revision, a new source-bound execution, or production adoption. Until that
decision is recorded, BUILD-06 may be viewed and verified, but its semantics remain non-official
and cannot be promoted or executed again.
