-- Enable pgvector once, at database creation.
CREATE EXTENSION IF NOT EXISTS vector;

-- Dedicated database for the integration tests (TEST_DATABASE_URL): from phase 3 on
-- they insert and delete documents, so they must not touch the data the API serves.
-- Note: this file runs only when the data volume is empty; existing volumes get the
-- database created by the integration test fixture (tests/integration/_database.py).
CREATE DATABASE docrag_test;

\connect docrag_test
CREATE EXTENSION IF NOT EXISTS vector;
