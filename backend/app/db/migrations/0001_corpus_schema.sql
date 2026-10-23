-- Corpus schema for documents, chunks and their permissions.
--
-- Permissions live in exactly one place: `documents.allowed_groups`. Every query that
-- returns chunks joins `documents` in the WHERE clause and checks that the document's
-- groups intersect the session user's groups — see AGENTS.md, the filter must live in
-- the SQL search query itself. A per-chunk copy would be a way for a stale insert to
-- grant access, so the schema forbids one.
-- `supersedes` has no foreign key on purpose: the manifest lists the superseding
-- document before the superseded one, and forward references would force deferred
-- constraints everywhere for a relation that is advisory only.

CREATE TABLE documents (
    id text PRIMARY KEY,
    title text NOT NULL,
    department text NOT NULL,
    format text NOT NULL CHECK (format IN ('md', 'pdf', 'docx')),
    allowed_groups text[] NOT NULL CHECK (array_length(allowed_groups, 1) > 0),
    effective_date date NOT NULL,
    status text NOT NULL CHECK (status IN ('current', 'superseded')),
    supersedes text,
    path text NOT NULL,
    content_hash text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE chunks (
    id bigint GENERATED ALWAYS AS identity PRIMARY KEY,
    document_id text NOT NULL REFERENCES documents (id) ON DELETE CASCADE,
    ordinal int NOT NULL,
    text text NOT NULL CHECK (length(text) > 0),
    section text,
    -- bge-m3 produces 1024-dimensional embeddings; the column dimension is pinned so
    -- a wrong model cannot silently write shorter or longer vectors.
    embedding vector(1024) NOT NULL,
    -- Permissions are read from `documents` through a join in the search query's
    -- WHERE clause; a chunk never carries a copy of its own.
    UNIQUE (document_id, ordinal)
);

CREATE INDEX chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);
