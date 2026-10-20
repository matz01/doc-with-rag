# Engineering Onboarding

*Owner: Engineering*

## Your first week

- Set up your laptop following the "dev-setup" guide in the `infra` repository. All services run locally in **devcontainers**.
- Request access to GitHub, the cloud console (read-only) and the observability stack through **Deskline**.
- You will be assigned an **onboarding buddy** from your team.

## Main repositories

| Repository | Language | Purpose |
|---|---|---|
| `web-app` | TypeScript, React | Customer-facing web application |
| `ledger-api` | Kotlin | Core API and business logic |
| `ingestion-service` | Python | Invoice capture, OCR and data extraction |
| `sync-gateway` | Go | ERP connectors and synchronisation |
| `infra` | Terraform | Cloud infrastructure |

## Milestones

- **First pull request** merged within your first 2 weeks.
- **On-call:** you join the on-call rotation **after 3 months**, starting with **2 shadow shifts** alongside an experienced engineer.
- **Production access:** granted after **6 months** and after completing the security training.

## Ways of working

- Every change needs at least one approving review; changes to `ledger-api` payment logic need two.
- Releases follow the Release Process. Incidents follow the Incident Response Runbook.
