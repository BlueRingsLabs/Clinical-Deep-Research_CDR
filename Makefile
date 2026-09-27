# CDR — Clinical Deep Research
# Run `make` with no arguments to see what's here.

.PHONY: help setup check-env check test test-ui test-all lint format typecheck \
        eval eval-cases demo demo-online figures dev run server docker-up docker-down clean

SHELL := /bin/bash
UV    ?= uv
RUN   := $(UV) run

help:
	@echo ""
	@echo "CDR — Clinical Deep Research"
	@echo ""
	@echo "  Getting started"
	@echo "    make setup        Install everything (Python via uv, UI via npm)"
	@echo "    make check-env    Tell me what's missing in .env"
	@echo "    make demo         Offline demo, no API keys needed"
	@echo ""
	@echo "  Before you open a PR"
	@echo "    make check        Lint + backend tests (same as CI)"
	@echo ""
	@echo "  Testing & quality"
	@echo "    make test         Backend tests (pytest). Pass ARGS='-k foo' to filter"
	@echo "    make test-ui      Frontend tests (vitest)"
	@echo "    make test-all     Both"
	@echo "    make lint         Ruff lint + format check"
	@echo "    make format       Auto-fix lint + format"
	@echo "    make typecheck    mypy (advisory, not clean yet)"
	@echo ""
	@echo "  Running"
	@echo "    make dev          API with autoreload  → http://localhost:8000/docs"
	@echo "    make run          API without reload"
	@echo "    make docker-up    API + UI in Docker   → http://localhost:5173"
	@echo "    make demo-online  Real pipeline on the golden set (needs keys, slow)"
	@echo ""
	@echo "  Evaluation"
	@echo "    make eval         Offline structural evaluation on the golden set"
	@echo "    make eval-cases   Same, on the Case Files (eval/cases/)"
	@echo "    make figures      Regenerate evaluation charts"
	@echo ""

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup:
	@command -v $(UV) >/dev/null 2>&1 || { \
		echo "uv not found. Install it: https://docs.astral.sh/uv/getting-started/installation/"; \
		exit 1; }
	$(UV) sync --frozen
	@if command -v npm >/dev/null 2>&1; then cd ui && npm ci --silent; \
	else echo "npm not found — skipping UI deps (only needed for frontend work)"; fi
	@[ -f .env ] || { cp .env.example .env; echo "Created .env from .env.example"; }
	@echo ""
	@echo "Done. Next: add one LLM key to .env, or just run 'make demo'."

check-env:
	@[ -f .env ] || { echo "No .env yet. Run: cp .env.example .env"; exit 1; }
	@if grep -Eq '^(GEMINI_API_KEY|GOOGLE_API_KEY|GROQ_API_KEY|CEREBRAS_API_KEY|OPENROUTER_API_KEY|CLOUDFLARE_API_KEY|HF_TOKEN|OPENAI_API_KEY|OPENAI_BASE_URL|ANTHROPIC_API_KEY)=.+' .env; then \
		echo "LLM provider key: found"; \
	else \
		echo "LLM provider key: MISSING — set at least one in .env (see .env.example)"; exit 1; \
	fi
	@grep -Eq '^NCBI_EMAIL=.+@' .env && ! grep -q '^NCBI_EMAIL=you@example.com' .env \
		&& echo "NCBI_EMAIL: set" \
		|| echo "NCBI_EMAIL: still the placeholder — PubMed asks for a real contact email"

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------

check: lint test

test:
	$(RUN) pytest tests/ $(ARGS)

test-ui:
	cd ui && npm test -- --run

test-all: test test-ui

lint:
	$(RUN) ruff check src tests eval scripts examples
	$(RUN) ruff format --check src tests eval scripts examples

format:
	$(RUN) ruff check --fix src tests eval scripts examples
	$(RUN) ruff format src tests eval scripts examples

typecheck:
	$(RUN) mypy src/cdr

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

dev:
	$(RUN) uvicorn cdr.api.routes:app --host 127.0.0.1 --port 8000 --reload

run: check-env
	$(RUN) uvicorn cdr.api.routes:app --host 0.0.0.0 --port 8000

server: run

docker-up:
	docker compose up --build -d
	@echo "API: http://localhost:8000/docs   UI: http://localhost:5173"

docker-down:
	docker compose down

# ---------------------------------------------------------------------------
# Demo & evaluation
# ---------------------------------------------------------------------------

demo:
	$(RUN) python scripts/generate_demo.py

demo-online: check-env
	$(RUN) python scripts/run_online_demo.py

eval:
	$(RUN) python -m eval.eval_runner \
		--dataset eval/datasets/golden_set_toy.json \
		--output eval/results/

eval-cases:
	$(RUN) python -m eval.eval_runner --dataset eval/cases/ --output eval/results/

figures:
	$(RUN) python scripts/generate_figures.py

# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------

clean:
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage test_reports reports
	@echo "Clean."
