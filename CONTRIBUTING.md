# Contributing to CDR

Thanks for being here. Short version:

1. `make setup && make check` (about 5 minutes the first time)
2. Pick something: a [good first issue](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/issues?q=is%3Aopen+label%3A%22good+first+issue%22),
   a `loose end` in the code, or a [Case File](docs/case-files.md)
3. Open a small PR. Draft is fine. We'll help you get it over the line.

The rest of this page is detail. Read it when you need it.

---

## Pick your lane

CDR needs two kinds of expertise that rarely sit in the same person. You don't need both.

**You write code.** You don't need to know what a forest plot is. The pipeline is typed
end to end, the tests run offline in seconds, and the [glossary](docs/glossary.md) covers the
clinical vocabulary. Start with a `good first issue` or a loose end (below).

**You know clinical research** (clinician, epidemiologist, methodologist, librarian, student).
You don't need to write code. The most valuable things you can do:

- Run a question you know the answer to and report where CDR got it wrong, using the
  [evidence problem form](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/issues/new?template=evidence_problem.yml).
  "Claim 3 says X, but the cited passage says Y" is exactly what we need.
- Propose a [Case File](docs/case-files.md): a question with a known answer that CDR should
  be able to reproduce.
- Review how we apply PRISMA, RoB 2 or GRADE. If the methodology is off, nothing else matters.

**You like measuring things.** Evaluation is where the project is thinnest. See
[docs/evaluation.md](docs/evaluation.md) and the discovery track in the [roadmap](ROADMAP.md).

## Setup

You need [uv](https://docs.astral.sh/uv/getting-started/installation/), Python 3.12, and Node 20
if you're touching the UI. Or open the repo in a GitHub Codespace, where the devcontainer
does all of this for you.

```bash
git clone https://github.com/<you>/Clinical-Deep-Research_CDR.git
cd Clinical-Deep-Research_CDR
make setup        # installs Python + UI deps, creates .env
make check        # lint + backend tests: exactly what CI runs
```

You don't need an API key to contribute. Tests mock every network call. To run the real
pipeline, see [docs/providers.md](docs/providers.md). A local model through Ollama works and
needs no key.

Optional: `uv run pre-commit install` runs the linters on every commit.

## Finding something to work on

- **Issues labeled [`good first issue`](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/issues?q=is%3Aopen+label%3A%22good+first+issue%22)**
  are scoped, explained, and have a clear definition of done.
- **Loose ends.** `grep -rn "loose end" src eval` lists code that parses or computes something
  and then never uses it: ClinicalTrials.gov phase and enrollment, PubMed study type, an
  observational-design check that is never enforced. Each one is either a small feature waiting
  to be wired up or dead code waiting to be deleted. Figuring out which is the task.
- **[`help wanted`](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/issues?q=is%3Aopen+label%3A%22help+wanted%22)**
  are bigger pieces where an owner would be very welcome.
- **The [vision doc](docs/vision.md#open-problems-pick-one)** lists open research problems.
  Talk to us before starting one of those. They're more design than code.

Comment on an issue to claim it so two people don't do the same work. If you go quiet for two
weeks, it's fair game again. No hard feelings.

## Making a pull request

- **Keep it small.** One idea per PR. Three small PRs get reviewed faster than one big one.
- **Open a draft early** if you want feedback on direction before polishing.
- **`make check` must pass.** CI runs the same thing plus the frontend and E2E jobs.
- **Tests for behavior changes.** Bug fix: a test that fails without your fix. Feature: tests
  for the contract, not for the LLM's wording.
- **Commit messages:** [Conventional Commits](https://www.conventionalcommits.org/) style
  (`fix: ...`, `feat: ...`, `docs: ...`) is appreciated but not policed. PRs are squash-merged,
  so the PR title is what ends up in history.
- **Maintainers may push small fixes to your branch** (a lint nit, a rebase) to save you a round
  trip. Uncheck "Allow edits from maintainers" if you'd rather we didn't.

What to expect from us: a first response within a few days, a straight answer on whether the
change fits, and help finishing it if it's close. If a PR can't be merged, we'll say why.

## The non-negotiables

CDR is only useful if it can be trusted. These rules hold in every PR:

1. **Every claim cites real snippets.** Never add a fallback that fabricates, guesses or
   "fills in" supporting evidence. This is the reason CDR exists
   ([INC-001](docs/incidents.md#inc-001-citation-laundering)).
2. **Don't loosen a gate quietly.** Changing a threshold or bypassing a verification step
   needs its own PR that explains why.
3. **Tests never touch the network.** Mock HTTP and LLM calls. CI enforces this.
4. **Never present illustrative data as real.** If an example is synthetic, label it.
5. **The clinical disclaimer stays on every output.**
6. **Honest negatives are valid results.** `insufficient_evidence` and `unpublishable` are
   the system working, not bugs to be "fixed" by relaxing checks.

## Where things live

```
src/cdr/
├── orchestration/   graph.py (the pipeline) + nodes/ (one module per phase)
├── core/            schemas.py (every data contract), enums.py
├── retrieval/       PubMed, ClinicalTrials.gov, PMC full text, BM25/dense/rerank
├── screening/       inclusion/exclusion
├── extraction/      study cards
├── rob2/            RoB 2 and ROBINS-I
├── synthesis/       evidence claims + GRADE
├── skeptic/         adversarial critique
├── verification/    claim checking and the DoD gates
├── composition/     A + B ⇒ C hypothesis engine
├── publisher/       JSON / Markdown / HTML reports
├── llm/             provider abstraction (one file per provider) + factory
└── api/             FastAPI routes
tests/               pytest, fully offline
eval/                golden set + evaluation runner
ui/                  React + TypeScript frontend
```

Deeper: [docs/architecture.md](docs/architecture.md).

## Common tasks

**Change a pipeline node.** Contract first: update the model in `core/schemas.py`, then the node
in `orchestration/nodes/`, then its entry in `docs/contracts/pipeline_contracts.md`, then tests.
Wiring changes go in `orchestration/graph.py`.

**Add an LLM provider.** See [docs/providers.md](docs/providers.md#adding-a-provider). If it
speaks the OpenAI API, try `OPENAI_BASE_URL` before writing code.

**Add a Case File.** See [docs/case-files.md](docs/case-files.md).

**Add an evaluation metric.** See [docs/evaluation.md](docs/evaluation.md#adding-new-metrics).

**Change the API.** Regenerate the spec, or CI will fail:
`uv run python scripts/export_openapi.py --output docs/openapi.json`

## Testing

```bash
make test                          # all backend tests
make test ARGS="-k prisma"         # filter by name
make test ARGS="tests/test_synthesis.py -x"
make test-ui                       # frontend
uv run pytest tests --cov=src/cdr --cov-report=term-missing
```

Test structure and contracts, not LLM prose. The LLM's wording changes run to run. The shape
of its output, and what the pipeline does with it, shouldn't.

## Writing about clinical content

In docs, prompts and report templates:

- CDR never gives medical advice. Don't write anything that reads like it does.
- Use hedged, accurate language: "the evidence suggests", not "proves".
- Report limitations plainly, especially missing databases and abstract-only assessments.
- Every claim traces to a snippet, and every snippet traces to a source.

## Getting help

- **Questions, ideas, "is this a good idea?":** [Discussions](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/discussions)
- **Bugs and concrete proposals:** [Issues](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/issues/new/choose)
- **Security:** privately, see [SECURITY.md](SECURITY.md)

Everyone participating agrees to the [Code of Conduct](CODE_OF_CONDUCT.md). Short version:
be direct about the work and decent to the people.

## Credit

Every merged contribution is credited in the [changelog](CHANGELOG.md) and release notes by
GitHub handle. That includes code, docs, case files and evidence reports.
