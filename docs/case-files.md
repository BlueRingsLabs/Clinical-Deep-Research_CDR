# Case Files

A Case File is a clinical question where **we already know what a careful expert would
conclude**, written down so CDR can be checked against it. They're CDR's test bench, and adding
one is the most direct way to make the engine better, whether or not you write code.

They live in [`eval/cases/`](../eval/cases/), one JSON file per case.

## Three kinds of case

| Type | What it tests | Example |
|---|---|---|
| **settled** | Can CDR reproduce a well-established answer, with the right caveats? | Aspirin after a heart attack ([CF-0001](../eval/cases/CF-0001-aspirin-secondary-prevention.json)) |
| **uncertain** | Does CDR stay honest when the evidence is mixed, instead of forcing a yes or no? | Vitamin D and respiratory infections ([CF-0002](../eval/cases/CF-0002-vitamin-d-respiratory-infections.json)) |
| **retrodiction** | Given only the literature that existed *before* a discovery, does CDR propose it? | Swanson's fish oil → Raynaud's, 1986 ([CF-0003](../eval/cases/CF-0003-fish-oil-raynaud-retrodiction.json)) |

Settled and uncertain cases test the evidence engine. Retrodiction cases test the discovery
engine, and they're the benchmark the [vision](vision.md) is aiming at. Today CDR can't enforce
a literature cutoff, so retrodiction cases are targets, not yet runnable tests. Building that
is on the [roadmap](../ROADMAP.md).

The first case already bites. On CF-0001 (aspirin after a heart attack), a real run on a free 8B
model rated every claim *low* certainty, when the established answer is high. That's the point:
a Case File turns "the output feels off" into a specific, fixable failure.

## What makes a good case

- **The answer has a source you can point to.** A Cochrane review, a major guideline, a
  landmark trial or meta-analysis, or, for retrodiction, the paper that made the connection and
  the study that confirmed it. "Everyone knows" is not a source.
- **The answer includes its caveats.** "Reduces events but increases bleeding" is a known answer.
  "Works" is not.
- **It has a trap.** The most useful cases are ones a naive system gets wrong: mixing
  populations, ignoring dosing, overstating a subgroup, using literature from after the cutoff.
- **It's narrow enough to check.** One PICO, one clear conclusion.

## Adding one

1. Copy an existing file in `eval/cases/` and name it `CF-XXXX-short-slug.json` with the next
   free number.
2. Fill it in. The schema is [`schemas/case_file.schema.json`](../schemas/case_file.schema.json).
   Required fields:
   - `id`, `title`, `case_type` (`settled` | `uncertain` | `retrodiction`)
   - `question` and the PICO fields: `population`, `intervention`, `comparator` (may be `null`), `outcome`
   - `expected_evidence_level` (`high` | `moderate` | `low` | `very_low`), `expected_min_studies`
   - `composition_expected`: `true` if answering needs an A + B ⇒ C connection
   - `known_answer`: plain language, with caveats
   - `references`: full citations. Add PMID/DOI only if you've checked it.
   - Retrodiction also needs `expected_hypothesis` and `literature_cutoff_year`.
3. Run `make test ARGS="tests/test_case_files.py"`. It validates every case.
4. Open a PR. A reviewer with clinical background checks the known answer and the sources.

Not comfortable with JSON? Use the
[Case File issue form](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/issues/new?template=case_file.yml)
and someone will turn it into a file.

## Running them

```bash
make eval-cases     # offline structural check of every case
uv run python -m eval.eval_runner --dataset eval/cases/ --mode online   # real pipeline, needs a key
```

Scoring against `known_answer` is still manual: read the report and compare. Automating that
judgment reliably is itself an open problem, and a good one to pick up.
