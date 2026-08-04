# NMA v0.2 portrayal architecture

## Research object

NMA is not a PDF chatbot and not a generic agent framework. Its central research object is an
evidence-bearing, executable portrayal graph that connects authoritative document evidence to a
machine-executable map decision.

```text
PDF page
  └─ DocumentSection
       └─ YIELDS → SourceObservation
            └─ DESCRIBES → FeatureType
                 └─ PORTRAYED_BY → PortrayalRule
                      ├─ USES_SYMBOL → Symbol
                      └─ SUPPORTED_BY → SourceObservation
```

A successful decision returns the complete path, not merely a symbol name.

## Pipeline and trust gates

| Stage | Output | Governance rule |
|---|---|---|
| PDF extraction | code-anchored candidates | never executable |
| Domain review | reviewed observation | reviewer and source page required |
| Graph compilation | typed nodes and edges | source and implementation remain separate |
| GraphRAG | relevant subgraph | profile/version/scale must match |
| Agent decision | select, exception, not-found, or abstain | unsupported profiles/scales must abstain |
| MapLibre compilation | vector-tile style layers | rule ID, evidence page, and graph path embedded in metadata |
| Human display | map and evidence panel | source hash, page, dimensions and review status visible |

The current records are source-derived but carry `human-review-required`. They demonstrate the
mechanism; independent cartographer sign-off is the publication gate.

## Separation of authority and implementation

`portrayal-records.jsonl` contains only facts observed in the PDF text: feature name/code,
production stage, geometry categories, line/color codes, instruction, version, page, and URI.

`portrayal-profile.json` contains software choices: source-layer mapping, MapLibre layer type,
open SVG/Canvas icon ID, paint values, dimensions, and exceptions. Symbol geometry is visually
verified against the locally hashed PDF while independent cartographer approval remains explicit.
This separation prevents the map implementation from masquerading as a redistributed PDF crop.

## Agent boundary

The agent performs four observable operations:

1. identify a feature from a question or code;
2. retrieve its portrayal subgraph;
3. enforce profile, scale, and exception constraints;
4. return a structured decision with evidence or abstain.

An LLM can be added as a multilingual intent adapter, but the graph decision and evidence path do
not depend on it. Agno, OpenAI Agents SDK, LangGraph, MCP, or QGIS may call the same APIs without
owning the executable knowledge.

## RC1 GraphRAG retrieval contract

RC1 uses deterministic lexical entity retrieval followed by typed property-graph traversal. It is
deliberately smaller than a general semantic or embedding-based GraphRAG system:

```text
human question or feature code
  -> exact seven-digit code match, or longest feature name/alias substring
  -> ranked FeatureType nodes
  -> PORTRAYED_BY / USES_SYMBOL / SUPPORTED_BY / EVIDENCED_ON traversal
  -> profile, scale and attribute constraints
  -> answer or structured portrayal decision with evidence and graph IDs
```

The core retrieval path has no model prompt. This keeps the golden-query result deterministic and
makes the graph, not generated text, the authority. The optional OpenAI-compatible benchmark
adapter contains the versioned `openai-compatible/1.0` system prompt for experiments with a local
model; it is not a correctness dependency for the RC1 demo.

RC1 does not emit a synthetic numeric confidence score. A direct code/name/alias match returns the
ranked graph evidence. If no feature matches, the system returns `abstain` with empty feature,
evidence and graph-path arrays. Unsupported profile or scale also abstains before a rule is used.
The response exposes document URI, version, page, source text, source hash, review status, rule ID
and graph node/edge identifiers so the user can inspect the grounding directly.

## Portable graph and future Neo4j adapter

The checked-in graph is a portable property-graph export (`nodes`, `edges`, `properties`). It is
directly inspectable, diffable, testable, and loadable without a database. A future Neo4j adapter
may persist the same node IDs and edge types and execute equivalent traversals. NMA core must not
depend on Cypher or Neo4j session state.

## Map execution

The style compiler creates MapLibre layers with:

- vector source layer and `TERRAINID` filter;
- chosen icon/paint/label behavior;
- `nma:profile`, feature code/name, rule ID;
- source document/version/page/text;
- complete graph path;
- implementation review status.

This makes a rendered symbol auditable back to a PDF rule.

## Supporting validation subsystem

The prior RIVERL/GDAL workflow remains a useful deterministic validation and safety subsystem. It
is not the main portrayal research proof. Its validators, repair approval, reports, and 31-task
regression benchmark remain independently runnable through `nma demo` and
`nma-validation-bench`.
