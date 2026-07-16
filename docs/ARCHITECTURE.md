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
| Human display | map and evidence panel | approximation/review status visible |

The current records are source-derived but carry `human-review-required`. They demonstrate the
mechanism; independent cartographer sign-off is the publication gate.

## Separation of authority and implementation

`portrayal-records.jsonl` contains only facts observed in the PDF text: feature name/code,
production stage, geometry categories, line/color codes, instruction, version, page, and URI.

`portrayal-profile.json` contains software choices: source-layer mapping, MapLibre layer type,
Canvas icon ID, paint values, and exceptions. It labels current glyphs as demonstration
approximations. This separation prevents the map implementation from masquerading as an extracted
official symbol.

## Agent boundary

The agent performs four observable operations:

1. identify a feature from a question or code;
2. retrieve its portrayal subgraph;
3. enforce profile, scale, and exception constraints;
4. return a structured decision with evidence or abstain.

An LLM can be added as a multilingual intent adapter, but the graph decision and evidence path do
not depend on it. Agno, OpenAI Agents SDK, LangGraph, MCP, or QGIS may call the same APIs without
owning the executable knowledge.

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
