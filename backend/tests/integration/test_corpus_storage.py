"""Integration tests for corpus persistence (`app/db/corpus.py`).

`upsert_document` stores `DocumentRecord` fields in the migrated `documents` table,
`replace_chunks` swaps all of a document's chunks (delete-all-then-insert, so
re-ingestion is idempotent) and `document_hashes` feeds the unchanged-skip. These
tests run against the real dedicated test database and apply the migrations first.

The write path takes plain Python float lists (the SQL casts to ::vector itself, no
pgvector adapter needed); the read path uses the canonical pgvector adapter
(`register_vector`) exactly like `test_migrations.py` does.
"""

from datetime import date

import psycopg
import pytest
from pgvector.psycopg import register_vector

from app.db.corpus import (
    DocumentRecord,
    document_hashes,
    replace_chunks,
    upsert_document,
)
from app.db.migrations import apply_migrations
from app.ingestion.chunking import ChunkPlan

from ._database import _test_database_url, reset_test_database


@pytest.fixture(autouse=True)
def empty_schema():
    reset_test_database()


def _migrated_url() -> str:
    """The test database URL with the corpus schema applied."""
    apply_migrations(_test_database_url())
    return _test_database_url()


def _vector(base: float) -> list[float]:
    """A distinct 1024-dim embedding built only from plain Python floats."""
    return [(base + index * 0.1) % 1.0 for index in range(1024)]


def _record(
    article_id: str = "doc-a",
    content_hash: str = "h1",
    title: str = "Doc A",
) -> DocumentRecord:
    """A sensible corpus record: an engineering markdown document."""
    return DocumentRecord(
        id=article_id,
        title=title,
        department="engineering",
        format="md",
        path="documents/engineering/doc-a.md",
        allowed_groups=["engineers"],
        effective_date=date(2026, 2, 1),
        status="current",
        supersedes=None,
        content_hash=content_hash,
    )


@pytest.mark.integration
def test_upsert_document_persists_all_record_fields_and_reads_them_back():
    """Every field of the record must land in the documents row exactly as given,
    including a non-null created_at the database fills in itself."""
    url = _migrated_url()

    with psycopg.connect(url) as conn:
        upsert_document(conn, _record())
        conn.commit()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM documents WHERE id = 'doc-a'")
            row = cursor.fetchone()

    assert row is not None
    (
        stored_id,
        title,
        department,
        format,
        allowed_groups,
        effective_date,
        status,
        supersedes,
        path,
        content_hash,
        created_at,
    ) = row

    assert stored_id == "doc-a"
    assert title == "Doc A"
    assert department == "engineering"
    assert format == "md"
    assert allowed_groups == ["engineers"]
    assert effective_date == date(2026, 2, 1)
    assert status == "current"
    assert supersedes is None
    assert path == "documents/engineering/doc-a.md"
    assert content_hash == "h1"
    assert created_at is not None


@pytest.mark.integration
def test_upsert_document_updates_instead_of_duplicating_when_the_id_is_already_there():
    """The id is the key: upserting the same id twice must leave exactly one row,
    holding the latest values (otherwise re-ingestion would pile up duplicates)."""
    url = _migrated_url()

    with psycopg.connect(url) as conn:
        upsert_document(conn, _record(content_hash="h1"))
        upsert_document(conn, _record(title="Doc A v2", content_hash="h2"))
        conn.commit()
        with conn.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM documents WHERE id = 'doc-a'")
            count = cursor.fetchone()[0]
            cursor.execute("SELECT title FROM documents WHERE id = 'doc-a'")
            title = cursor.fetchone()[0]
            cursor.execute("SELECT content_hash FROM documents WHERE id = 'doc-a'")
            content_hash = cursor.fetchone()[0]

    assert count == 1
    assert title == "Doc A v2"
    assert content_hash == "h2"


@pytest.mark.integration
def test_replace_chunks_stores_the_document_chunks_with_their_embeddings_in_ordinal_order():
    """Chunks are stored with the embedding vectors the pipeline already computed:
    ordinals 0..n-1 in the given order, texts and sections as given, and every
    stored embedding equal to the vector passed in (plain floats, no register_vector)."""
    url = _migrated_url()
    chunks = [
        ChunkPlan(text="one", section="Intro"),
        ChunkPlan(text="two", section="Details"),
        ChunkPlan(text="three", section=None),
    ]
    vectors = [_vector(0.1), _vector(0.25), _vector(0.5)]

    with psycopg.connect(url) as conn:
        # register_vector is how the app reads embeddings back (canonical adapter);
        # the write path under test still accepts plain float lists on its own.
        register_vector(conn)
        upsert_document(conn, _record())
        replace_chunks(conn, "doc-a", chunks, vectors)
        conn.commit()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT ordinal, text, section FROM chunks"
                " WHERE document_id = 'doc-a' ORDER BY ordinal"
            )
            rows = cursor.fetchall()
            cursor.execute(
                "SELECT embedding FROM chunks WHERE document_id = 'doc-a' ORDER BY ordinal"
            )
            stored_vectors = [row[0].to_list() for row in cursor.fetchall()]

    assert [row[0] for row in rows] == [0, 1, 2]
    assert [row[1] for row in rows] == ["one", "two", "three"]
    assert [row[2] for row in rows] == ["Intro", "Details", None]
    assert len(stored_vectors) == len(vectors)
    for stored, given in zip(stored_vectors, vectors, strict=True):
        assert stored == pytest.approx(given)


@pytest.mark.integration
def test_replace_chunks_drops_the_previous_chunks_when_called_again():
    """Replace means replace: a second call must leave only the new chunks — no
    leftover from the first set — so re-ingesting a document is idempotent."""
    url = _migrated_url()
    first = [
        ChunkPlan(text="old-one", section="A"),
        ChunkPlan(text="old-two", section="A"),
        ChunkPlan(text="old-three", section="B"),
    ]
    second = [
        ChunkPlan(text="new-one", section="A"),
        ChunkPlan(text="new-two", section="A"),
    ]

    with psycopg.connect(url) as conn:
        upsert_document(conn, _record())
        replace_chunks(conn, "doc-a", first, [_vector(0.1)] * len(first))
        replace_chunks(conn, "doc-a", second, [_vector(0.25)] * len(second))
        conn.commit()
        with conn.cursor() as cursor:
            cursor.execute("SELECT text FROM chunks WHERE document_id = 'doc-a' ORDER BY ordinal")
            texts = [row[0] for row in cursor.fetchall()]

    assert texts == ["new-one", "new-two"]


@pytest.mark.integration
def test_chunks_are_removed_with_their_document():
    """Chunks have no life of their own: deleting a document must take its chunks
    with it (ON DELETE CASCADE on chunks.document_id), as permission re-ingestion
    relies on."""
    url = _migrated_url()

    with psycopg.connect(url) as conn:
        upsert_document(conn, _record())
        chunks = [ChunkPlan(text="c0"), ChunkPlan(text="c1")]
        replace_chunks(conn, "doc-a", chunks, [_vector(0.1)] * len(chunks))
        conn.commit()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM documents WHERE id = 'doc-a'")
            cursor.execute("SELECT count(*) FROM chunks WHERE document_id = 'doc-a'")
            count = cursor.fetchone()[0]

    assert count == 0


@pytest.mark.integration
def test_document_hashes_maps_the_stored_content_hash_by_id():
    """The unchanged-skip needs a hash per document id: two documents with
    different ids and hashes map one to one."""
    url = _migrated_url()

    with psycopg.connect(url) as conn:
        upsert_document(conn, _record(article_id="doc-a", content_hash="h1"))
        upsert_document(conn, _record(article_id="other-b", content_hash="h2"))
        conn.commit()
        hashes = document_hashes(conn)

    assert hashes == {"doc-a": "h1", "other-b": "h2"}
