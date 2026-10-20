# Architecture Overview

*Owner: Engineering · Last updated: September 2026*

## Services

| Service | Technology | Responsibility |
|---|---|---|
| web-app | React, TypeScript | Customer web application |
| ledger-api | Kotlin, Spring Boot | Core API, approval workflows, payments preparation |
| ingestion-service | Python | Invoice capture, OCR and AI data extraction |
| sync-gateway | Go | Connectors and synchronisation with customer ERPs |
| notifications | Kotlin | Email and in-app notifications |

Services communicate through REST APIs and **Kafka** events.

## Data

- **PostgreSQL 16** primary database with **2 read replicas**.
- Invoice files are stored in object storage, encrypted at rest.
- All customer data is stored **in the EU**.

## Hosting

- Cloud provider: **Nimbus Cloud**.
- Primary region: **eu-south-1 (Milan)**; disaster recovery region: **eu-west-3**.

## Resilience targets

- **Recovery time objective (RTO): 4 hours**
- **Recovery point objective (RPO): 15 minutes**
- Database write-ahead logs are backed up every 15 minutes; daily snapshots are kept for **35 days**.
