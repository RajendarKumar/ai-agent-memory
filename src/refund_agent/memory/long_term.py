from collections.abc import Sequence
from typing import Any
from uuid import uuid4

from fastembed import TextEmbedding
from pymilvus import MilvusClient


class MilvusMemory:
    """Vector search over cross-session, anonymized memory records."""

    def __init__(
        self,
        uri: str,
        token: str | None,
        collection: str,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.client = MilvusClient(uri=uri, token=token)
        self.collection = collection
        self.embedder = TextEmbedding(model_name=embedding_model)
        self.dimension = len(next(self.embedder.embed(["dimension probe"])))
        if not self.client.has_collection(collection_name=collection):
            self.client.create_collection(
                collection_name=collection,
                dimension=self.dimension,
                metric_type="COSINE",
                enable_dynamic_field=True,
            )

    def add(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        vector = list(next(self.embedder.embed([text])))
        self.client.insert(
            collection_name=self.collection,
            data={
                "id": uuid4().int & ((1 << 63) - 1),
                "vector": vector,
                "text": text,
                "metadata": metadata or {},
            },
        )

    def search(self, query: str, limit: int = 3) -> list[str]:
        vector = list(next(self.embedder.embed([query])))
        results = self.client.search(
            collection_name=self.collection,
            data=[vector],
            limit=limit,
            output_fields=["text"],
        )
        return [
            hit["entity"]["text"]
            for group in results
            for hit in group
            if hit.get("entity", {}).get("text")
        ]

    def close(self) -> None:
        self.client.close()