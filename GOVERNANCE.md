# Governance

CDR is small, so the governance is small. This page exists so nobody has to guess.

## Who decides

**Gonzalo Romero ([@glromero](https://github.com/glromero))** started the project and is
currently its lead maintainer. He has the final say on scope, architecture and releases.

In practice, most decisions happen in issues and pull requests, in the open, and the best
argument usually wins. "Here's the evidence and here's the mechanism" beats "I think".

## Becoming a maintainer

There's no application form. People who make several solid contributions, review others' work
thoughtfully, and show good judgment about the non-negotiables in
[CONTRIBUTING.md](CONTRIBUTING.md) get invited to become maintainers of an area (retrieval,
methodology, UI, evaluation...). Maintainers get merge rights for their area and a line in
`.github/CODEOWNERS`.

Clinical methodology counts as much as code. A methodologist who keeps CDR's use of RoB 2
honest is as much a maintainer as someone who owns the retrieval layer.

## What needs more than one person

- Changes that loosen an evidence gate or a verification threshold
- Changes to the report schema (`schemas/report.schema.json`), since people build on it
- Adding a new data source that has licensing implications

These need an issue with the reasoning, and a maintainer other than the author to approve.

## Changing this document

Open a PR. As the contributor base grows, this should grow with it.
