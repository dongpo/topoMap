# NMA Runtime v0.5 Development Rules

## Purpose

These rules establish the development-governance baseline for NMA Runtime v0.5. They control how later work is proposed, isolated, reviewed, and accepted. They do not authorize a feature, architecture, graph, dependency, or benchmark change by themselves.

## Baseline policy

- `nma-v0.2.1-baseline` is the immutable engineering baseline.
- The tag must continue to resolve to commit `6c7eef1259bfc3001afae761a7ae47321612a709`.
- Frozen graph, vector, runtime, Neo4j, verification, and documentation artifacts must not be rewritten under the existing tag.
- Runtime v0.5 development starts from `develop/runtime-v0.5`, created from `nma-v0.2.1-baseline`.
- A correction to the frozen baseline requires a separately reviewed version and tag; the existing tag must never be moved.

## Branch policy

The branch structure is:

```text
main
 |
 +-- nma-v0.2.1-baseline
 |
 +-- develop/runtime-v0.5
        |
        +-- feature/<linear-issue>-<short-scope>
```

- Every implementation change requires a feature branch created from `develop/runtime-v0.5`.
- Feature branches must identify the owning Linear issue, for example `feature/HERO-01-school-resolution`.
- Direct feature commits to `main` or `develop/runtime-v0.5` are prohibited.
- Every feature branch requires a pull request back to `develop/runtime-v0.5`.
- Required CI checks must pass before merge.
- Pull requests must remain limited to their approved issue scope and acceptance criteria.
- Merging to `main`, creating a release tag, or changing release state requires a separate authorized release task.

## Codex policy

Every Codex development task must have:

- exactly one owning Linear issue;
- an explicit objective and non-goals;
- testable acceptance criteria;
- an explicit list or narrow category of files permitted to change;
- existing verification commands to run, plus any issue-approved tests required by the acceptance criteria; and
- a stop condition that prevents continuation into the next issue or milestone.

Codex must inspect the branch and dirty-worktree state before editing. Unexpected or unrelated changes must be reported and excluded. A task must not silently expand scope, combine issues, rewrite frozen artifacts, or claim unavailable private-data validation.

## Review and CI policy

- CI must exercise the approved tests for the issue and the existing runtime compatibility checks relevant to the changed surface.
- A human reviewer must confirm scope, acceptance evidence, provenance, data-boundary compliance, and compatibility with the Runtime v0.5 branch.
- A failed required check blocks merge unless the owning issue explicitly classifies the failure and a reviewer approves that classification.
- Historical failures already excluded by `docs/NMA-V0.2.1-HISTORICAL-TEST-STATUS.md` must not be repaired or redefined incidentally.

## Prohibited actions

- direct modification of `main`;
- moving, deleting, or recreating `nma-v0.2.1-baseline`;
- modifying frozen artifacts through an existing tag;
- architecture expansion without explicit Linear issue approval;
- undocumented runtime or configuration changes;
- graph-schema, ontology, benchmark, or dependency expansion outside an approved issue;
- adding private or non-redistributable data to Git history;
- bypassing the approval workflow or required CI; and
- combining unrelated refactors, cleanup, or presentation work with a feature issue.

## Scope boundary

Potential Runtime v0.5 work includes School Hero Agent workflow, planning, evidence-grounded execution, approvals, and provenance. Listing those areas does not approve their implementation. Each requires its own Linear issue, feature branch, acceptance criteria, review, and CI evidence.
