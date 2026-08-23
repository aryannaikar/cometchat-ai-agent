from dataclasses import dataclass

from app.rag.document_loader import Document


@dataclass(frozen=True)
class Chunk:
    """A retrievable piece of a knowledge-base document."""

    chunk_id: str
    document_id: str
    content: str
    metadata: dict


class DocumentChunker:
    """Splits documents into overlapping text chunks."""

    def __init__(self, chunk_size: int = 800, overlap: int = 120):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if overlap < 0:
            raise ValueError("overlap cannot be negative")

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, document: Document) -> list[Chunk]:
        text = document.content.strip()

        if not text:
            return []

        chunks: list[Chunk] = []
        start = 0
        chunk_number = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    Chunk(
                        chunk_id=f"{document.document_id}-chunk-{chunk_number}",
                        document_id=document.document_id,
                        content=chunk_text,
                        metadata={
                            **document.metadata,
                            "chunk_id": f"{document.document_id}-chunk-{chunk_number}",
                        },
                    )
                )

            if end >= len(text):
                break

            start = end - self.overlap
            chunk_number += 1

        return chunks

    def chunk_documents(self, documents: list[Document]) -> list[Chunk]:
        chunks: list[Chunk] = []

        for document in documents:
            chunks.extend(self.chunk_document(document))

        return chunks
        