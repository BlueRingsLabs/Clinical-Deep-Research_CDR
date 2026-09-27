# Examples

| File | Needs keys? | What it does |
|---|---|---|
| `inspect_report.py` | No | Prints a readable summary of any CDR report JSON |
| `evaluate.py` | No | Shows the golden set and the evaluation thresholds |
| `run_query.py` | Yes (one LLM key) | Runs a real question through the full pipeline |

```bash
uv run python examples/inspect_report.py
uv run python examples/inspect_report.py --report examples/output/online/run_01/cdr_report_run_01.json
```

## About `output/`

- **`output/sample_report.json` / `.md` are illustrative.** They were written by hand to show
  every field of the report format. The PMIDs are placeholders, not real papers. Don't cite them.
- **`output/online/run_*` are real runs**, unedited: real PubMed/CT.gov retrieval, real LLM
  calls on free-tier 8B models. [docs/online-run-notes.md](../docs/online-run-notes.md)
  describes each one.
