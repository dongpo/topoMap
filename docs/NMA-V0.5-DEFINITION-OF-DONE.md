# NMA Runtime v0.5 Definition of Done

## Purpose

This document defines the minimum evidence required before a Runtime v0.5 issue may be considered complete. Meeting this definition does not authorize release or modification of the frozen v0.2.1 baseline.

## Code requirements

- The change implements only the behavior authorized by one Linear issue.
- The implementation satisfies every stated acceptance criterion and preserves declared non-goals.
- Modified files are limited to the issue's approved scope.
- No unrelated feature, refactor, dependency, architecture, graph-schema, ontology, or benchmark change is included.
- Error, unavailable, fallback, and approval states are explicit where the issue touches them.
- The branch contains no private data, credentials, generated local caches, or temporary artifacts.

## Tests

- Existing tests relevant to the changed behavior pass.
- Issue-approved tests cover the acceptance criteria, supported behavior, and required rejection or abstention behavior.
- Existing runtime identity, graph identity, vector identity, backend, and retrieval checks affected by the change pass.
- Required CI completes successfully on the pull request.
- Skipped or unavailable validation is listed explicitly and is not reported as passed.
- Historical failures excluded from the v0.2.1 baseline are not silently fixed, reclassified, or used to conceal a new regression.

## Documentation

- User-visible behavior, runtime contracts, configuration, operating steps, and limitations changed by the issue are documented.
- The pull request links the owning Linear issue and maps evidence to its acceptance criteria.
- Any new or changed public/private data boundary is documented without adding restricted data or changing licensing implicitly.
- Known limitations and deferred work are recorded without expanding the current issue.

## Runtime compatibility

- `nma-v0.2.1-baseline` remains unchanged and continues to resolve to its frozen commit.
- The change is based on `develop/runtime-v0.5` and is delivered through an issue-specific feature branch.
- Compatibility with `nma.runtime-baseline/0.32` is preserved unless the owning issue explicitly authorizes and documents a new Runtime v0.5 contract.
- Frozen graph, vector, Neo4j, benchmark, and evidence identities are unchanged unless the issue explicitly authorizes a versioned successor artifact.
- Backend selection and fallback behavior remain visible and testable.

## Provenance requirements

- Outputs identify the runtime or artifact version that produced them.
- Evidence-bearing behavior retains traceable feature, rule, source-document, page, and citation identifiers where applicable.
- Generated artifacts record their source identity, checksum, build or observation context, and relationship to the governing runtime version.
- Approval and execution records distinguish proposed, approved, executed, observed, and validated states.
- Private inputs remain outside the repository, and private validation is claimed only when performed in an authorized environment.

## Human acceptance

- At least one human reviewer confirms that the pull request matches the Linear issue and acceptance criteria.
- The reviewer confirms that required CI passed and that remaining limitations are accurate.
- Changes affecting approval, execution, evidence, provenance, or data boundaries receive explicit human acceptance for those surfaces.
- The reviewer confirms that no frozen baseline artifact or tag was modified.
- Merge approval is recorded through the pull-request workflow; completion of a Codex task alone is not acceptance.

## Completion record

An issue is done only when code, tests, documentation, compatibility evidence, provenance evidence, and human acceptance are all present. Missing evidence keeps the issue open or explicitly blocked; it must not be inferred from unrelated tests or prior milestones.
