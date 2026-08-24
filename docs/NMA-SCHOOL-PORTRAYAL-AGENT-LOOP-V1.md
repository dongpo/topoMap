# NMA School portrayal Agent loop v1

## Outcome

This slice replaces the old `TERRAINID=9920103` and 15-point demo assumption with a plan built from
the School features actually observed in a user's `MARK` Shapefile. `9920100` is the classification
family; it is not used as a leaf filter. The supported leaves are `9920101` through `9920106`, and
there is no fixed feature-count limit in the portrayal planner.

The planner does not contain a second copy of the classification names or select a style from a
hard-coded route alone. For every observed leaf it asks the active read-only Knowledge Service for
the canonical code-list value, Annex 7 classification, Document 01 portrayal rule, symbol family,
line/colour evidence, and source citations. A missing or changed evidence path fails closed.

## Source gate

This component begins after the upload adapter has validated the Shapefile archive. Its input must
report the user `MARK` Point layer and the reviewed runtime binding `MARKID`, `TERRAINID`, and
`MARKNAME1`. Source identity is `zip-relative-filename + MARKID`; a single repeated source ID is not
treated as globally unique. Unknown codes, the family code `9920100`, missing schema bindings,
non-Point geometry, empty counts, and any claim that raw feature bytes were transmitted are rejected
before KG retrieval.

The upload adapter remains responsible for checking `.shp`, `.shx`, `.dbf`, and `.prj`, optional
`.cpg`, archive size, CRS decoding, and source-feature inspection. No upload bytes enter these
portrayal endpoints.

## Evidence-grounded portrayal

The official evidence currently separates the leaves as follows:

| `TERRAINID` | Class | Preview mode | Evidence |
| --- | --- | --- | --- |
| `9920101` | 大專院校 | school flag and name | Document 01 p.61; Annex 7 p.65 |
| `9920102` | 中學 | school flag and name | Document 01 p.61; Annex 7 p.65 |
| `9920103` | 小學 | school flag and name | Document 01 p.61; Annex 7 p.65 |
| `9920104` | 職訓中心 | name annotation only | Document 01 p.61; Annex 7 p.65 |
| `9920105` | 幼兒園 | name annotation only | Document 01 p.61; Annex 7 p.65 |
| `9920106` | 特殊學校 | school flag and name | Document 01 p.62; Annex 7 p.65 |

The shared School flag SVG is an implementation-derived preview resource, not authoritative source
geometry. Each compiled MapLibre layer keeps its exact rule, source section, and page binding. The
compiler returns style fragments only: it includes no GeoJSON, performs no map mutation, exports no
data, and never activates an official or production rule.

## Observable Agent loop

The server exposes five bounded operations. Plans, authorizations, and compiled results are
content-addressed and kept in a bounded in-memory registry for the active server session; a client
cannot forge an artifact by recomputing its public hash. The registry contains contracts only and
never stores Shapefile or GeoJSON bytes.

1. `POST /api/school-portrayal/proposals` validates the dataset observation, retrieves KG evidence,
   and returns a content-addressed plan.
2. `POST /api/school-portrayal/authorizations` records a human preview decision bound to exactly one
   plan hash.
3. `POST /api/school-portrayal/compile` compiles MapLibre resources and layers after authorization.
4. `POST /api/school-portrayal/observations` feeds the tool result back into the decision loop.
5. `POST /api/school-portrayal/verify` checks code coverage, render semantics, evidence binding,
   feature count, authorization, and the preview-only boundary.

The action observation changes the next decision. A successful compile moves to verification. A
style validation error makes the Agent abstain and stop. An SDF resource failure produces a revised
plan using the same reviewed SVG as a non-SDF black preview; the old authorization becomes invalid,
so a human must authorize the new plan. This is a small, measurable Agenticity result rather than a
claim that the full School/ROAD/BUILD Agenticity study is complete.

## Claim boundary and next integration

Canonical portrayal rules for these classes still report `activation_status=non-executable`.
Therefore this slice is an evidence-grounded, governed preview implementation, not official
production activation. Browser rendering may occur only after QA returns
`pass-ready-for-browser-render`.

The next UI integration should keep upload/schema/CRS validation local, send only the resulting
observation to these endpoints, show the evidence and authorization before map rendering, and feed
the actual MapLibre load/validation result back to the observation endpoint. ROAD and BUILD should
then implement the same loop with their own geometry and classification semantics rather than reuse
School-specific assumptions.
