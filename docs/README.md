# CDR documentation

Pick the page that matches the question you have.

**What is this and why?**
- [vision.md](vision.md): where CDR is going, and why the evidence engine comes first
- [glossary.md](glossary.md): every acronym in this repo, in plain language

**How does it work?**
- [architecture.md](architecture.md): the 13-node pipeline, the state object, stage contracts
- [contracts/pipeline_contracts.md](contracts/pipeline_contracts.md): per-node input/output spec
- [case-study.md](case-study.md): design decisions and trade-offs
- [openapi.json](openapi.json): the HTTP API (also live at `/docs` when the server runs)

**Why is it so strict?**
- [incidents.md](incidents.md): postmortems of real failures (citation laundering and friends)
- [history/hardening-log.md](history/hardening-log.md): the four review rounds before release

**How good is it?**
- [evaluation.md](evaluation.md): metrics, golden set, how to run the evaluation
- [case-files.md](case-files.md): known-answer clinical questions CDR must get right
- [online-run-notes.md](online-run-notes.md): how the bundled real runs were made

**How do I use it?**
- [providers.md](providers.md): LLM keys, free tiers, local models
- [report-anatomy.md](report-anatomy.md): how to read and audit a report

Something missing or wrong? That's a docs bug.
[Open an issue](https://github.com/BlueRingsLabs/Clinical-Deep-Research_CDR/issues/new?template=docs.yml).
