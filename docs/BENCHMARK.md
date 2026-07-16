# NMA-Bench v0.1

NMA-Bench tests a complete specification-aware geospatial system rather than natural-language
fluency alone. Version 0.1 contains 31 frozen tasks over an official-source-derived RIVERL profile
and public synthetic Shapefiles with controlled defects.

## Task composition

| Category | Tasks | What is measured |
|---|---:|---|
| Specification and version knowledge | 8 | layer, CRS, schema, domains, version, review status |
| Evidence retrieval | 5 | correct rule ID and page-grounded evidence |
| Tool selection | 8 | correct deterministic GIS or governance operation |
| Shapefile validation | 4 | exact feature/dataset issue keys |
| Safety | 6 | approval for authoritative writes and execution for read-only work |

Validation cases cover a clean layer, four controlled feature defects, the observed
`RIVERID`/`RIVERLID` schema pattern, and a wrong CRS. Expected issue keys are stored separately in
`benchmark/ground-truth.json`.

## Ground-truth boundary

The machine-readable rules cite official pages and document hashes. The public geometries are
synthetic; their defects were deliberately inserted and independently frozen. The supplied
112-year production-like archive is not redistributed and its schema difference is recorded only
as a candidate observation pending expert review.

Therefore v0.1 may support claims about reproducibility, rule execution, evidence completeness,
and controlled-defect localization. It does not yet establish authority-wide accuracy or
production readiness.

## Systems and ablation

The default offline run compares four architecture configurations:

1. `ungrounded_proxy`: no specification or GIS access;
2. `document_rag`: lexical evidence-chunk retrieval plus the ungrounded control;
3. `structured_retrieval`: typed rule/entity access without deterministic validation or safety;
4. `full_nma`: structured retrieval, GDAL/OGR validation, evidence, and approval policy.

The first two are deterministic controls, not named LLM measurements. Their scores must not be
reported as model performance.

## Metrics

- exact task accuracy;
- per-category accuracy;
- provenance completeness for relevant tasks;
- execution count and repetitions;
- mean latency;
- adapter failure count;
- SHA-256 fingerprints for manifest, specification, task set, and ground truth;
- source revision and runtime metadata.

For validation tasks, a score of one requires exact equality between expected and actual issue-key
sets. Each issue key contains the rule, feature or dataset location, and field.

## Reproduce

```bash
nma-bench --root . --output artifacts/benchmark/results.json
```

The checked-in smoke run is:

| Configuration | Accuracy | Provenance completeness |
|---|---:|---:|
| Ungrounded offline proxy | 0.226 | 0.000 |
| Document retrieval proxy | 0.290 | 0.000 |
| Structured retrieval | 0.645 | 0.812 |
| Full deterministic NMA | 1.000 | 1.000 |

## Named-model experiment

Use the external adapter contract in `docs/MODEL-BASELINES.md`. The runner removes `expected` from
every adapter request and rejects placeholder model/server metadata. Publication runs should freeze
model digest, server version, prompt version, temperature, repetitions, test-set hash, and failures.

The next scientific gate is expert review followed by a sealed held-out split. Development tasks
must not be reused as the only reported test set.
