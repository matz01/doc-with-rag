# Incident Response Runbook

*Owner: Engineering*

## Severity levels

| Severity | Definition | Acknowledge within | Status updates |
|---|---|---|---|
| **SEV1** | Full outage, or a data integrity risk affecting multiple customers | **15 minutes** | every 30 minutes |
| **SEV2** | A major feature is degraded for many customers | **30 minutes** | every hour |
| **SEV3** | Minor issue, or a single customer affected | next business day | as needed |

## Roles

- The **on-call engineer** is the incident commander until they hand over to the Engineering Manager on duty.
- For **SEV1**, notify the **CTO** and the **Head of Customer Success** immediately.

## Communication

- Open an incident channel named `#inc-YYYYMMDD-short-name`.
- For SEV1 and SEV2, update the public status page **status.ledgerline.example** within **30 minutes** of acknowledging the incident.

## After the incident

- SEV1 and SEV2 incidents require a **blameless postmortem within 5 business days**.
- Postmortems list the timeline, root cause, impact and action items with owners and due dates.
