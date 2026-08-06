# D23 blocker correction and asset re-freeze

## Scope

D23 removes the correctness defect discovered during D22 preflight without changing the demo,
data, portrayal decisions, layout system, or evidence boundary.

## Blocking defect resolved

| Defect | Before | Resolution | Result |
|---|---|---|---|
| DR1-01 | Slide 12 said `Approve the package. Then open the bridge.` after D21 had already approved and deployed the bounded Pages artifact. | The closing now says `The bridge is open. Review before extending.` and asks the audience to open the bounded release, inspect five paths, and confirm the next gate. | Fixed in presentation v1.0 |

The deck version marker was advanced from v0.9 to v1.0. The original v0.9 file is retained for
traceability.

## Verification

- Final deck: `artifacts/presentation/nma-foss4g-presentation-v1.0.pptx`
- All 12 slides rendered and were visually reviewed at full size.
- Template fidelity check passed with zero issues.
- Slide-canvas overflow check passed.
- Slide 12 speaker notes preserve the research and redistribution limitations and add
  `docs/PUBLIC-ASSETS-RC1.md` to the existing source block.
- The demo code, five-scene decisions, PMTiles boundary, and backup package were not modified.

## Explicit deferrals

| Defect | Disposition |
|---|---|
| DR1-02 — missing concise talk tracks on slides 3, 4, 6, and 7 | Deferred to D24 speaker notes work |
| DR1-03 — slide 5 screenshot is not conference-distance evidence | Keep as a handoff cue; address delivery guidance in D24 |
| DR1-04 — slides 8–11 may overrun | Preserve current scientific boundary copy; address cut cues in D24 |
| DR1-05 — uninterrupted timing and deliberate fallback transition were not measured | D22 owner waiver recorded; residual delivery risk transfers to D25/D26 |

## Acceptance status

- Blocking correctness defect: fixed.
- Changed presentation asset: versioned and re-frozen as v1.0.
- Live and fallback paths: unchanged from the passed D22 preflight; regression gates must remain
  green before D23 approval.
- Non-blocking issues: explicitly deferred above.
