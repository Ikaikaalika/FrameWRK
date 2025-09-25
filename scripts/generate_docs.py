#!/usr/bin/env python3
"""Generate synthetic ops runbook documents for bulk ingestion tests.

Usage:
    python scripts/generate_docs.py --output scripts/bulk_docs --count 200

Each document is saved as a Markdown file with metadata headers compatible with
`vectorstore._extract_metadata`, plus a realistic operations narrative so the
RAG pipeline has varied content to rank.
"""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timezone
from pathlib import Path

LOCATIONS = [
    "Salt Lake City Surgery Center",
    "Phoenix Surgery Center",
    "Austin Surgery Center",
    "Denver Surgery Center",
    "Nashville Surgery Center",
]

STAGES = [
    "Pre-Op",
    "Intra-Op",
    "Post-Op",
    "Recovery",
]

RISKS = ["Low", "Moderate", "High"]

TITLES = [
    "Sedation Safety Checklist",
    "Inventory Replenishment SOP",
    "Digital Guide Verification",
    "Emergency Response Protocol",
    "Follow-up Call Script",
    "Sterilization Audit",
    "Lab Coordination Workflow",
    "Medication Reconciliation",
]

SCENARIOS = [
    "Verify IV sedation kit contents, staffing coverage, and patient vitals before induction.",
    "Stage implant kits and backup abutments while logging serial numbers for compliance.",
    "Coordinate with lab to confirm digital guide arrival and reprint contingency plans.",
    "Run pharmacy pickup tracker to ensure antibiotics and pain management meds are in stock.",
    "Document anesthesia event review process and escalation thresholds for the medical director.",
    "Maintain sedation trend dashboards with daily snapshots and risk alerts.",
    "Prep post-op wellness outreach scripts highlighting red-flag symptoms and scheduling steps.",
]

FOLLOW_UPS = [
    "Schedule 24-hour sedation safety check-in and track in CRM.",
    "Escalate low inventory alerts to supply chain coordinator within 2 hours.",
    "Create automation to reconcile lab shipment statuses nightly.",
    "Automate medication refill reminders based on sedation schedule.",
]


def build_document(idx: int) -> str:
    title = random.choice(TITLES)
    location = random.choice(LOCATIONS)
    stage = random.choice(STAGES)
    risk = random.choices(RISKS, weights=[0.4, 0.4, 0.2])[0]
    scenario = random.choice(SCENARIOS)
    follow_up = random.choice(FOLLOW_UPS)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    body = f"""Title: {title} #{idx:04d}
Location: {location}
Procedure Stage: {stage}
Risk Level: {risk}

Scenario Overview
-----------------
{scenario}

Automation Ideas
----------------
- Use sensor telemetry to auto-flag sedation kit gaps before morning huddles.
- Generate checklist variants tailored to {location.split()[0]}'s staffing constraints.
- Trigger inventory reorder tickets when on-hand counts drop below thresholds.

Follow-up Actions
-----------------
- {follow_up}
- Record automation performance metrics weekly (success rate, manual overrides).
- Update analytics dashboard with {risk.lower()}-risk patient markers.

Document generated at {timestamp}.
"""
    return body


def generate_docs(output_dir: Path, count: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(count):
        content = build_document(idx)
        path = output_dir / f"synthetic_ops_{idx:05d}.md"
        path.write_text(content, encoding="utf-8")
    print(f"Generated {count} documents in {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic operations docs for ingestion testing.")
    parser.add_argument("--output", type=Path, default=Path("scripts/bulk_docs"))
    parser.add_argument("--count", type=int, default=100)
    args = parser.parse_args()

    generate_docs(args.output, args.count)


if __name__ == "__main__":
    main()
