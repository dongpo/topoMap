# Contributing to AMA

Authoritative Mapping Agent (AMA) is an open geospatial research-software project. Contributions are welcome when they either improve a reusable open component or strengthen the evidence needed to evaluate the GIScience research questions.

## Contribution areas

Contributions are especially welcome in these areas:

1. **Mapping knowledge profiles** — jurisdiction-, authority-, or specification-specific source metadata, vocabularies, classifications, portrayal rules, constraints, provenance, and tests.
2. **Executable rules** — reviewed machine-readable mapping rules with stable identifiers and explicit evidence.
3. **Validators and execution adapters** — deterministic checks or GIS/tool integrations that preserve the authorization and provenance boundary.
4. **Benchmarks and baseline adapters** — new held-out tasks, failure cases, expert labels, or adapters for LLM-only, RAG, GraphRAG, and comparable geospatial-agent systems.
5. **Interoperability** — mappings to open geospatial standards, schemas, APIs, or reusable FOSS4G components.

## Research/software boundary

A software test demonstrates that an implementation satisfies a contract. It does **not** by itself establish a scientific hypothesis. Contributions that make research claims should identify the research question, comparison condition, evaluation dataset, metric, and evidence needed to support that claim.

See the [research and open-source contribution model](docs/research/RESEARCH-AND-OPEN-SOURCE-CONTRIBUTIONS.md).

## Rule contribution requirements

Every executable-rule contribution must declare:

- stable rule identifier;
- source authority / publisher;
- source title and version/date;
- target feature, schema, portrayal, or operation;
- explicit condition/constraint;
- expected action or abstention;
- authority/severity level where applicable;
- provenance/evidence reference;
- source licence and redistribution boundary;
- review status.

Automatically extracted candidates are never accepted as authoritative executable knowledge until reviewed under the profile's declared governance process.

## Mapping profile requirements

A new profile should be separable from the AMA core and should include, as applicable:

```text
profile metadata
source registry
vocabulary / ontology mappings
feature classifications
mapping / portrayal rules
constraints
test fixtures or open examples
provenance
licence information
validation cases
```

Profiles should not hard-code jurisdiction-specific assumptions into the shared core when those assumptions can remain profile data.
Use the [mapping-profile authoring entry point](profiles/README.md) for the canonical package
requirements and current compatibility locations.

## Validator requirements

Every validator change must include:

- at least one clean case;
- at least one failing case;
- stable expected issue identifiers;
- a description of false-positive and false-negative risks;
- deterministic output for equivalent inputs.

Repair logic must declare its risk class and must not bypass authorization or human-review boundaries.

## Benchmark requirements

Benchmark contributions should keep prompts/tasks separate from ground truth and must document:

- task family;
- input data and redistribution status;
- expected answer/decision/evidence;
- scoring method;
- whether the case is development, validation, or sealed held-out material;
- expert-review status.

Do not tune a system against sealed held-out cases and then report them as independent evaluation.

## Compatibility and naming

The research programme is transitioning from National Map Agent (NMA) to **Authoritative Mapping Agent (AMA)**. Historical `nma` package names, CLI commands, schemas, tags, and evidence remain valid compatibility identifiers. Do not rename frozen identifiers in an unrelated contribution.
The [version policy](docs/open-source/VERSIONING.md) defines the separate AMA branding, package,
and frozen-evidence namespaces.

## Before submitting

Run the relevant project verification commands, including `make verify` when available. The normal
gate tests current AMA behavior; exact historical assertions use `make test-historical` at their
documented frozen ref. A contribution should leave existing frozen evidence reproducible unless its
purpose is an explicitly authorized new release or research experiment.

Do not commit:

- restricted or non-redistributable source documents;
- private national-mapping datasets unless explicitly licensed for redistribution;
- credentials or production secrets;
- personal data;
- model/API keys;
- generated evidence that cannot be reproduced from documented inputs.

## Licence

Code contributions are made under the repository's Apache-2.0 licence unless a file clearly states a compatible alternative. Data, specifications, and third-party assets may have separate licences; contributors must state those boundaries explicitly.
