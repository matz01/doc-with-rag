"""Fake embedder for unit tests and evaluation runs: no database, no model download."""

from hashlib import md5


class FakeEmbedder:
    """Deterministic hash-based embedder: fixed dimensions, stable across runs.

    Hashing the text keeps retrieval-like behaviour meaningful (equal texts produce
    equal vectors, different texts usually differ) while staying fully offline.
    """

    def __init__(self, dimensions: int = 8) -> None:
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        # md5 is fine here: only determinism matters, not cryptographic strength.
        digests = [md5(text.encode("utf-8"), usedforsecurity=False).digest() for text in texts]
        return [
            [digest[index % len(digest)] / 255.0 for index in range(self._dimensions)]
            for digest in digests
        ]
