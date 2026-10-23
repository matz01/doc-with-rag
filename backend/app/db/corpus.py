"""Corpus persistence: documents and their chunks, with embeddings.

Permission values live on `documents.allowed_groups` only; retrieval joins the
document, so persistence never writes a per-chunk permission copy (see the schema
migration). Transaction ownership: the caller opens/commits the connection, these
functions only run statements inside it.
"""

from dataclasses import dataclass
from datetime import date

import psycopg

from app.ingestion.chunking import ChunkPlan


@dataclass(frozen=True)
class DocumentRecord:
    """A document's indexed form: manifest fields plus the parsed-content hash."""

    id: str
    title: str
    department: str
    format: str
    path: str
    allowed_groups: list[str]
    effective_date: date
    status: str
    supersedes: str | None
    content_hash: str


def upsert_document(conn: psycopg.Connection, record: DocumentRecord) -> None:
    """Insert or update the document row (id is the key); chunks are untouched."""
    conn.execute(
        """
        INSERT INTO documents (id, title, department, format, allowed_groups,
                               effective_date, status, supersedes, path, content_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            department = EXCLUDED.department,
            format = EXCLUDED.format,
            allowed_groups = EXCLUDED.allowed_groups,
            effective_date = EXCLUDED.effective_date,
            status = EXCLUDED.status,
            supersedes = EXCLUDED.supersedes,
            path = EXCLUDED.path,
            content_hash = EXCLUDED.content_hash
        """,
        (
            record.id,
            record.title,
            record.department,
            record.format,
            record.allowed_groups,
            record.effective_date,
            record.status,
            record.supersedes,
            record.path,
            record.content_hash,
        ),
    )


def replace_chunks(
    conn: psycopg.Connection, document_id: str, chunks: list[ChunkPlan], vectors: list[list[float]]
) -> None:
    """Replace ALL of the document's chunks with these, in ordinal order.

    Delete-all-then-insert makes re-ingestion idempotent without diff logic; callers
    build `vectors` with their own embedder — this module does not embed anything.
    """
    if len(chunks) != len(vectors):
        raise ValueError("chunks and vectors must be paired one to one")

    # The insert casts to vector with the textual representation: plain Python floats
    # suffice, no pgvector adapter setup is needed on the write path.
    conn.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
    with conn.cursor() as cursor:
        # executemany is on the cursor in psycopg 3 (the connection API has no shortcut).
        cursor.executemany(
            """
            INSERT INTO chunks (document_id, ordinal, text, section, embedding)
            VALUES (%s, %s, %s, %s, %s::vector)
            """,
            [
                (
                    document_id,
                    ordinal,
                    chunk.text,
                    chunk.section,
                    f"[{', '.join(repr(value) for value in vector)}]",
                )
                for ordinal, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
            ],
        )


def document_hashes(conn: psycopg.Connection) -> dict[str, str]:
    """The stored documents' content hashes keyed by id (the unchanged-skip lookup)."""
    rows = conn.execute("SELECT id, content_hash FROM documents").fetchall()
    return {document_id: content_hash for document_id, content_hash in rows}
