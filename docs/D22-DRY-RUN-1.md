# D22 dry run #1 — timing and defect log

This log evaluates the complete FOSS4G Hiroshima talk before any individual slide is edited. It
uses the frozen five-scene Demo RC1, public-assets RC1, presentation v0.9, and the approved backup
bundle.

## Run identity

- Linear issue: GEO-80 / D22
- Deck: `artifacts/presentation/nma-foss4g-presentation-v0.9.pptx`
- Demo sequence: [`FIVE-SCENE-DEMO.md`](FIVE-SCENE-DEMO.md)
- Backup runbook: [`nma-demo-backup/RUNBOOK.md`](../artifacts/presentation/nma-demo-backup/RUNBOOK.md)
- Conference format: regular talk, 20 minutes speaking + 5 minutes Q&A
- Target content duration: **17:20**
- Required delivery buffer: **2:40**
- Actual uninterrupted run: **pending presenter rehearsal**

The 20-minute speaking limit comes from the official
[FOSS4G Hiroshima 2026 regular-talk format](https://2026.foss4g.org/en/call-for-papers/general-sessions/).

## Preflight completed on 2026-08-05

| Surface | Result | Evidence |
|---|---|---|
| Five-scene reset | Passed | 5/5 scenes, pages 61/11/60/50/69, 2/2 abstention controls |
| Frozen artifact gate | Passed | 16/16 frozen artifacts verified |
| Evidence-only runtime | Passed | 2 browser modes and pinned-runtime manifest verified |
| Hosted fallback UI | Passed | 5/5 scene controls returned the frozen codes, actions, and pages; 0 console errors/warnings |
| Portable backup | Passed | Manifest, video, playback page, five screenshots, and five evidence images matched checksums |
| Presentation structure | Passed | 12 slides, 12 source-note blocks, no slide-canvas overflow |
| Public release | Passed | Bounded evidence-only Pages artifact deployed in run #36 |
| Full local browser path | Passed | Presenter-started preview reached `Map ready · local PMTiles · pinned runtime cache enabled`; all five live scene controls returned the expected evidence page and portrayal action, with zero browser errors or warnings |

## Target timing card

Start the timer when slide 1 appears. Do not pause during the live-to-fallback transition. Record
actual cumulative time at every checkpoint.

| Segment | Target | Target cumulative | Actual cumulative | Cut cue if late |
|---|---:|---:|---:|---|
| Slide 1 — contribution | 0:40 | 0:40 | — | State only the research object and bounded claim |
| Slide 2 — auditability problem | 1:20 | 2:00 | — | Keep the school example; remove the manual-map aside |
| Slide 3 — evidence-bearing architecture | 1:30 | 3:30 | — | Name the six stages; explain only the two trust gates |
| Slide 4 — five capabilities | 0:50 | 4:20 | — | One phrase per scene |
| Slide 5 — demo handoff | 0:20 | 4:40 | — | Say the order and begin immediately |
| Live demo — five frozen scenes | 5:00 | 9:40 | — | School 90 s; four scenes 30 s each; boundary 60 s |
| Slide 6 — golden path | 1:00 | 10:40 | — | Trace one path, not all metadata fields |
| Slide 7 — RC1 stability | 0:50 | 11:30 | — | Read only 20/20, 10/10, and zero blockers |
| Slide 8 — data boundary | 1:20 | 12:50 | — | Contrast referenced authority with redistributable assets |
| Slide 9 — review command | 0:50 | 13:40 | — | Explain the gate; do not narrate implementation details |
| Slide 10 — benchmark gates | 1:00 | 14:40 | — | Development set now; held-out and named baselines next |
| Slide 11 — research roadmap | 1:40 | 16:20 | — | Connect question, method, limits, and next gates |
| Slide 12 — closing decision | 1:00 | 17:20 | — | End on the open, auditable bridge and invitation |

### Timer thresholds

- At slide 5: green ≤ 4:40; amber 4:41–5:10; red > 5:10.
- After the demo: green ≤ 9:40; amber 9:41–10:20; red > 10:20.
- At slide 10: green ≤ 14:40; amber 14:41–15:20; red > 15:20.
- Stop content at 18:30 even if a detail remains; preserve at least 1:30 before Q&A.

## Frozen live sequence

| Order | Scene | Budget | Required visible proof | Spoken capability |
|---:|---|---:|---|---|
| 1 | School | 90 s | `9920103`, page 61, rule, graph path, action | Versioned retrieval and evidence path |
| 2 | Fire hydrant | 30 s | `9350906`, page 11, 2 × 2.5 mm | Deterministic symbol and dimensions |
| 3 | Police | 30 s | `9910603`, page 60, symbol + name | Alias resolution and label |
| 4 | Fish pond | 30 s | `9740100`, page 50, fill/outline + fish | Geometry-aware compound portrayal |
| 5 | Post office | 30 s | `9950201`, page 69, `text_only`, abstention | Conditional exception and guardrail |

Use the remaining 60 seconds to state the authority, review, redistribution, and expert-review
boundaries. Do not improvise a sixth scene or an unsupported factual claim.

## Fallback transition drill

1. Begin the live path at `http://127.0.0.1:8080/nmaAgentDemo.html`.
2. At the nominated failure cue, switch to `?mode=degraded` without stopping the timer.
3. Confirm that all five decisions and evidence paths remain available.
4. If the local server fails, open `artifacts/presentation/nma-demo-backup/PLAYBACK.html`.
5. If video playback fails, continue with the five frozen screenshots and matching evidence images.
6. If recovery exceeds two minutes, stop troubleshooting and use screenshots.

Record the transition start, usable fallback time, narration gap, and any audience-visible error in
the defect table.

## Initial defect and observation log

These observations come from the full-slide review and automated preflight. Their severity must be
confirmed during the uninterrupted presenter run.

| ID | Area | Severity | Observation | Owner | Due | Disposition |
|---|---|---|---|---|---|---|
| DR1-01 | Closing narrative | Blocking correctness | Slide 12 still asks reviewers to approve the package before public deployment, but D21 is already approved and deployed. | Codex + dongpo | 08/26 | Fix in D23 after timed run confirms the closing transition |
| DR1-02 | Speaker notes | High | Slides 3, 4, 6, and 7 contain sources but no spoken transition or concise talk track; timing may depend on improvisation. | Codex + dongpo | 08/27 | Add notes in D24; do not edit before dry run #1 |
| DR1-03 | Demo handoff | Medium | Slide 5's embedded UI screenshot is not readable at conference distance; it must function only as a handoff cue, not evidence. | dongpo | 08/25 | Validate on the presentation display during the timed run |
| DR1-04 | Research section | Medium | Slides 8–11 contain the densest prose and are the most likely source of overruns. | dongpo | 08/25 | Record actual cumulative times; apply the cut cues above |
| DR1-05 | Live-path verification | Pending human step | Local MapLibre execution and all five live scenes passed. Only the uninterrupted talk timing and deliberate live-to-fallback transition remain to be measured by the presenter. | dongpo | 08/25 | Complete the uninterrupted rehearsal and enter actual times |

## Presenter result — complete immediately after the run

- Start time:
- End time:
- Actual content duration:
- Q&A buffer remaining:
- Live demo duration:
- Fallback transition duration, if exercised:
- First red timing threshold:
- Required cuts:
- Blocking defects confirmed:
- New defects:
- Overall result: `pass` / `pass with D23 fixes` / `blocked`

### Acceptance checklist

- [ ] One uninterrupted 20-minute-slot rehearsal completed with a timer.
- [ ] Actual cumulative times recorded for all 13 segments.
- [ ] Live demo shows the five required decisions and evidence.
- [ ] One fallback transition is timed without stopping narration.
- [ ] Narrative, handoff, UI, evidence, and fallback observations are logged.
- [ ] Every blocking defect has an owner and due date.
- [ ] Required cuts preserve the bounded authority claim.

Do not close GEO-80 until the presenter result and acceptance checklist are completed.
