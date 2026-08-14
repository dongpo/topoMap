# HERO-02 School Feature Intelligence Agent

## Purpose

HERO-02 analyzes three local school-data sources and generates evidence-based candidate proposals for human validation. It can identify a school that may be missing from the NMA dataset or a matched NMA school whose geometry or attributes may have changed.

The Agent is advisory. It does not edit a dataset, call an execution tool, change an official feature, or approve its own proposal.

## Architecture

The implementation is under `src/nma/agents/school_agent/`:

- `discovery.py` loads and normalizes NMA GeoJSON, OSM school POI GeoJSON, and an official registry JSON document.
- `reasoning.py` evaluates geometry proximity, administrative-area equality, semantic name similarity, and attribute agreement.
- `evidence.py` requires complete evidence from at least two distinct sources and calculates a bounded confidence score.
- `proposal.py` emits JSON and JSON-LD-compatible update proposals with human-validation and non-execution flags.

```text
Local school datasets
        |
        v
Discovery and normalization
        |
        v
Spatial and semantic matching
        |
        v
Evidence completeness evaluation
        |
        v
Candidate update proposal
        |
        v
Human validation required
```

## Data connectors

The connector boundary accepts:

- NMA school data as GeoJSON Point features;
- OSM school POIs as GeoJSON Point features; and
- an official school registry JSON object containing a `schools` array.

Each record requires an identifier, name, administrative area, and coordinates. Registry IDs and addresses are optional for GeoJSON sources and supported by all matching stages.

Bundled synthetic samples are provided under `data/samples/school-agent/`. They demonstrate the connector contract and are not authoritative or redistributable-source substitutes.

The API uses those samples by default. A controlled local deployment can select reviewed snapshots with `NMA_SCHOOL_DATASET`, `OSM_SCHOOL_DATASET`, and `OFFICIAL_SCHOOL_REGISTRY`. Dataset paths remain server-side configuration and cannot be supplied by an API caller.

## Spatial reasoning

Candidate matching uses standard-library calculations only:

- haversine point distance with a 250-metre match boundary;
- exact normalized administrative-area equality;
- token-based Jaccard similarity for school names; and
- agreement over name, registry identifier, and address when available.

The overall matching score weights proximity at 40%, administrative relationship at 20%, semantic similarity at 20%, and attribute matching at 20%. A registry-ID match or semantic score of at least 0.5 is required in addition to proximity and administrative agreement.

An `ADD_FEATURE` proposal requires matching OSM and official-registry evidence with no NMA match. Attribute differences produce `UPDATE_ATTRIBUTES`. A geometry difference greater than 75 metres from the OSM/registry reference location produces `UPDATE_GEOMETRY`.

## Proposal contract

Every proposal contains:

- `feature_id`;
- `proposal` type;
- bounded `confidence` score;
- evidence records with source, type, feature identifier, detail, and score;
- a concise reasoning explanation;
- an ISO 8601 UTC timestamp;
- `human_validation_required: true`; and
- `automatic_execution: false`.

The analysis response uses schema `nma.school-feature-intelligence/0.5`, retains runtime contract `nma.runtime-baseline/0.32`, and includes an `@context` plus JSON-LD `@type` values. A complete example is stored at `data/samples/school-agent/example-output.json`.

## API

Endpoint:

```text
POST /api/school-agent/analyze
```

Request:

```json
{
  "administrative_area": "North District"
}
```

The request accepts only `administrative_area`. Extra fields, empty values, and values longer than 160 characters are rejected. The response contains candidate proposals only and exposes no execution parameter.

## Limitations

- HERO-02 reads local JSON/GeoJSON snapshots; it does not query live OSM or registry services.
- The bundled datasets are synthetic connector fixtures, not private or authoritative production data.
- Point proximity and token similarity are screening signals, not authoritative conflation decisions.
- Administrative matching currently uses exact normalized area names rather than boundary geometry.
- Confidence is a transparent deterministic ranking score, not a calibrated probability.
- Every candidate requires human review. The endpoint cannot modify NMA, OSM, registry, graph, vector, or MapLibre data.
