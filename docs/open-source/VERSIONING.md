# AMA version and compatibility policy

AMA uses separate version namespaces so public branding can evolve without rewriting reproducible
software or evidence identities.

## Public project identity

**Authoritative Mapping Agent (AMA)** is the current project and research-programme name. This
branding change is not, by itself, a new software release. No `ama-v1.0` tag is created by the
canonical reconciliation.

## Compatibility package identity

The Python distribution remains `national-map-agent` at version `0.2.0`; imports and CLI commands
remain `nma`, `nma-bench`, and `nma-validation-bench`. `CITATION.cff` uses the AMA title and the
same `0.2.0` software version. These identifiers remain stable through the FOSS4G transition.

## Frozen evidence identity

Annotated NMA tags such as `nma-v1.0-final`, `nma-road-v1.0-final`,
`nma-core-v1.0-final`, `nma-build-v1.0-final`, `nma-generalization-v1.0-final`, and
`nma-demo-v1.0-final` identify immutable historical engineering baselines. Their `v1.0` values are
evidence-series versions, not replacements for the Python distribution version.

Historical v0.3/v0.32 identifiers and deployment-specific release schemas also remain unchanged.
They identify bounded candidates or artifacts and do not define the current package version.

## Future releases

A new AMA release tag requires a reviewed release scope, updated package/citation metadata where
appropriate, a clean validation matrix, documented migration and compatibility behavior, and an
explicit release decision. Repository restructuring alone does not meet that bar.
