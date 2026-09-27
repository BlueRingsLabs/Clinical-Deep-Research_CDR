# Vision

> Short version: first earn the right to be trusted with evidence, then use that trust to
> propose things nobody has tested.

## The problem worth solving

Medicine has open problems that aren't waiting on a new experiment. They're waiting on someone
to connect results that are already published.

This isn't a new idea. In 1986 Don Swanson, an information scientist, noticed two groups of
papers that never cited each other:

- **A → B:** dietary fish oil lowers blood viscosity and platelet aggregation.
- **B → C:** patients with Raynaud's syndrome have high blood viscosity and platelet aggregation.

He proposed **A → C**: fish oil might help Raynaud's. Nobody had tested it. A clinical trial
later found an effect. He repeated the trick with magnesium and migraine in 1988. The field is
called *literature-based discovery*, and it's been around for almost forty years.

Swanson did it by hand with a library. The literature is now roughly 40 million PubMed records
and grows by more than a million a year. No human reads across all of it. And LLMs, which can
read across all of it, invent things.

**CDR is an attempt to build the machine Swanson would have wanted: one that reads everything,
connects across literatures, and never lies about where a claim came from.**

## Why the order of the work matters

The obvious version of this project is "ask an LLM for novel hypotheses." It takes an afternoon
to build and produces confident, citation-shaped nonsense. A hypothesis is only worth
something if every link in its chain is real.

So CDR climbs a ladder, and each rung has to hold before the next one means anything:

| Rung | Capability | State |
|---|---|---|
| 1 | **Retrieve and trace.** Find the studies, keep a snippet-level trail for every claim. | ✅ Works |
| 2 | **Synthesize honestly.** Grade the evidence, attack it, refuse to publish when it's weak. | ✅ Mostly works: GRADE is partial, RoB 2 is limited by full-text access |
| 3 | **Connect.** Extract mechanisms from verified claims and chain them: A → B, B → C, so A → C? | 🧪 Implemented in [`composition/`](../src/cdr/composition/), not yet producing on real runs |
| 4 | **Stress-test.** Rival hypotheses, confounders, evidence gaps. Kill weak ideas early. | 🧪 Implemented (`ThreatAnalysis`), untested at scale |
| 5 | **Propose the experiment.** Population, comparator, outcome, design, sample size. | 🧪 Implemented (`ProposedStudyDesign`), untested at scale |
| 6 | **Prove it works.** Rediscover known discoveries from the literature that existed *before* they were made. | ❌ Not started |

Rungs 1–2 are the reason anyone should trust rungs 3–5. Rung 6 is the reason anyone should
believe them.

## What "working" will mean

Talking about hypothesis generation is easy. The hard part is showing it produces something
useful. The benchmark CDR is aiming for is **retrodiction**:

1. Take a discovery with a known date (fish oil and Raynaud's, 1986).
2. Freeze the literature at the year before.
3. Run CDR on the relevant question with only that literature available.
4. See whether the known discovery shows up among the proposed hypotheses, and how far down
   the list it is.

If CDR can rediscover things humans took years to find, from the evidence those humans had,
then its new proposals are worth a clinician's time. If it can't, no amount of README prose will
fix that. [Case Files](case-files.md) is where these test cases live.

## Who it's for

- **Now:** engineers and researchers who want to build and stress-test the engine.
- **Soon:** clinical researchers, epidemiologists and methodologists who want a fast,
  auditable first pass over a question, and who will tell us when it's wrong.
- **Eventually:** anyone doing research at the edges of a field: rare diseases, drug
  repurposing, conditions that fall between specialties.

## What CDR will not become

- **A diagnostic tool.** It reasons about literature, not about patients.
- **A replacement for peer review, trials, or clinical judgment.** A hypothesis is a reason to
  run an experiment, not a reason to change practice.
- **An oracle.** Every output shows its evidence chain so a human can check it and throw it out.

## Open problems (pick one)

These are real, unsolved, and mostly independent of each other:

- **Get the composer producing on real runs.** Composition only runs at DoD level 3 and needs
  at least two verified claims. What blocks it in practice, and is the level-3 gate too strict
  for exploratory use?
- **Cross-literature retrieval.** Swanson's insight depended on finding the B-literature that
  the A-literature never cites. Today CDR runs one search per question. Two-hop retrieval is
  the missing piece.
- **Time-sliced retrieval.** The retrodiction benchmark needs "PubMed as of year X".
  PubMed supports date filters, so this is mostly plumbing and evaluation design.
- **Ranking hypotheses.** Given 50 candidate A → C links, which ones deserve attention?
  Novelty, mechanistic plausibility, and evidence strength pull in different directions.
- **Full-text access.** Risk-of-bias assessment on abstracts is structurally weak
  ([INC-002](incidents.md#inc-002-uniform-rob2-some-concerns)). More open-access sources help.

If one of these grabs you, open a discussion or an issue. Half-formed ideas are welcome.
Unverified claims aren't.
