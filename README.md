<div align="center">

# Clinical Deep Research (CDR)

**An open research engine that reads the clinical literature, shows its work,
and is being built to propose the questions nobody has tested yet.**

[![CI](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/actions/workflows/ci.yml/badge.svg)](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Status: open alpha](https://img.shields.io/badge/status-open_alpha-orange.svg)](ROADMAP.md)
[![Good first issues](https://img.shields.io/github/issues/BlueRingsLabs/Clinical-Deep-Research_CDR/good%20first%20issue?label=good%20first%20issues&color=7057ff)](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/issues?q=is%3Aopen+label%3A%22good+first+issue%22)

<img src="docs/assets/evidence-chain.svg" alt="A real CDR claim traced from the question to its snippets and the PubMed paper they came from" width="860" />

</div>

> **Not medical advice.** CDR is a research tool. It does not diagnose, prescribe, or replace
> clinical judgment. Everything it produces needs expert review. See [DISCLAIMER.md](DISCLAIMER.md).

---

## Why this exists

A good systematic review takes months. By the time it's published, part of it is already
out of date. LLMs can read faster than any team of reviewers, but left alone they do something
unacceptable in medicine: they make things up and cite real papers for claims those papers
never made.

**CDR is an attempt to get the speed without the fabrication.** Every claim it outputs points
to a specific passage in a specific study. If the evidence doesn't hold up, the report is marked
unpublishable instead of being dressed up to look confident. An honest "the evidence isn't there"
beats a confident wrong answer, every time.

That's the part that works today. The long game is bigger.

## Where this is going

AI systems have started producing real results on open problems in mathematics. Medicine has
its own open problems: associations nobody can explain, drugs that work for reasons nobody fully
understands, patients who fall between two specialties and two literatures. Some of those
answers may already be sitting in the papers, split across studies that never cite each other.
It's happened before: in 1986 Don Swanson connected fish oil to Raynaud's syndrome by reading two
literatures that had never met, and a trial later backed him up.

**CDR's goal is to become an engine that can propose credible, testable clinical hypotheses:**
"A is linked to B, B is linked to C, so here's why A might affect C, here's what could make
that wrong, and here's the study that would settle it."

There's a rule behind the order of the work: **you don't get to speculate until you can prove
you don't hallucinate.** That's why the evidence engine came first, and why it's strict.

The first version of the hypothesis layer already exists
([`composition/`](src/cdr/composition/)). It extracts mechanistic relations, chains them into
A + B ⇒ C hypotheses, attacks them with rival explanations and confounders, and proposes a study
design to test them. **It hasn't produced a verified hypothesis on a real run yet.** Getting it
there is the most interesting open problem in this repo. [The vision doc](docs/vision.md) has
the details.

## What works today

| | Status |
|---|---|
| PICO extraction from a free-text clinical question | ✅ Works |
| PubMed + ClinicalTrials.gov search, dedup, hybrid ranking (BM25 + dense + rerank) | ✅ Works |
| LLM screening with explicit exclusion reasons (PRISMA-style) | ✅ Works |
| Full-text parsing from PMC Open Access | ✅ Works (abstracts when no OA full text) |
| Risk of bias: RoB 2 (trials) and ROBINS-I (observational) | ⚠️ Works, but weak on abstracts alone ([why](docs/incidents.md#inc-002-uniform-rob2-some-concerns)) |
| Evidence claims traced to exact snippets + verification gates | ✅ Works (reports carry snippet IDs; including the snippet text is an open issue) |
| Skeptic agent that attacks claims before publication | ✅ Works |
| Reports in JSON / Markdown / HTML, API, basic web UI | ✅ Works |
| Hypothesis composition (A + B ⇒ C) | 🧪 Implemented and tested, not yet producing on real runs |
| Full GRADE, meta-analysis, Embase/Cochrane, streaming, auth | ❌ Not yet ([roadmap](ROADMAP.md)) |

Real runs on free-tier 8B models include 8 to 27 studies, produce 3 or 4 traced claims, and take
7 to 27 minutes. The raw outputs are in [`examples/output/online/`](examples/output/online/),
unedited, and [the run notes](docs/online-run-notes.md) describe how each one was made.

They're also humbling. On aspirin after a heart attack, one of the best-established answers in
cardiology, the 8B run rated every claim *low* certainty. That's the kind of gap
[Case File CF-0001](eval/cases/CF-0001-aspirin-secondary-prevention.json) exists to catch, and
closing it is real work waiting to be done.

## Try it

You need [uv](https://docs.astral.sh/uv/) and Python 3.12. Node 20 is only needed for the UI.

```bash
git clone https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR.git
cd Clinical-Deep-Research_CDR
make setup          # Python deps (uv), UI deps (npm), creates .env
make demo           # no API keys: renders the bundled sample report
make test           # the whole backend suite runs offline in under a minute
```

> The bundled `examples/output/sample_report.json` is **illustrative**. It was written by hand to
> show every field of the report format, and its PMIDs are placeholders. For real output, look at
> [`examples/output/online/`](examples/output/online/).

**Run a real question.** Put one LLM key in `.env`; Gemini, Groq and OpenRouter all have free
tiers ([providers guide](docs/providers.md)). Then:

```bash
make dev            # API on http://localhost:8000/docs

curl -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{"research_question": "Is low-dose aspirin effective for secondary prevention of cardiovascular events?", "max_results": 20}'

# → {"run_id": "...", "status": "..."}   then poll:
curl http://localhost:8000/api/v1/runs/<run_id>
```

Or run everything in containers with `make docker-up`. The UI is at http://localhost:5173.

## How it works

<div align="center">
<img src="docs/assets/architecture.svg" alt="The 13-node CDR pipeline" width="800" />
</div>

A 13-node [LangGraph](https://github.com/langchain-ai/langgraph) pipeline with typed contracts
between every step. If a node hands the next one something malformed, the run fails loudly
instead of quietly producing garbage.

| Phase | Nodes | What happens |
|---|---|---|
| **Retrieve** | parse_question → plan_search → retrieve → deduplicate | Question → PICO → database queries → records |
| **Screen** | screen → parse_docs → extract_data | Include/exclude with reasons, pull full text, extract study data |
| **Analyze** | assess_rob2 → synthesize → critique | Risk of bias, evidence claims, adversarial critique |
| **Publish** | verify → compose → publish | Check every claim against its sources, compose hypotheses, write the report |

The strictness is configurable through **DoD levels** ("definition of done"):
1 = exploratory, 2 = research-grade, 3 = full gates plus hypothesis composition. The
[glossary](docs/glossary.md) explains these and every other acronym in this repo.

Start with [docs/architecture.md](docs/architecture.md). If you want to know why it's built this
way, read [docs/case-study.md](docs/case-study.md) and the
[incident postmortems](docs/incidents.md). They're the honest version.

## Contributing

CDR sits at an awkward intersection: engineers who don't know what RoB 2 is, and clinicians
who don't know what LangGraph is. **Both are needed**, and neither has to learn the other's job
to help.

- **Engineers:** [good first issues](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/issues?q=is%3Aopen+label%3A%22good+first+issue%22),
  or grep for `loose end` in the code for things that are half-wired and waiting.
- **Clinicians, methodologists, researchers:** run a question you know the answer to and tell us
  where CDR got it wrong. A precise "this claim is not supported by that paper" report is worth
  more than most PRs. There's an [issue form for exactly that](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/issues/new?template=evidence_problem.yml).
- **Everyone:** [Case Files](docs/case-files.md) are clinical questions with known answers that
  CDR has to get right. Adding one is the fastest way to make the engine better.

Read [CONTRIBUTING.md](CONTRIBUTING.md). It opens with the three-step version.

## Documentation

| | |
|---|---|
| [docs/vision.md](docs/vision.md) | Where CDR is going and why the order of work matters |
| [docs/glossary.md](docs/glossary.md) | PICO, PRISMA, RoB 2, GRADE, DoD levels in plain language |
| [docs/architecture.md](docs/architecture.md) | Pipeline, data model, stage contracts |
| [docs/case-study.md](docs/case-study.md) | Design decisions, trade-offs, hard problems |
| [docs/incidents.md](docs/incidents.md) | Postmortems of things that broke |
| [docs/evaluation.md](docs/evaluation.md) | How output quality is measured |
| [docs/report-anatomy.md](docs/report-anatomy.md) | How to read and audit a CDR report |
| [docs/providers.md](docs/providers.md) | LLM provider setup and free tiers |
| [ROADMAP.md](ROADMAP.md) | What's next |

## Who's behind this

CDR was started by Gonzalo Romero ([@glromero](https://github.com/glromero)) and lives at
[BlueRingsLabs](https://github.com/BlueRingsLabs). It's an open project: the roadmap, the
arguments and the mistakes all happen in public. See [GOVERNANCE.md](GOVERNANCE.md) for how
decisions get made.

## Citing CDR

If you use CDR in research, cite it with the metadata in [CITATION.cff](CITATION.cff). GitHub
shows a "Cite this repository" button in the sidebar.

## License

[Apache 2.0](LICENSE).
