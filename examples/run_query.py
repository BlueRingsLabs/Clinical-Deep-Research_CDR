#!/usr/bin/env python3
"""
Example: Run CDR from Python

Demonstrates how to use CDR programmatically to run a clinical
research query and inspect the results.

Requirements:
    make setup
    cp .env.example .env  # add at least one LLM provider key

Usage:
    python examples/run_query.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


async def main():
    """Run a sample clinical research query."""

    # Lazy import — only import after path is set up
    try:
        from cdr.llm.factory import create_provider_with_fallback
        from cdr.orchestration.graph import CDRRunner
    except ImportError:
        print("❌  CDR not installed. Run: make setup")
        sys.exit(1)

    # Define a clinical question
    question = "Is aspirin effective for secondary prevention of cardiovascular events in adults?"

    print("🔬  Running CDR query:")
    print(f"    {question}")
    print()

    # Run the pipeline
    try:
        provider = create_provider_with_fallback()
        runner = CDRRunner(llm_provider=provider, output_dir="reports", dod_level=1)
        state = await runner.run(research_question=question, max_results=20)
    except Exception as e:
        print(f"❌  Pipeline error: {e}")
        print()
        print("Common fixes:")
        print("  - Check .env has at least one LLM provider key (see .env.example)")
        print("  - Check .env has NCBI_EMAIL set")
        print("  - Verify network connectivity")
        sys.exit(1)

    report = state.report or {}

    print("✅  Pipeline complete!")
    print(f"    Status: {report.get('status', 'unknown')}")
    print(f"    Studies found: {report.get('study_count', 0)}")
    print(f"    Claims generated: {report.get('claim_count', 0)}")
    print(f"    Snippets extracted: {report.get('snippet_count', 0)}")
    print()

    # Show claims
    claims = report.get("claims", [])
    if claims:
        print(f"📋  Evidence Claims ({len(claims)}):")
        for i, claim in enumerate(claims, 1):
            certainty = claim.get("certainty", "?")
            text = claim.get("claim_text", "")[:120]
            snippets = len(claim.get("supporting_snippet_ids", []))
            print(f"    {i}. [{certainty.upper()}] {text}...")
            print(f"       Supported by {snippets} snippet(s)")
        print()

    # Show PRISMA counts
    prisma = report.get("prisma_counts", {})
    if prisma:
        print("📊  PRISMA Flow:")
        print(f"    Identified: {prisma.get('records_identified', 0)}")
        print(f"    Screened:   {prisma.get('records_screened', 0)}")
        print(f"    Included:   {prisma.get('studies_included', 0)}")
        print()

    # Save report
    output_path = Path("reports/run_query_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"💾  Report saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
