"""Integration tests for the local bge-m3 embedder.

Embeddings run locally with the ``BAAI/bge-m3`` sentence-transformers model:
no external API is involved. The model is downloaded from Hugging Face on the
first run of this test, which is why the tests are marked ``slow``; later runs
load it from the local cache. The vector size pinned here must match the
``vector(1024)`` column in the database schema.
"""

import pytest

from app.embeddings.bge import BgeM3Embedder

pytestmark = [pytest.mark.integration, pytest.mark.slow]

# The documented output dimensionality of BAAI/bge-m3, pinned by the schema.
DIMENSIONS = 1024


def test_embeds_texts_with_the_documented_1024_dimensions():
    embedder = BgeM3Embedder()

    vectors = embedder.embed(["first tiny sentence", "a different sentence"])

    assert len(vectors) == 2
    assert all(len(vector) == DIMENSIONS for vector in vectors)
    assert embedder.dimensions == DIMENSIONS


def test_is_stable_for_the_same_text():
    embedder = BgeM3Embedder()

    first = embedder.embed(["first tiny sentence"])
    second = embedder.embed(["first tiny sentence"])

    assert first[0] == second[0]
