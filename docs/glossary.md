# Glossary

CDR borrows vocabulary from two worlds that rarely talk to each other: evidence-based medicine
and LLM engineering. This page is for engineers who have never read a systematic review and
clinicians who have never read a stack trace. It's written for someone new to both.

## Evidence-based medicine

**Systematic review.** A literature review with a written protocol. You decide in advance how
you'll search, what you'll include, and how you'll judge quality, then you report every
decision. It's the opposite of "I read some papers and here's my take." CDR automates the
mechanical parts of this process.

**PICO.** The standard way to structure a clinical question:
**P**opulation (who), **I**ntervention (what's being tried), **C**omparator (versus what),
**O**utcome (measured how). "Does low-dose aspirin (I) versus placebo (C) reduce heart attacks
(O) in adults who already had one (P)?" The first thing CDR does is turn a free-text question
into a PICO. See `parse_question` and `core/schemas.py → PICO`.

**PRISMA / PRISMA 2020.** A reporting standard for systematic reviews. The part CDR cares most
about is the **flow diagram**: how many records were found, how many were duplicates, how many
were screened out and why, how many were included. The numbers have to add up. When they
didn't, that was an incident ([INC-003](incidents.md#inc-003-prisma-count-arithmetic-failures)).

**PRISMA-S.** The search-reporting extension of PRISMA: exactly which databases were queried,
with which strings, on which date. CDR records this as `executed_searches`.

**Screening.** Deciding whether each retrieved record is relevant. Every exclusion needs a
reason (wrong population, wrong study type, ...). In CDR each decision is a `ScreeningDecision`
with a reason code.

**RCT (randomized controlled trial).** Participants are randomly assigned to intervention or
control. It's the strongest single-study design for causal claims, because randomization
balances confounders you didn't even think of.

**Observational study.** Cohort, case-control, cross-sectional. Nobody assigns the exposure.
These studies are useful and common, but more vulnerable to confounding.

**Risk of bias.** How likely a study's design or conduct pushed its result away from the
truth. It's not the same as "quality" or "impact factor."

**RoB 2.** Cochrane's risk-of-bias tool for randomized trials. It has five domains:
randomization, deviations from intended interventions, missing outcome data, outcome
measurement, and selection of the reported result. Each domain gets *low*, *some concerns*,
or *high*. CDR enforces exactly five domains per assessment.

**ROBINS-I.** The equivalent tool for non-randomized studies, with seven domains
(confounding, selection, classification of interventions, deviations, missing data,
measurement, selective reporting).

**GRADE.** A framework for rating how certain we are in a body of evidence: *high*,
*moderate*, *low*, *very low*. Evidence starts high for RCTs and gets downgraded for risk of
bias, inconsistency, indirectness, imprecision, or publication bias. CDR assigns GRADE
certainty per claim with a structured `grade_rationale`. Full GRADE is on the
[roadmap](../ROADMAP.md).

**Meta-analysis.** Statistically pooling results across studies into one estimate (the forest
plot). CDR does not do this yet. Its synthesis is qualitative.

**PMC Open Access.** The subset of PubMed Central whose full text can be legally downloaded and
reused. It's CDR's only source of full text, which is a real limitation.

**MCID (minimal clinically important difference).** The smallest change in an outcome that
patients would actually notice. It shows up in CDR's proposed study designs.

## CDR-specific terms

**Record.** One retrieved item: a PubMed article or a ClinicalTrials.gov registration.
Records are immutable once created.

**Snippet.** A specific passage of text from a specific record, with a pointer back to where
it came from (`source_ref`). Snippets are the atoms of traceability.

**Study card.** Structured data extracted from an included study: design, sample size,
population, outcomes.

**Claim (`EvidenceClaim`).** A statement CDR makes about the evidence. **Every claim must cite at
least one snippet**, and the schema enforces this. A claim without evidence can't be
constructed.

**Citation laundering.** When an LLM writes a plausible claim and attaches a real citation that
doesn't support it. This is the failure mode CDR exists to prevent
([INC-001](incidents.md#inc-001-citation-laundering)).

**Verification.** After synthesis, each claim is checked against its cited snippets:
*verified*, *partial*, *contradicted*, or *unverifiable*.

**Skeptic / critique.** An adversarial pass that attacks each claim along fixed dimensions
(internal validity, overstatement, confounders, ...) before anything is published.

**Composed hypothesis (A + B ⇒ C).** A new hypothesis built by chaining verified claims:
if A affects B and B affects C, maybe A affects C. Each one comes with a mechanistic chain,
a threat analysis (rival explanations, confounders, gaps) and a proposed study to test it.
See [the vision](vision.md).

**DoD level ("definition of done").** How strict a run is:

| Level | Name | What changes |
|---|---|---|
| 1 | Exploratory | Heuristic fallbacks allowed. Fast, forgiving, good for poking around. |
| 2 | Research-grade | Structured LLM output required (no Markdown-parsing fallback); ≥80% of claims must pass verification. |
| 3 | Full | Level 2, plus a GRADE rationale on every claim, ≥95% verification, and hypothesis composition turned on. |

**Run status.** A finished run ends in one of these states: `completed` (publishable),
`insufficient_evidence` (not enough studies to say anything), `unpublishable` (the evidence
didn't pass the gates), or `partially_publishable`. **An unpublishable run is the system
working as designed, not a crash.**

**Golden set.** A small set of clinical questions with known evidence profiles, used for
evaluation. See [evaluation.md](evaluation.md) and [Case Files](case-files.md).

## Engineering terms clinicians will run into

**LLM provider.** The company or server running the language model (Gemini, Groq, OpenAI, ...).
CDR can use eight of them and falls back between them.

**LangGraph / StateGraph.** The library that runs CDR's pipeline as a fixed graph of steps
("nodes") sharing one state object. It's predictable and debuggable. It isn't an autonomous
agent.

**Pydantic model / schema / contract.** A typed definition of what a piece of data must look
like. If a step produces something that doesn't match, it fails immediately instead of
passing garbage downstream.

**Mocked test.** A test that fakes external services (PubMed, the LLM) so it runs offline,
fast and deterministically. The whole backend test suite is mocked.
