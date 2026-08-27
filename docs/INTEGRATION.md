# Portrayal profile integration guide

NMA core is framework-independent. A country or mapping authority adds executable portrayal
knowledge through source records, a profile, benchmark tasks, and expert review—not a new generic
agent framework.

## Required inputs

1. Legally usable specification PDFs with stable title, version, page, and URI.
2. A bounded feature subset and scale/profile.
3. Local PDF files for hashing, text extraction, page rendering, and visual symbol comparison.
4. A vector-tile source with documented layer and feature-code fields.
5. Expert-approved answers and an unresolved-case policy.

## Integration sequence

1. Inventory and hash source PDFs without redistributing them by default.
2. Run `nma extract-portrayal` to create code-anchored **candidates**.
3. Render and visually inspect every cited page; transcribe evidence and symbol cells.
4. Review candidates into `portrayal-records.jsonl`; unresolved items stay non-executable.
5. Define implementation/source-layer mappings in a versioned portrayal profile.
6. Run `nma compile-knowledge` and inspect graph diffs.
7. Add human questions, symbol decisions, abstention cases, and map-compilation truth.
8. Run `nma compile-style`, inspect the map, and compare official/implemented glyphs.
9. Obtain independent expert sign-off and seal held-out cases.

## Framework adapters

Agno, OpenAI Agents SDK, LangGraph, MCP, QGIS, and other runtimes should call the stable NMA API:

- ask a human question;
- select a portrayal rule;
- retrieve the executable graph;
- retrieve compiled MapLibre layers.

They must not own the source evidence, rule/profile/version model, or review status.

## Safety behavior

The agent must abstain when a requested profile or scale is not loaded. A label/code conflict
between profiles is evidence of version ambiguity, not permission to choose the most convenient
symbol. Implemented glyphs remain unapproved until compared with the official rendered symbol cell
and independently reviewed; this reference profile has completed the comparison step.

The prior validation integration remains available for read-only GIS auditing. It retains the flow
proposal → preview → approval → execution → revalidation → audit.
