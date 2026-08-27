# Mapping Knowledge Profiles

Mapping Knowledge Profiles are reusable authority- or community-specific packages that bind AMA
Core to an explicit body of mapping knowledge without embedding jurisdiction-specific assumptions
in the core.

The current NLSC reference material remains in its compatibility locations under `data/`,
`assets/`, `schemas/`, and `benchmark/`; moving those frozen paths would break reproducibility.
This directory is the canonical profile-authoring entry point, not a duplicate of those artifacts.

A contributed profile should declare, as applicable:

- stable profile identifier and version;
- publisher/authority and source registry;
- source licence and redistribution boundary;
- vocabulary, ontology, feature, and schema mappings;
- reviewed mapping or portrayal rules and constraints;
- candidate-to-reviewed governance status;
- provenance and evidence references;
- validation fixtures, benchmark cases, and expected failures;
- compatibility requirements for AMA Core and the `nma` package.

Automatically extracted knowledge is candidate material and must not become authoritative
executable knowledge until it passes the profile's declared review boundary.
