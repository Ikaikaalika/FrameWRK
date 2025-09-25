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

FACILITIES = [
    "SLC Implant Center",
    "Phoenix Surgical Arts",
    "Austin Regenerative Implant Clinic",
    "Denver Full Arch Institute",
]

PROCEDURES = [
    "Full-Arch Immediate Load",
    "Single Implant Placement",
    "Sinus Lift + Graft",
    "All-on-4 Conversion",
]

DOCUMENT_TYPES = [
    "Pre-Operative Assessment",
    "Sedation Consent",
    "Anesthesia Record",
    "Post-Operative Discharge",
    "Medication Reconciliation",
    "Follow-up Outreach Log",
]

CLINICIANS = [
    "Dr. Leah Chen",
    "Dr. Marcus Reed",
    "Dr. Priya Desai",
    "Dr. James Holloway",
]

ANESTHESIA_NOTES = [
    "Patient maintained stable vitals through induction; BIS between 55-60."
    " Prophylactic ondansetron administered pre-induction.",
    "Airway secured with nasal intubation; minimal bleeding; suction every 5 minutes.",
    "Documented ASA II with mild hypertension; lab results attached in chart."
]

POST_OP_INSTRUCTIONS = [
    "Prescribe amoxicillin 500mg TID for 7 days; call if allergic reaction occurs.",
    "Issue liquid diet plan for 48 hours; no smoking or using straws." 
    " Provide detailed saline rinse schedule.",
    "Schedule follow-up CBCT at 48 hours; monitor swelling via patient-submitted photos.",
]

FOLLOW_UP_AUTOMATIONS = [
    "Automate text reminders for medication adherence with secure confirmation capture.",
    "Generate nursing task if pain score > 6 reported via patient app check-in.",
    "Sync sedation event logs to analytics dashboard for daily anesthesia review.",
    "Auto-create labs follow-up checklist to ensure biopsy results delivered within 72 hours.",
]


def build_document(idx: int) -> str:
    facility = random.choice(FACILITIES)
    procedure = random.choice(PROCEDURES)
    doc_type = random.choice(DOCUMENT_TYPES)
    clinician = random.choice(CLINICIANS)
    anesthesia_note = random.choice(ANESTHESIA_NOTES)
    discharge_note = random.choice(POST_OP_INSTRUCTIONS)
    automation = random.choice(FOLLOW_UP_AUTOMATIONS)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    body = f"""Title: {doc_type} — Case {idx:04d}
Facility: {facility}
Procedure: {procedure}
Attending Clinician: {clinician}

Patient Intake Details
----------------------
- Allergies: None reported
- ASA Classification: II
- Pre-op BP: 132/84 mmHg
- Last meal > 8 hours ago

Intraoperative Summary
----------------------
- Anesthesia Notes: {anesthesia_note}
- Implant batch number recorded in sterilization log.
- Chairside assistant completed instrument counts (see attached checklist).
- Labs dispatched for provisional fabrication at 09:45.

Discharge & Follow-up Plan
--------------------------
- {discharge_note}
- Provide emergency on-call number and sedation safety triage guide.
- Document pain score via patient app at 12h/24h intervals.

Automation Opportunities
------------------------
- {automation}
- Flag charts missing signed sedation consent before case closeout.
- Auto-upload anesthesia flowsheet snapshots to compliance archive.

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
