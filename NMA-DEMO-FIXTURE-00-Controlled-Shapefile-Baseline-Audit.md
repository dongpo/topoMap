# DEMO-FIXTURE-00 — Controlled Shapefile Baseline Audit

## Terminal verdict

**PASS — CONTROLLED SHAPEFILE DEMO BASELINE ESTABLISHED**

The owner-supplied controlled archive is the correct NMA v1.0 School/ROAD demo input. Direct,
read-only inspection proves that it satisfies the frozen School data contract and the complete
frozen ROAD data, geometry, identity, and authorization contract. No external data substitution is
needed or appropriate.

School has one bounded remaining **DEMO BINDING GAP**: a normal demo user cannot obtain and store a
new domain-owned HERO-03 authorization. That is an authorization-binding issue, not a data,
GraphRAG, geometry, portrayal, or frozen-runtime incompatibility. ROAD executes its exact frozen
ROAD-01/02/03/04/05 chain when the controlled archive is locally present.

This PASS establishes the controlled baseline. It does not claim DEMO-02 acceptance and does not
authorize any change to a frozen executor.

## 1. Scope correction

NMA v1.0 demonstrates:

> Agent + GraphRAG + frozen cartographic knowledge + controlled geospatial fixtures → rule-aligned
> map production.

NMA v1.0 does **not** claim general-purpose arbitrary geospatial data ingestion. Schema mapping,
semantic alignment, CRS handling, geometry QA/repair, data-quality assessment, provenance
onboarding, trust/authorization, and generic data adaptation remain separate post-v1.0 concerns.

No arbitrary NLSC/government/OSM/third-party School or ROAD dataset was searched for, downloaded,
or substituted during this audit. The DEMO-DATA-00 open-data strategy remains preserved as
historical evidence and is superseded for demo-fixture acceptance.

## 2. Repository and predecessor evidence

| Check | Result |
|---|---|
| Canonical origin | `https://github.com/dongpo/topoMap.git` |
| Fetch | canonical remote branches and tags fetched with prune |
| Latest finalized demo predecessor | `demo/demo-data-00-public-demo-data-closure` |
| Exact predecessor SHA | `8fb113b8beb00952901abeafa22ebee0c8b76bc6` |
| Predecessor local/upstream/remote equality | exact |
| Requested branch | `demo/demo-fixture-00-controlled-shapefile-baseline` |
| Starting task worktree | clean at the predecessor SHA |
| Original checkout | contained an unrelated untracked DEMO-01B report; preserved untouched |

## 3. Controlled fixture authority and inspection boundary

The inspected package was the locally supplied `data/datasets/112年多維度SHP成果_0502.zip`:

| Property | Observation |
|---|---|
| Size | 12,822,898 bytes |
| SHA-256 | `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53` |
| Engine | GDAL 3.11.0 / read-only OGR |
| Normalization by audit | none |
| Reprojection/repair/simplification/snapping/dissolve/interpolation | none |
| Redistribution | none |

The package hash is the exact archive hash already referenced by the School runtime profile and
the frozen ROAD chain. This byte equality is evidence of compatibility; it does not convert the
archive into production canonical data.

Repository policy in `docs/NMA-V0.2.1-DATA-BOUNDARY.md` marks the reviewed archive, private source
coordinates, and derived copies as non-redistributable. Therefore the audit read and compared the
exact ROAD coordinate arrays but does not add those private numeric arrays to Git. The
machine-readable record contains non-invertible canonical coordinate-array hashes, full geometry
hashes, and exact vertex counts. Frozen execution also materialized the arrays successfully in a
temporary local execution artifact. This preserves both the requested coordinate verification and
the existing no-redistribution rule.

## 4. Controlled Demo Fixture Identity

Historical identity and demo identity are separate concepts:

```text
Historical frozen fixture identity ≠ Controlled demo fixture identity
Historical production authorization ≠ Demo execution authorization
```

The controlled identities use a demo-only namespace and bind the exact relevant Shapefile
components:

| Domain | Controlled Demo Fixture Identity |
|---|---|
| School | `nma-demo-fixture:school:sha256:77802b44b97c6687bc626d257e14b57c3d7427949a65942fa721d05bb79fc12d` |
| ROAD | `nma-demo-fixture:road:sha256:dc82db8bfc96dd6ab16b3206866e000459b9fd59a8f6d44602fcf06586b1ae79` |

Aggregate procedure:

1. Include `.cpg`, `.dbf`, `.prj`, `.shp`, and `.shx` for each logical fixture layer.
2. Sort by `layer_id`, then lowercase extension.
3. Begin with UTF-8 bytes `nma-controlled-demo-fixture-v1\n`.
4. Append one UTF-8 line per component:
   `{layer_id}\t{extension}\t{lowercase_file_sha256}\n`.
5. SHA-256 the complete byte stream.

All 35 per-file hashes, sizes, ordering inputs, and both aggregate identities are recorded in
`data/specifications/nma-demo-controlled-fixture-baseline-v1.0.json`.

## 5. School fixture inventory

### 5.1 Exact Shapefiles inspected

The School fixture is the elementary-school selection across these six primary archive families,
each with complete `.shp/.shx/.dbf/.prj/.cpg` components:

| Layer | Raw MARK features | `TERRAINID=9920103` | Geometry | Selected IDs |
|---|---:|---:|---|---|
| `J01_MARK` | 176 | 0 | Point | — |
| `J13_MARK` | 107 | 1 | Point | `J0000002393` |
| `J17_MARK` | 349 | 0 | Point | — |
| `K01_MARK` | 668 | 12 | Point | `K0000001676`–`K0000001687` |
| `K02_MARK` | 120 | 1 | Point | `K0000001334` |
| `K14_MARK` | 44 | 1 | Point | `K0000001371` |
| **Total** | **1,464** | **15** | **Point** | **15 unique IDs** |

The six layers are source partitions. Two valid partitions happen to contribute zero elementary
school records. The contract is not “six non-empty elementary-school layers”; it is “inspect the
six reviewed MARK layers and select exactly 15 elementary-school features.”

### 5.2 CRS, fields, geometry, and quality

All six layers have the same observed contract:

| Item | Direct observation | Role |
|---|---|---|
| CRS name | `TWD97[2020]_TM121`, metres | source positioning |
| Projected EPSG authority | not embedded in the supplied custom WKT | runtime uses the `.prj` directly |
| `MARKID` | String(11) | stable feature identifier |
| `TERRAINID` | String(8) | classification and GraphRAG/rule linkage |
| `MARKNAME1` | String(254) | required school name label |
| `MDATE` | String(8) | optional source currency metadata |
| Invalid/empty/multipart selected geometry | 0 / 0 / 0 | valid Point input |
| Selected missing labels | 0 | labeling supported |
| Selected duplicate IDs | 0 | identity supported |
| Z/M | absent | frozen School output explicitly forces XY |

Coordinates are plausible for the six supplied Taiwan TM121 profiles: easting
230,762.8873–256,038.6363 and northing 2,711,769.2762–2,741,424.0694. The audit did not assign an
EPSG code, repair the WKT, or transform the source.

### 5.3 Is “6 layers / 15 features” real?

**Yes.** It is simultaneously:

- a directly observed characteristic of this exact controlled archive;
- a frozen, dataset-specific runtime contract in `REAL_LAYER_PROFILES["school-point"]`;
- an enforced execution condition in `execute_real_layer` and `_validate_school_geojson`; and
- a historical fixture assumption intentionally scoped to this curated demo input.

It is not a universal School schema and must not become a generic ingestion rule.

### 5.4 School compatibility matrix

| Requirement | Classification | Evidence |
|---|---|---|
| Six named source layers | **MATCH** | exact `J01/J13/J17/K01/K02/K14_MARK` set |
| 15 selected elementary schools | **MATCH** | direct filter counts `0+1+0+12+1+1` |
| Point geometry | **MATCH** | all source definitions and selected features are Point |
| Source CRS | **MATCH** | all `.prj` files name `TWD97[2020]_TM121` |
| Identity | **MATCH** | `MARKID`, 15 unique selected values |
| Classification | **COMPATIBLE_WITH_ADAPTER** | observed `TERRAINID`; frozen profile explicitly binds it instead of Document 09 `MARKTYPE1` |
| Labels | **MATCH** | `MARKNAME1`; zero missing selected labels |
| GraphRAG linkage | **MATCH** | `TERRAINID=9920103` links classification/rule; MARK layer and label available |
| Historical archive provenance | **MATCH** | exact archived byte SHA already bound by runtime |
| New HERO-03 identity | **AUTHORIZATION_BINDING_ONLY** | no production issuer or stored demo authorization |
| Frozen executor | **MATCH** | existing School real-data/execution/rollback tests execute the archive |

### 5.5 School authorization conclusion

The frozen School executor is structurally capable of executing this fixture. A complete
authorization must bind:

- feature identity `9920103` / Point;
- proposal and validation identities;
- explicit human approval and operations;
- the official School portrayal baseline;
- this archive SHA-256; and
- the bounded derived-layer/portrayal/MapLibre scope.

The repository contains a verifier, store, executor, and test-support authorization constructor,
but no domain-owned production HERO-03 issuer or normal demo binding that creates and stores a new
authorization. Direct controlled-fixture execution passed when the complete contract-shaped
authorization was supplied by the existing test boundary.

**School classification: FIXTURE COMPATIBLE — AUTHORIZATION BINDING BLOCKER.**

This is a **DEMO BINDING GAP**, not a frozen architecture or data failure. DEMO-FIXTURE-00 does not
bypass or change it.

## 6. ROAD fixture inventory

### 6.1 Exact Shapefile inspected

The frozen ROAD domain targets the complete primary family:

`K14_頭屋都市計畫/SHP/K14_ROAD.{shp,shx,dbf,prj,cpg}`

| Item | Direct observation |
|---|---|
| Layer | `K14_ROAD` |
| Declared geometry | LineString |
| Total features | 196 |
| CRS | `TWD97[2020]_TM121`, metres; custom WKT without a projected EPSG authority ID |
| Extent | easting 234,582.0027–235,841.6277; northing 2,718,365.2691–2,719,467.3085 |
| Required identity fields | `ROADSEGID`, `TERRAINID` |
| Route fields | `ROADNUM`, `ROADNUM1`, `ROADNUM2`, `ROADNAME` |
| Other portrayal/semantic fields | `WIDTH`, `ROADCLASS1`, `ROADSTRUCT`, aliases/name sections |
| Invalid / empty | 0 / 0 |
| Multipart in full layer | 21; none of the three authorized segments |
| Total source vertices | 1,252 |
| Z/M | absent |

The full layer also contains non-target features and multipart lines. That is not a frozen-contract
mismatch: frozen execution selects and verifies only the exact authorized three-segment route.

### 6.2 Are the ROAD coordinate arrays present?

**Yes.** They are native coordinate arrays in the supplied `K14_ROAD.shp`, not reconstructed from
Git metadata.

| Ordered segment | Geometry | Native vertices | Coordinate-array SHA-256 | Frozen geometry SHA-256 |
|---|---|---:|---|---|
| `K0000004671` | LineString | 4 | `0c6bbf075b4468bcfde9a26ab1a2362dee58af7c140421be2215d142e1fdbeb0` | `42616b9b91d91efd4582171b23ad70259156c586bef776098329cdd81aa8f800` |
| `K0000004913` | LineString | 3 | `c11b2e99fae69e7b4ddf4c902707080cb6365b48dd37a13de5fdac3d440c113c` | `c075943948c1184493d41672f0ca00e610c90bfa7c721f24a645765dc48b9faf` |
| `K0000005348` | LineString | 4 | `f151e78f72c187cada8fbe8364f0276b5ef1255e76839bb4746b3bc2dec7d596` | `88ad286f2b368130e0870360acd07d1d79614d8005ee53eed966b8db6abd2cc6` |

Every target is finite, non-empty, valid, simple, XY, class `9420400`, and has exact identity
`ROADNUM=縣126|ROADNUM1=|ROADNUM2=|ROADNAME=中山街`. Their endpoint topology reproduces the frozen
contiguous order. The full source geometry hashes exactly equal the ROAD-04/05 frozen values.

### 6.3 ROAD compatibility matrix

| Requirement | Classification | Evidence |
|---|---|---|
| `K14_ROAD` family and 196 features | **MATCH** | direct Shapefile inspection |
| Required sidecars | **MATCH** | `.shp/.shx/.dbf/.prj/.cpg`, individually hashed |
| Route/segment IDs and order | **MATCH** | three exact `ROADSEGID` values |
| Class/route/name fields | **MATCH** | `9420400`, `縣126`, `中山街` |
| Native coordinate arrays | **MATCH** | exact arrays read; 4/3/4 vertices |
| Frozen geometry commitments | **MATCH** | all three exact frozen SHA-256 values |
| Geometry continuity | **MATCH** | one connected, non-branching, non-overlapping chain |
| Runtime EPSG:4326 output | **COMPATIBLE_WITH_SERIALIZATION** | explicit GDAL derivative preserves 4/3/4 vertex counts |
| Historical archive identity | **IDENTITY_BINDING_ONLY** | exact package already matches frozen archive hash |
| ROAD-03 authorization | **MATCH** | tracked frozen authorization verifies and executes |
| Executor binding | **MATCH** | ROAD-04 execution and ROAD-05 verification pass |

**ROAD blocker: none when the exact controlled package is locally available at the reviewed input
boundary.** The prior “coordinates unavailable” statement described the public Git artifact, not
the supplied controlled fixture.

## 7. GraphRAG and mapping-rule suitability

### 7.1 School rule chain

Frozen/reviewed knowledge sources:

- `data/knowledge/nma-canonical-graph-v0.4.json`
  - `code-value:landmark-type:9920103` — 小學;
  - `product-layer:MARK` — Point Shapefile landmark layer;
  - `portrayal-rule:doc01:9920103` — name annotation, line/color references, Point role;
  - `portrayal-recipe:doc01:9920103:review-v1` — fixed 2.2 × 3.0 mm flag marker and school name.
- `data/knowledge/nma-semantic-links-approved-v0.8.json`
  - reviewed terms `國小` + `校名` link to the School portrayal rule;
  - automatic rule activation remains false.
- `data/portrayal/nlsc112v5.4/portrayal-recipe-review-batch-01-v0.4.json`
  - exact reviewed primitives, dimensions, label requirement, and unresolved activation gates.
- `src/nma/real_layer.py`
  - requires the classification, portrayal rule, and MARK layer evidence nodes before proposing a
    controlled real layer.

Fixture attributes `TERRAINID`, `MARKNAME1`, and `MARKID`, plus Point geometry, expose exactly the
classification, label, identity, and layer semantics needed for this reasoning. The fixture does
not resolve pending human choices such as collision placement or activate a review candidate by
itself.

### 7.2 ROAD rule chain

Frozen/reviewed knowledge sources:

- `data/knowledge/nma-canonical-graph-v0.4.json`
  - `code-value:road-class2:9420400` — county highway;
  - `portrayal-rule:doc01:9420400` — surveyed-width boundary and name annotation;
  - `portrayal-rule:doc01:9490005` — county route shield parallel to the road;
  - `portrayal-recipe:road:9420400:compound-v1`;
  - road-name and route-shield vector primitives.
- `data/extraction/v0.4/road-compound-portrayal-reviewed.json`
  - Document 01 road boundary/name and route-shield evidence;
  - Document 02 Annex 7 classification evidence;
  - BMAP096 graphic-element roles;
  - the reviewed compound recipe and its unresolved ROAD↔ROADA spatial-association boundary.
- `data/specifications/nma-road-hero-road-01-v1.0.json`
  - exact K14 route, class, segment order, topology, and evidence bindings.
- `src/nma/road_execution.py` / `src/nma/road_verification.py`
  - exact native geometry, explicit runtime serialization, line-following `中山街`, semantic shield
    binding `9490005`, receipt, observation, QA, provenance, and rollback.

The fixture supplies `TERRAINID`, `ROADSEGID`, `ROADNUM*`, `ROADNAME`, `WIDTH`, and LineString
geometry. This is sufficient for the frozen controlled ROAD demonstration. The frozen demo
truthfully uses the centreline for the authorized semantic geometry and line-following label, and
keeps shield `9490005` as `semantic_binding_only`; it does not fabricate a shield asset or claim the
unresolved ROADA surveyed-boundary association.

## 8. End-to-end feasibility

| Stage | School | ROAD |
|---|---|---|
| Controlled fixture discovery | **READY** | **READY** |
| Fixture validation | **READY** | **READY** |
| Agent request interpretation | **READY** | **READY** |
| GraphRAG rule retrieval | **READY** | **READY** |
| Planning | **READY** | **READY** |
| Authorization | **BLOCKED_BY_AUTHORIZATION** for a new normal demo transaction | **READY** with frozen ROAD-03 authorization |
| Execution | **READY_WITH_DEMO_BINDING** | **READY** |
| Portrayal | **READY_WITH_DEMO_BINDING** | **READY** within frozen semantic-shield boundary |
| Verification/provenance | **READY_WITH_DEMO_BINDING** | **READY** |
| Map result | **READY_WITH_DEMO_BINDING** | **READY** |

## 9. Minimum safe future binding

The only bounded closure required for a new School end-to-end demo transaction is:

```text
Controlled Demo Fixture
        ↓
Controlled Demo Fixture Identity
        ↓
Demo-specific, human-approved HERO-03 authorization
        ↓
Existing frozen School domain contract
        ↓
Canonical execution and verification
```

That bridge may translate the demo fixture identity into an authorization-bound reference to the
same verified archive bytes. It must not change domain semantics, mapping rules, geometry
semantics, portrayal rules, Core identity, verification rules, or either frozen executor.
DEMO-FIXTURE-00 specifies but does not implement this bridge.

## 10. Controlled reproducibility baseline

Another authorized developer can reproduce the controlled demo using:

1. this public repository branch;
2. the exact owner-supplied package with SHA-256
   `4888dbf9a838ed5c41e20c3b528c542c7e52845b4d8e4809f58ea5afcec2da53`;
3. local placement at `data/datasets/112年多維度SHP成果_0502.zip` (or the documented School
   private-archive environment binding);
4. GDAL/OGR;
5. the existing frozen ROAD authorization; and
6. a future bounded demo-specific HERO-03 authorization for a new School execution.

Public GitHub redistribution of the package is neither required nor authorized. The fixture is an
appropriate experimental control because its bytes, schema, geometry, CRS, expected selections,
attributes, mapping behavior, and failure boundaries are known and reproducibly hashed.

## 11. Focused and regression verification

Focused direct-fixture verification:

- `tests/test_demo_fixture00_controlled_baseline.py`: fixture discovery/integrity, deterministic
  aggregate hashes, required sidecars, School inventory and 6/15 contract, ROAD coordinates and
  geometry commitments, identity separation, GraphRAG attribute/rule suitability, and no external
  substitution.
- Existing private School real-data, acceptance, execution, and rollback suites plus frozen ROAD-04
  execution: **63 passed** against the exact controlled archive.

| Verification set | Result |
|---|---:|
| DEMO-FIXTURE-00 focused, including live archive | **7 passed** |
| DEMO-01 + DEMO-02 focused | **34 passed, 1 loopback skip** |
| Exact detached `nma-generalization-v1.0-final` | **10 passed** |
| Frozen School/Core/real-layer/HERO selection | **54 passed** |
| Frozen ROAD-01 through ROAD-05 | **199 passed** |
| Applicable BUILD-10/11/11A/12 | **87 passed, 2 stage-local scope failures** |
| Complete descendant repository | **1,382 passed, 1 skipped, 20 inherited/stage-local failures** |

The BUILD failures assert their historical stage's exact changed-file set or direct-parent position;
they are expected to reject a later descendant audit branch. The complete-run failures comprise
those historical exact-scope/lineage checks and three already documented Agentic v0.3 stale
manifest/catalog checks. With the ignored local ROAD runtime artifact materialized, ROAD-05 has no
failure. No failure concerns fixture bytes, schema, CRS, geometry, coordinate availability,
GraphRAG linkage, frozen School/ROAD behavior, or this audit's deterministic identities.

Ruff lint and format, JSON parsing, and `git diff --check` pass. Production changes and frozen
implementation changes remain zero by construction; the branch adds only this audit, one
machine-readable record, and one focused audit test file.

## 12. Required questions answered

### School

1. **What exact Shapefiles were inspected?** The six primary `J01_MARK`, `J13_MARK`, `J17_MARK`,
   `K01_MARK`, `K02_MARK`, and `K14_MARK` families from the exact supplied archive.
2. **Do they meet the real School execution requirements?** Yes: complete sidecars, Point geometry,
   reviewed CRS, required fields, 15 unique classified/labeled features, and exact archive binding.
3. **Is 6-layer / 15-feature satisfied?** Yes, exactly: `0+1+0+12+1+1=15` selected records.
4. **If not, why?** Not applicable; it is satisfied. It is a frozen dataset-specific demo contract,
   not a general School-ingestion requirement.
5. **What is the blocker?** Authorization binding only: no normal domain-owned HERO-03 demo issuer
   or stored new authorization. Data, GraphRAG suitability, planning, execution, and verification
   structures are compatible.

### ROAD

1. **What exact Shapefile was inspected?** Complete `K14_ROAD.{shp,shx,dbf,prj,cpg}` from the exact
   supplied archive.
2. **Are the ROAD coordinates actually present?** Yes. Exact native arrays were read for all three
   authorized segments and match frozen geometry commitments and 4/3/4 vertex counts.
3. **Does geometry satisfy frozen ROAD requirements?** Yes: finite, valid, simple, contiguous
   LineStrings in the correct source CRS and order, with exact source geometry hashes.
4. **What is the blocker?** None when the exact controlled package is locally available. Public Git
   non-redistribution is a packaging boundary, not a fixture, identity, authorization, or runtime
   incompatibility.

### Demo

1. **Are the supplied Shapefiles suitable as the controlled NMA demo baseline?** Yes.
2. **Can they support Agent + GraphRAG mapping-rule demonstration?** Yes, within the exact frozen
   School and ROAD rule/portrayal boundaries described above.
3. **What is the minimum remaining blocker before DEMO-02 can PASS?** A bounded, demo-specific,
   human-approved HERO-03 authorization issuance/storage binding for a new School execution, plus
   normal DEMO-02 acceptance rerun. No fixture or frozen executor redesign is needed.
4. **Is external open-data substitution required?** **No — external open-data substitution is
   neither required nor part of the NMA v1.0 demo objective.**
