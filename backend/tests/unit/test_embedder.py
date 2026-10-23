"""Contract tests for the FakeEmbedder: deterministic, offline, no real model."""

from app.embeddings.fake import FakeEmbedder


def test_returns_one_vector_per_text_in_input_order() -> None:
    """One vector per input text, keeping the input order."""
    embedder = FakeEmbedder()

    vectors = embedder.embed(["alpha", "beta"])

    assert len(vectors) == 2
    assert len(embedder.embed(["alpha", "beta"])) == 2


def test_vectors_are_length_dimensions() -> None:
    """Every returned vector has exactly `dimensions` entries in [0.0, 1.0]."""
    embedder_8 = FakeEmbedder(dimensions=8)
    embedder_16 = FakeEmbedder(dimensions=16)

    vectors_8 = embedder_8.embed(["alpha", "beta"])
    vectors_16 = embedder_16.embed(["alpha", "beta"])

    assert all(len(vector) == 8 for vector in vectors_8)
    assert all(0.0 <= value <= 1.0 for vector in vectors_8 for value in vector)
    assert all(len(vector) == 16 for vector in vectors_16)
    assert all(0.0 <= value <= 1.0 for vector in vectors_16 for value in vector)


def test_equal_texts_produce_equal_vectors_and_repeated_calls_are_stable() -> None:
    """Repeated calls with the same text return value-equal vectors."""
    embedder = FakeEmbedder()

    first = embedder.embed(["doc text"])
    second = embedder.embed(["doc text"])

    assert first == second


def test_different_texts_produce_different_vectors() -> None:
    """Different texts must not produce identical vectors."""
    embedder = FakeEmbedder()

    vectors = embedder.embed(["a policy statement", "a different statement"])

    assert vectors[0] != vectors[1]


def test_default_dimensions_is_8() -> None:
    """The constructor default for `dimensions` is 8."""
    embedder = FakeEmbedder()

    assert embedder.dimensions == 8
