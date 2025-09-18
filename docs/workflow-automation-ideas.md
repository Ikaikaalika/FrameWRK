# Suggested Workflow Automations (Derived from Mock Medical Docs)

Using the new pre-op, sedation, and post-op documents, the platform can automate several high-impact workflows to support Nuvia Smiles operations.

## 1. Pre-Op Readiness Gate
- **Trigger**: New surgery added to Ops Command schedule.
- **Automation**: Parse `pre_op_protocol.md` checkpoints and auto-create task list (identity verification, guide readiness, consent collection) with due times relative to procedure start.
- **Outcome**: Dashboard surfaces "readiness score" and prevents case from hitting "Ready" status until all tasks are checked off.

## 2. Sedation Safety Monitor
- **Trigger**: JSON sedation log uploaded (`sedation_event_log.json`).
- **Automation**:
  - Extract vitals and events; if SpO2 < 94% or notes contain keywords ("drop", "desat"), raise an amber alert in Ops Command.
  - Auto-schedule 24-hour safety call with patient and inject reminder into checklist.
- **Outcome**: Real-time alerting for anesthesia leads and automated adherence to follow-up policies.

## 3. Recovery Room Discharge Bot
- **Trigger**: Post-op recovery note ingested (`post_op_recovery.txt`).
- **Automation**:
  - Generate patient-facing discharge summary (diet, hygiene, activity limitations) and send via SMS/email.
  - Auto-create follow-up call tasks at 48 hours and 1 week, assign to concierge team.
  - Log medication administration times for regulatory compliance.
- **Outcome**: Consistent patient education, proactive follow-up scheduling, improved documentation.

## 4. Inventory Forecast Alerts
- **Trigger**: Pre-op doc references critical supplies (implant kits, titanium bars).
- **Automation**:
  - Cross-check against inventory levels; if on-hand < par (from ops dashboard data), open supply restock task.
- **Outcome**: Prevents day-of-surgery surprises; ties knowledge base to stock management.

## 5. Multichannel Communication Nudges
- **Trigger**: Pre-op communication checklist lines mentioning SMS, pharmacy, or caregiver notifications.
- **Automation**:
  - Generate templated messages for patient/caregiver (arrival, fasting reminders).
  - Notify pharmacy automatically with procedure details and prescriptions.
- **Outcome**: Reduces manual outreach load on coordinators and ensures consistent messaging.

## Integration Notes
- Use existing `/upload` ingestion to capture docs; a background worker can parse payloads and emit events.
- Attach metadata (location, procedure, patient ID) at ingestion to target tasks to the right team in Ops Command.
- Extend `/ops/checklist` endpoint to incorporate automated items; provide toggles in UI for human approval before publishing tasks.

Implementing these automations demonstrates how the platform turns unstructured SOPs into trackable, actionable workflows that keep surgical centers compliant and on schedule.
