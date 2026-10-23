"""Embedder interface: local-only embedding, no external API (see AGENTS.md).

`Embedder` is a typing.Protocol so fakes plug in without inheritance, exactly like
the LLM provider layer.
"""

from typing import Protocol


class Embedder(Protocol):
    """Everything phase 4+ needs from an embedding model."""

    @property
    def dimensions(self) -> int:
        """Size of every vector this embedder returns."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts in order; one vector per input, same length as `texts`."""
        ...
