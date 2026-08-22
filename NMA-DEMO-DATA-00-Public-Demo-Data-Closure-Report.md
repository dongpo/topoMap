# NMA DEMO-DATA-00 — Public Demo Data Authority & Canonical Fixture Closure Report

**Repository:** `https://github.com/dongpo/topoMap.git`

**Branch:** `demo/demo-data-00-public-demo-data-closure`

**Exact remotely finalized predecessor:** `9e59237296ed3baed551db2bbd565234a1b02db5`

**Audit date:** `2026-08-22` (`Asia/Taipei`)

## 1. Verdict

> **FAIL — PUBLIC DEMO DATA AUTHORITY OR FROZEN CONTRACT COMPATIBILITY NOT CLOSED**

The requested PASS verdict is not defensible. Officially published and redistributable School and
ROAD source categories do exist, but neither can become an executable public-demo fixture through
the frozen domain paths without a post-freeze domain change:

1. School candidates do not establish the frozen six-layer MARK schema, 15-feature selection, or
   source-to-layer relationships. More importantly, this checkout has a HERO-03 authorization
   consumer/verifier but no production School authorization issuer. The repository's frozen
   governance evidence explicitly forbids inventing or emulating that issuer.
2. ROAD has a strong official open-data candidate, but ROAD-03 and ROAD-04 are intentionally bound
   to the one historical archive, fixture, route, class, segment set, authorization, and upstream
   identity chain. The issuer and verifier reject a new public fixture by design.

No fixture, fixture manifest, demo authorization, demo execution identity, or coordinate payload
was published. This is the required fail-closed outcome, not a partial PASS.

## 2. Canonical predecessor and branch gate

The starting checkout was `demo/demo-01b-public-domain-artifact-closure` at the requested
predecessor and contained an untracked DEMO-01B report. That report was preserved untouched and
used only as audit evidence. It was not treated as a commit, canonical predecessor, or public
fixture authority.

After `git fetch origin --prune --tags`, canonical remote inspection established:

| Check | Result |
|---|---|
| Latest remotely finalized demo predecessor | `origin/demo/demo-01a-unified-runtime-integration-closure` |
| Remote predecessor SHA | `9e59237296ed3baed551db2bbd565234a1b02db5` |
| DEMO-01B finalized remote commit | none |
| Required branch pre-existed | no |
| DEMO-DATA-00 branch base | exact predecessor |
| DEMO-DATA-00 starting worktree | clean, isolated worktree |

The requested branch was created only after those checks.

## 3. Frozen identity gate

| History | Required commit | Remote/tag evidence | Result |
|---|---|---|---|
| GEN-FINAL | `380cc6ea2a4498ce83690521c933accfd918818e` | `nma-generalization-v1.0-final^{}` | exact |
| BUILD-FINAL | `95de5fa3657a2c8ac7847f1ee1010c48ea984cd7` | `nma-build-v1.0-final^{}` | exact |
| CORE-FINAL | `5eb138ae7686502431587743ebce9ddf92c5a799` | `nma-core-v1.0-final^{}` | exact |
| ROAD-FINAL | `325c70d5335f57c43a8af85822db25032aa225c3` | `nma-road-v1.0-final^{}` | exact |
| School Hero | `56f99eb9ae63272a68accac3041fb10eacefb986` | `origin/freeze/hero-final-school-hero-56f99eb` | exact |

No frozen source, implementation, schema, authorization, semantics, portrayal, or identity file was
changed. Focused tests pin the byte hashes of the relevant frozen School, ROAD, and GEN artifacts.

## 4. Identity levels and fail-closed application

The three identity levels remain distinct:

1. **Production/frozen domain identity** — the immutable School, ROAD, BUILD, Core, and GEN
   histories listed above.
2. **Public-demo fixture identity** — would require a separately versioned fixture manifest and
   canonical hash with `historical-production-equivalence: false`. No candidate passed, so no such
   identity was assigned.
3. **Demo execution identity** — would have to bind a passing fixture and a domain-owned demo
   authorization without using a frozen execution identity. No candidate passed, so no demo
   execution identity was assigned.

The authority matrix encodes four false historical-substitution permissions. Schema and tests make
them closed constants. A demo fixture cannot replace a frozen hash, a demo authorization cannot
claim HERO-03 identity, and a demo execution cannot claim a frozen execution identity.

## 5. Authority terminology

The audit records these independently:

| Authority | Meaning used here |
|---|---|
| Access | A publisher-provided mechanism to obtain the data. |
| Use | Permission to use the published data for the contemplated purpose. |
| Redistribution | Permission to redistribute source data or an applicable derivative. |
| Execution | Domain authorization for NMA to perform a specific action on a specific fixture. |
| Provenance | Evidence that identifies the publisher, dataset, retrieval, transformation, and resulting identity. |

Web access is not treated as redistribution authority. Source licensing is not treated as NMA
execution authority. Transformation is not treated as removing licensing or attribution duties.

## 6. External publication authority

Authoritative source pages were checked on `2026-08-22`. Taiwan's Open Government Data License
version 1.0 grants reproduction, distribution, public transmission, compilation, adaptation, and
sublicensing for any purpose, while requiring explicit attribution. The candidate datasets below
identify that license on official `data.gov.tw` metadata pages.

Authority references:

- Open Government Data License 1.0: `https://data.gov.tw/license`
- NLSC school-area data: `https://data.gov.tw/dataset/174606`
- Chiayi City school-point-capable data: `https://data.gov.tw/dataset/52297`
- NLSC national/provincial road centerlines: `https://data.gov.tw/en/datasets/73232`

This establishes a defensible redistribution basis for those specific candidates with attribution.
It is not a general legal opinion and does not establish compatibility, exact payload identity, or
execution authority.

## 7. Machine-readable authority matrix

The canonical matrix is:

`data/demo/public-demo-data-authority-matrix-v1.0.json`

Schema:

`schemas/public-demo-data-authority-matrix-v1.0.schema.json`

Canonical matrix SHA-256, computed from canonical JSON after excluding `matrix_sha256`:

`2cccebe3753385ad1a441b51b776976ec0db9953861ec12a66ab9e27842a1227`

| Domain | Source | Access | Use | Redistribution | Provenance | Contract compatibility | Decision |
|---|---|---|---|---|---|---|---|
| School | NLSC `各級學校範圍圖_121分帶` | explicit | explicit | allowed with attribution | official metadata; payload not retrieved | incompatible | reject |
| School | Chiayi `嘉義市設有特殊教育班級之學校` | explicit | explicit | allowed with attribution | official metadata; payload not retrieved | incompatible | reject |
| ROAD | NLSC national/provincial centerlines | explicit | explicit | allowed with attribution | official metadata; payload not retrieved | incompatible with frozen ROAD-04 | reject |

No candidate is marked accepted. The schema requires any future accepted record to have one of the
three publishable redistribution classifications, a retrieved payload identity, compatibility with
zero frozen changes, and required attribution representation.

## 8. Q1 — School source

**Answer: no compatible public fixture is established.**

The requirement was recovered directly from `REAL_LAYER_PROFILES["school-point"]`, the School
execution-plan builder, the real-layer executor, and the materialized-output validator.

### True frozen execution requirements

| Requirement | Frozen value |
|---|---|
| Input container | ZIP containing complete Shapefile families |
| Required layer names | `J01_MARK`, `J13_MARK`, `J17_MARK`, `K01_MARK`, `K02_MARK`, `K14_MARK` |
| Required parts per layer | `.shp`, `.shx`, `.dbf`, `.prj` |
| Geometry family | `Point` |
| Identifier field | `MARKID` |
| Classification field/value | `TERRAINID = 9920103` |
| Label field | `MARKNAME1` |
| Combined result count | exactly 15 |
| Source CRS | each source `.prj` is authoritative; no global source EPSG is asserted |
| Output CRS | `EPSG:4326` |
| Coordinate dimensions | finite XY |
| Transformation | reviewed extraction, filter, reprojection, Z drop |
| Provenance assertions | `synthetic: false`, `random_coordinates: false` |
| Portrayal dependency | reviewed `assets/symbols/nlsc112v5.4/school.svg` baseline plus approved operations |

### Incidental or not independently required

- The frozen executor does not require a particular count per source layer; it requires 15 after
  combining and filtering all six.
- It does not enforce an inter-layer topology relationship.
- It does not require byte identity with the historical output GeoJSON as an input condition.
- It accepts the archive hash supplied by a valid authorization rather than a single hard-coded
  School archive hash.

Those flexibilities do not cure the source problem. Neither official candidate establishes six
source-backed MARK layers with those bindings. Artificially splitting one CSV into six files named
after historical map-sheet layers would manufacture a false provenance relationship. The task
explicitly forbids relabeling or weakening provenance to satisfy a contract.

The sources were therefore rejected before download. No nondeterministic or unnecessary source
payload was introduced.

## 9. Q2 — School authority

**Answer: a new public-demo execution authorization cannot be canonically issued in this checkout.**

The School execution path is:

`ExecutionAuthorizationStore.load → ExecutionAuthorizationVerifier.verify →`
`SchoolHeroExecutionEngine.execute → SchoolHeroVerifier.verify`

The verifier can validate a structurally valid hash-bound authorization. It does not issue one.
Repository governance evidence states that the upstream HERO-03 mechanism owns issuance and that
this checkout has no production issuer. The only constructor found locally is
`tests/hero04_support.py::make_authorization`, which is test support and cannot become authority.
The generic Agent handoff contract explicitly carries no domain execution authority.

Creating a static object that merely passes the consumer would emulate the absent issuer and would
misrepresent a test constructor as domain authority. No such object was created.

Required terminal School finding:

> **FAIL — SCHOOL PUBLIC DEMO REQUIRES POST-FREEZE AUTHORIZATION CHANGE**

This does not alter or revoke the historical HERO-03 authorization boundary.

## 10. Q3 — ROAD source

**Answer: an authorized public source exists, but no frozen-executable ROAD fixture can be created.**

The official NLSC national/provincial road centerline dataset is a credible future source:

- it is published by the appropriate government mapping authority;
- it advertises road-number/name attributes and downloadable road-centerline data;
- it is licensed under OGDL 1.0 with redistribution and derivative use allowed with attribution;
- clipping, attribute selection, reprojection, and GeoJSON conversion may be used while carrying
  forward attribution.

The payload was not downloaded because compatibility fails independently of coordinates. No
historical coordinates were reconstructed, approximated, inferred, digitized, or compared.

### Frozen ROAD-04 requirements

The actual frozen ROAD path is an immutable execution of one ROAD-03 capability, not a general
LineString executor. It requires:

| Requirement | Frozen value |
|---|---|
| Source archive SHA-256 | `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53` |
| ROAD-01 fixture SHA-256 | `b01e261971f65cbfc127aed4f1ba17b01b194dd89f256d3c024170c1dc7338f0` |
| Source layer | `K14_ROAD` |
| Geometry | finite `LineString` |
| Source CRS | `TWD97[2020]_TM121` |
| Runtime CRS | `EPSG:4326` |
| Ordered IDs | `K0000004671`, `K0000004913`, `K0000005348` |
| Required fields | `ROADSEGID`, `TERRAINID`, `ROADNUM`, `ROADNUM1`, `ROADNUM2`, `ROADNAME` |
| Class | `TERRAINID = 9420400` |
| Route identity | `ROADNUM=縣126\|ROADNUM1=\|ROADNUM2=\|ROADNAME=中山街` |
| Topology | ordered three-part endpoint continuity |
| Projection constraint | source/runtime vertex count preserved |
| Authorization SHA-256 | `f68220ecef989e589dd6e28c1ad2356a199790f061ea30cc725e42a5bdf92c38` |

The frozen plan records historical vertex counts `4`, `3`, `4`, but the executor principally
enforces preservation between source and runtime geometry; the complete frozen identity chain and
goldens preserve the historical counts.

`RoadAuthorizationStore` exposes only the frozen authorization ID.
`authorize_road_portrayal` issues only the historical bindings.
`FrozenRoadAuthorizationVerifier` rejects any changed archive, fixture, route, class, segment,
portrayal, or upstream identity. A focused test substitutes a new archive hash, recomputes the
authorization's content hash, and confirms the frozen verifier still rejects it.

A public road LineString can be license-valid and geometrically sensible while remaining
non-executable by ROAD-04. Calling it canonical or authorized would be false.

## 11. Q4 — architecture compatibility

**Answer: no.**

GEN-FINAL does not provide an alternate execution or authorization framework. Its generic adapter
boundary must not interpret domain payloads, issue domain authorization, execute mutations, or
replace domain validation. The Agent handoff layer likewise cannot substitute for School HERO-03
or ROAD-03 authorization.

Consequently:

- School requires a domain-owned public-demo issuer/profile decision after the freeze.
- ROAD requires a separately versioned ROAD public-demo contract, issuer, verifier, and executor
  path after the freeze.
- implementing either here would change frozen domain semantics or create a second authorization
  framework, both outside the allowed scope.

Required invariants remain:

- frozen contract changes: **0**;
- frozen domain semantic changes: **0**;
- historical identity substitution: **impossible/fail-closed**.

## 12. Canonicalization and fixture-manifest result

No fixture passed the authority-plus-compatibility gate, so creating a fixture ID, fixture hash, or
fixture manifest would falsely imply acceptance. The only new canonical identity is the authority
matrix itself. Its hash method is deterministic:

1. parse JSON;
2. remove `matrix_sha256`;
3. serialize UTF-8 JSON with keys sorted, no insignificant whitespace, preserved Unicode, and
   non-finite numbers forbidden;
4. compute SHA-256.

Future fixture work must separately define stable ordering, encoding, CRS, numeric serialization,
properties, transformation pipeline, source retrieval identity, attribution, and
`historical-production-equivalence: false` after the missing domain decisions are authorized.

## 13. Private archive boundary

Expected private archive SHA-256:

`4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`

It remained ignored, untracked, unstaged, unextracted, uninspected, and unused. Its existence or
content was not probed in the original checkout. Only Git ignore/tracking metadata was checked.
No candidate was compared with it.

## 14. Added evidence and tests

Changed files are limited to:

1. `NMA-DEMO-DATA-00-Public-Demo-Data-Closure-Report.md`;
2. `data/demo/public-demo-data-authority-matrix-v1.0.json`;
3. `schemas/public-demo-data-authority-matrix-v1.0.schema.json`;
4. `tests/test_public_demo_data_authority_demo_data00.py`.

The focused suite covers:

- JSON Schema validity and deterministic matrix hash;
- authority/license/attribution completeness;
- rejection of unresolved or incompatible publication candidates;
- direct recovery of School layer, field, geometry, CRS, and count requirements;
- ROAD rejection of a newly hashed source authorization;
- source metadata provenance completeness;
- absence of fixtures and authorizations after failed gates;
- machine-forbidden historical substitution;
- byte immutability of frozen contract/domain artifacts;
- private archive Git exclusion;
- public evidence reproducibility without private payloads.

## 15. Verification

Pre-commit focused result:

| Gate | Result |
|---|---:|
| DEMO-DATA-00 focused tests | 10 passed |
| JSON parse | passed |
| JSON Schema check and instance validation | passed |
| Deterministic matrix SHA-256 | passed |
| Frozen artifact byte hashes | passed |
| Private archive ignored/untracked/unstaged | passed |

Full lint, focused frozen-domain regressions, Git scope, fresh-clone reproduction, commit, and push
results are recorded in the terminal handoff after execution of those gates.

## 16. Closure decision

DEMO-DATA-00 establishes that publication licensing is not the only remaining blocker. Source data
can be lawfully obtained from official open-data sources, but current frozen execution and
authorization identities do not admit new School and ROAD public-demo fixtures.

The necessary next work is a separately authorized post-freeze domain stage—not a fixture copied
into this stage. Until then, the repository must continue to report public-demo School and ROAD
execution as unavailable.

**Terminal verdict:**

> **FAIL — PUBLIC DEMO DATA AUTHORITY OR FROZEN CONTRACT COMPATIBILITY NOT CLOSED**
