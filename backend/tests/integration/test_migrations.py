"""Integration tests for the schema migrations (`app/db/migrations.py`).

Schema changes are plain SQL files in `app/db/migrations/`, applied in order. These
tests run against the real dedicated test database, because a migration runner's whole
job is talking to a real database.
"""

import psycopg
import pytest
from pgvector.psycopg import register_vector

from app.db.migrations import apply_migrations

from ._database import _test_database_url, reset_test_database


@pytest.fixture(autouse=True)
def empty_schema():
    reset_test_database()


@pytest.mark.integration
def test_apply_migrations_creates_the_corpus_tables():
    """Applying the migrations on a fresh database must create the documents and
    chunks tables all data and permissions will live in."""
    apply_migrations(_test_database_url())

    with psycopg.connect(_test_database_url()) as conn, conn.cursor() as cursor:
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
        table_names = {row[0] for row in cursor.fetchall()}

    assert {"documents", "chunks", "schema_migrations"} <= table_names


@pytest.mark.integration
def test_apply_migrations_records_the_applied_files():
    """Every applied file must be tracked, so a later run can skip it."""
    apply_migrations(_test_database_url())

    with psycopg.connect(_test_database_url()) as conn, conn.cursor() as cursor:
        cursor.execute("SELECT filename FROM schema_migrations ORDER BY filename")
        tracked = [row[0] for row in cursor.fetchall()]

    assert tracked == ["0001_corpus_schema.sql"]


@pytest.mark.integration
def test_apply_migrations_can_run_again_on_an_already_migrated_database():
    """A second run must skip the already applied files without failing: the
    application applies migrations at startup, and startup runs every time."""
    apply_migrations(_test_database_url())
    apply_migrations(_test_database_url())

    with psycopg.connect(_test_database_url()) as conn, conn.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM schema_migrations")
        count = cursor.fetchone()[0]

    assert count == 1


@pytest.mark.integration
def test_a_chunk_can_store_and_roundtrip_a_1024_dimensional_embedding():
    """The pinned vector dimension must accept what bge-m3 produces: insert a chunk
    with a 1024-dim embedding, read it back, and check the values survive (this also
    pins the column dimension to 1024 and nothing else). A chunk carries no
    permissions of its own."""
    apply_migrations(_test_database_url())

    marker = "[{value}]".format(value=", ".join(str(i % 10) for i in range(1, 1025)))
    # register_vector is how the app will read and write embeddings: the canonical type
    # adapter (pgvector.psycopg), registered right after connect so cursors pick it up.
    with psycopg.connect(_test_database_url()) as conn:
        register_vector(conn)
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO documents (id, title, department, format, allowed_groups,
                                       effective_date, status, supersedes, path, content_hash)
                VALUES ('doc-1', 'Doc One', 'engineering', 'md', ARRAY['engineers'],
                        '2026-01-01', 'current', NULL, 'documents/doc-1.md', 'hash-1')
                """
            )
            cursor.execute(
                """
                INSERT INTO chunks (document_id, ordinal, text, embedding)
                VALUES ('doc-1', 0, 'some text', %s::vector)
                """,
                (marker,),
            )
            cursor.execute("SELECT embedding FROM chunks WHERE document_id = 'doc-1'")
            embedding = cursor.fetchone()[0].to_list()

    assert len(embedding) == 1024
    # ordinals repeat the pattern 1..9,0: the first value is 1, the tenth is 0.
    assert embedding[0] == pytest.approx(1)
    assert embedding[9] == pytest.approx(0)
    assert embedding[1023] == pytest.approx(1024 % 10)


@pytest.mark.integration
def test_chunks_do_not_carry_permissions_of_their_own():
    """Permissions have a single source of truth (documents): a chunk inherits them
    from its document through the join in the search query, so a diverging or stale
    per-chunk copy could not even be stored."""
    apply_migrations(_test_database_url())

    with psycopg.connect(_test_database_url()) as conn, conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name, column_name FROM information_schema.columns
            WHERE table_name IN ('chunks', 'documents')
              AND column_name = 'allowed_groups'
            """
        )
        column_pairs = set(cursor.fetchall())

    assert ("documents", "allowed_groups") in column_pairs
    assert ("chunks", "allowed_groups") not in column_pairs
