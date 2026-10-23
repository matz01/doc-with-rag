"""The real local embedder: sentence-transformers BAAI/bge-m3, 1024 dimensions.

No external API for embeddings (AGENTS.md): the model runs in-process; the first
construction downloads it from Hugging Face and caches it locally.
"""

from sentence_transformers import SentenceTransformer


class BgeM3Embedder:
    """`Embedder` implementation backed by BAAI/bge-m3 running locally.

    Constructing it is the expensive part (model load); keep one instance per process
    and call `embed` as many times as needed.
    """

    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        # Explicit dimensions instead of trusting the model to match the schema: a
        # mismatch would surface here, at startup, rather than corrupting storage.
        self._model = SentenceTransformer(model_name)
        dimensions = self._model.get_embedding_dimension()
        if dimensions != 1024:
            raise ValueError(f"{model_name}: expected 1024 dimensions, found {dimensions}")

    @property
    def dimensions(self) -> int:
        return 1024

    def embed(self, texts: list[str]) -> list[list[float]]:
        # .tolist() keeps psycopg-serializable plain floats, no numpy types crossing
        # the interface (the pgvector adapter handles numpy later, at the storage edge).
        return self._model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        ).tolist()
