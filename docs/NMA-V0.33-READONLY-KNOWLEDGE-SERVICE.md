# NMA v0.33 read-only Knowledge Service

## Decision

This iteration gives the existing NMA Agent a bounded, read-only path to the live Neo4j
projection. It does not create another Agent and it does not give an LLM a Cypher interface.
Allowing an Agent to modify the formal canonical Knowledge Graph is explicitly future research.

The canonical JSON graph remains the reviewed semantic authority. Neo4j remains a rebuildable
runtime projection of exactly one canonical graph revision.

## Runtime path

```text
user request
  -> existing NMA Agent orchestration and entity resolution
  -> retrieve_evidence operation
  -> read-only Knowledge Service
  -> fixed, parameterized Neo4j read templates
  -> versioned evidence package and provenance
  -> existing plan / approval / GIS tool / verification loop
```

Candidate discovery may continue to use the local, version-controlled graph index. Once the Agent
has selected reviewed node IDs, evidence expansion passes through the Knowledge Service. This
preserves the established entity-resolution policies while making the evidence-bearing graph read
observable and replaceable without exposing Neo4j or Cypher to the Agent.

## Closed query contract

The public operation registry contains only `retrieve_evidence`. Requests provide a natural-language
query for traceability, already-resolved canonical seed IDs, a ranked-candidate trace, and bounded
depth/node settings. The service rejects unknown operations, extra fields, unknown node IDs,
over-limit requests, unregistered Cypher templates, and graph responses that exceed the incident
edge scan limit.

Neo4j is accessed with `session.execute_read` and `default_access_mode=READ`. Query text is selected
from two source-controlled templates; all variable values are driver parameters. User text, LLM
output, classification codes, filenames, and schema names are never interpolated into Cypher.

The exact machine-readable contract is
`data/specifications/nma-readonly-knowledge-service-v0.33.json`.

## Activation and failure behavior

Live activation requires all of the following:

1. complete Neo4j connection settings;
2. explicit `NMA_NEO4J_CREDENTIAL_SCOPE=read-only` operator attestation;
3. a driver session constrained to read access mode;
4. full node/relationship structural parity between the live projection and the canonical graph
   revision at process activation.

The deployment account must be provisioned by the Neo4j administrator with read-only database
privileges. The configuration attestation and driver read mode are application controls, not a
substitute for server-side least privilege.

The ignored local configuration uses this shape (values are deployment-specific and must not be
committed):

```dotenv
NMA_GRAPH_BACKEND=neo4j
NMA_GRAPH_FALLBACK=none
NMA_NEO4J_CREDENTIAL_SCOPE=read-only
NEO4J_URI=neo4j+s://managed-host.example
NEO4J_USER=nma_reader
NEO4J_PASSWORD=<secret>
NEO4J_DATABASE=mapfeatures
```

If live Neo4j is unavailable or mismatched, the service either fails closed or uses the explicitly
configured canonical JSON snapshot. Snapshot fallback is valid only because it is loaded from the
same canonical revision and SHA-256. The fallback and its reason are included in every public
backend trace; the Agent may not silently use a different graph, an LLM guess, or external data.

## Evidence and provenance

Every evidence package reports:

- Knowledge Service and operation contract versions;
- active backend and fallback state;
- canonical graph revision and SHA-256;
- graph identity verification state;
- selected graph node IDs and stable relationship hashes;
- read transaction and bounded edge-scan counts;
- citations resolved through canonical section-to-document containment and the reviewed source
  registry;
- `mutation_allowed=false`, `arbitrary_cypher_allowed=false`, and
  `automatic_rule_activation=false`.

Credentials never enter the trace or response.

## Agenticity boundary

Read-only KG access supports evidence retrieval inside the Agent loop; it does not by itself prove
Agenticity. RQ10 still requires observable outcome-driven decisions such as replan, tool reselection,
abstention, human intervention, and stop. The Knowledge Service supplies governed observations that
can drive those decisions.

This iteration does not support proposals that write directly to Neo4j, promotion of session
mappings into the canonical KG, automatic rule review, or autonomous graph mutation. A future study
may evaluate Agent-proposed changes only through separate proposal, validation, human review,
versioning, rollback, and activation controls. Direct autonomous modification of the formal KG is
not an accepted production capability.

## Verification

Focused tests cover the sealed v0.28 Point, Line, Polygon, conflict, and quality-rule evidence cases;
live-adapter versus same-revision snapshot parity; `execute_read` enforcement; operation and
parameter rejection; credential redaction; visible same-identity fallback; projection mismatch;
and absence of mutation capabilities. Live deployment still requires an operator-provisioned
read-only Neo4j account and runtime infrastructure; no credentials are stored in the repository.
