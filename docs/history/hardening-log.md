# Hardening log (January 2026)

Before the first public release, CDR went through four rounds of internal review. Each round
listed findings by severity, fixed them, and wrote them down as an "ADR". Those notes were in
Spanish and written for one person. This is the English summary of what they found and what
changed, kept because **most of the pipeline's strictness exists because of a specific failure
listed here.**

If you're wondering why a piece of code is so paranoid, the reason is probably below.

---

## Round 1: "claims must be real"

| Finding | Severity | What changed |
|---|---|---|
| A node tried to mutate `EvidenceClaim.supporting_snippet_ids` on a frozen Pydantic model | Critical | Filtered claims are rebuilt with `model_copy(update=...)`. Immutability stays. |
| When no snippet existed, the synthesizer **invented** snippet IDs like `{record_id}_snip_0` | Critical | The fallback was removed. No real snippet means no claim, and the run can end as `insufficient_evidence`. |
| Screening without an LLM included studies because their abstract was longer than 100 characters | High | Replaced with PICO-based rules. Every exclusion gets a reason code. |
| When RoB 2 assessment failed, the "high risk" fallback never reached the GRADE certainty of affected claims | Medium | The downgrade now propagates to GRADE. |
| 18 retrieval tests were skipped | Medium | Tracked. Fixed in round 4. |

## Round 2: "don't over-correct"

Round 1 made the snippet filter too aggressive. It started rejecting *real* snippets whose IDs
happened to end in `_snip_0`.

| Finding | What changed |
|---|---|
| Real snippets filtered out by their ID format | Canonical format fixed as `{record_id}_snip_{index}`. The parser accepts it, and **only the gate in `synthesize` decides whether a snippet exists**. |
| `_placeholder` snippet IDs leaking into the flow | Removed. A claim without real support is not created. |
| Heuristic screening threshold (20% PICO match) too loose | Requires ≥2 PICO components (P+I or P+O) and a 0.4 threshold. The heuristic path logs a warning. |
| GRADE rationale was free text | Standardized structure. |

Design rule that came out of this: **one gate per invariant**. Parsers parse, gates judge. When
both try to judge, they disagree.

## Round 3: "every included study must carry evidence"

| Finding | Severity | What changed |
|---|---|---|
| `_parse_markdown_claims()` bypassed snippet-ID validation | Critical | All claim parsers get `valid_snippet_ids`. There's one validation path. |
| Included records could reach synthesis with no text at all | High | Records without usable content count as PRISMA `reports_not_retrieved`. PRISMA counts gained `reports_sought` / `reports_assessed`. |
| The heuristic screening fallback could silently power a research-grade run | High | Introduced **DoD levels**. Level ≥2 requires LLM screening. |
| GRADE downgrade reasons lived only in a free-text `limitations` field | Medium | Structured `grade_rationale` per claim. |

## Round 4: "enforce it end to end"

| Finding | Severity | What changed |
|---|---|---|
| The published report dropped the structured evidence rationale | Critical | The report carries each claim's full traceability (snippets, GRADE rationale, verification). |
| `dod_level` was only enforced during screening | High | Enforced end to end: early gates in `synthesize` (level 2 = structured output required, level 3 = rationale required) and final gates in `publish` (verification coverage). |
| 18 retrieval tests skipped because of API drift | High | Rewritten against current APIs. Zero skipped. |
| Abstract-length cutoff had no full-text fallback | Medium | Deferred at the time because it needed full-text infrastructure. PMC Open Access retrieval came later ([INC-002](../incidents.md#inc-002-uniform-rob2-some-concerns)). |
| `grade_rationale` completeness not gated | Medium | Gated at level 3. |

---

## What carried forward

- **Immutability** of records and claims ([INC-003](../incidents.md#inc-003-prisma-count-arithmetic-failures)).
- **No fabricated support, ever.** No snippet, no claim ([INC-001](../incidents.md#inc-001-citation-laundering)).
- **Honest negative outcomes.** `insufficient_evidence` and `unpublishable` are valid results.
- **DoD levels** as the single strictness knob. See the [glossary](../glossary.md#cdr-specific-terms).

The original notes are in git history (`docs/adr/`, removed in the commit that added this file)
if you want the line-by-line detail.
