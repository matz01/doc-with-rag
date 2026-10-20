# Postmortem — Invoice Sync Outage, 14 August 2026

*Owner: Engineering · Severity: SEV1 · Status: closed*

## Summary

On **14 August 2026**, invoice synchronisation between Ledgerline and customer ERPs failed for **2 hours and 47 minutes** (09:12–11:59 CEST). **312 customers** were affected, including Kestrel Health Partners. No data was lost; all queued invoices were synchronised after recovery.

## Root cause

The **TLS certificate of the sync-gateway expired**. The certificate was renewed manually, and the expiry alert was routed to a decommissioned mailbox, so nobody received it.

## Timeline (CEST)

| Time | Event |
|---|---|
| 09:12 | Sync failures start; first automated alert fires |
| 09:31 | On-call engineer acknowledges the page (**19 minutes** after the alert) |
| 09:48 | Status page updated; incident declared SEV1 |
| 10:40 | Root cause identified |
| 11:45 | New certificate deployed |
| 11:59 | Sync fully recovered; backlog processing begins |

## What went well

- Queued invoices were preserved and no data was lost.
- Customer Success contacted the 20 largest affected customers directly.

## What went wrong

- The acknowledgement took 19 minutes, above the SEV1 target.
- Certificate renewal was manual and not monitored.

## Action items

| Action | Owner | Due | Status |
|---|---|---|---|
| Automate certificate renewal for all services | David Lindqvist | 15 Sep 2026 | Done |
| Alert 30 days before any certificate expires, routed to on-call | Elena Rossi | 30 Sep 2026 | Done |
| Add certificate checks to the incident runbook | Elena Rossi | 31 Oct 2026 | In progress |
