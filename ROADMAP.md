# Roadmap

Two tracks run in parallel. The **evidence track** makes CDR trustworthy. The **discovery track**
makes it useful for what it's actually for: proposing hypotheses (see [the vision](docs/vision.md)).
Discovery work only counts if the evidence track underneath it holds.

Dates are deliberately absent. This is an open project and things ship when they're right.
Items marked 🙋 are well scoped for a new contributor.

---

## Now: v0.1 open alpha (released February 2026)

Working end to end: question → PICO → PubMed + ClinicalTrials.gov → screening → PMC full text →
RoB 2 / ROBINS-I → traced claims → skeptic critique → verification → JSON/Markdown/HTML report.
Eight hosted LLM providers plus any local OpenAI-compatible server. FastAPI + a basic React UI.

Known limits: qualitative synthesis only, PubMed + CT.gov only, no auth, no streaming, runs take
7–27 minutes on free tiers, and the hypothesis composer has not yet produced on a real run.

## Next: v0.2

### Evidence track

| Item | Why it matters |
|---|---|
| Put the snippet text in the report 🙋 | Reports carry snippet IDs only, so a reader can't audit a claim without re-running |
| Full GRADE (all five downgrade domains) | Certainty labels today are partial, and 8B runs under-rate strong evidence ([CF-0001](eval/cases/CF-0001-aspirin-secondary-prevention.json)) |
| Wire up the parsed-but-dropped metadata 🙋 | CT.gov phase/status/enrollment and PubMed study type are extracted and then thrown away (grep `loose end`) |
| Enforce the observational-design check 🙋 | `pico_allows_observational` is computed and never used |
| Streaming progress (SSE) | Runs take minutes. Watching a spinner that long is bad UX |
| Human-in-the-loop checkpoints | Let an expert correct screening/extraction mid-run |
| More full-text sources (Europe PMC, Unpaywall) | RoB 2 on abstracts is structurally weak |
| Replace debug `print()` calls with structured logging 🙋 | They leak into API logs |

### Discovery track

| Item | Why it matters |
|---|---|
| Get the composer producing on real runs | The whole point. Find out what blocks it (DoD-3 gate? too few verified claims?) |
| Re-measure the golden set, with outputs committed | The v0.1 baseline has no run artifacts behind it ([why this matters](docs/evaluation.md#about-baseline_v0_1)) |
| Case Files: first 10 cases 🙋 | Known-answer questions are how we know anything works ([docs/case-files.md](docs/case-files.md)) |
| Time-sliced retrieval ("PubMed as of year X") | Prerequisite for the retrodiction benchmark |
| Two-hop retrieval (find the B-literature) | Swanson-style discovery needs literatures that don't cite each other |

### Project

| Item | Why it matters |
|---|---|
| Re-enable the online canary | Real-provider regression checks, suspended since the free tiers ran dry |
| Make mypy clean enough to enforce 🙋 | It runs, but only as advisory |

## Later: v1.0

- Retrodiction benchmark: rediscover known discoveries from pre-discovery literature
- Hypothesis ranking (novelty × plausibility × evidence strength)
- Quantitative synthesis: pooled estimates, forest plots, heterogeneity
- Embase / Cochrane CENTRAL / grey literature (access permitting)
- Living reviews: scheduled re-runs with diffs
- Multi-user deployments: auth, audit log
- Evaluation against expert-conducted systematic reviews, published

---

Want to take something? Comment on the issue, or open one if it doesn't exist.
See [CONTRIBUTING.md](CONTRIBUTING.md).
