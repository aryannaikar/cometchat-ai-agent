from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """Creates semantic embeddings using Sentence Transformers."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.model = SentenceTransformer(model_name)

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
        )

        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            return []

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()