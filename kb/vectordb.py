from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import chromadb


@dataclass(frozen=True)
class SearchResult:
    score: float
    text: str
    source: str
    chunk_id: str
    metadata: Dict[str, Any]


class VectorDB:
    def __init__(self, chroma_dir: Path, collection_name: str = "kb_store"):
        chroma_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(chroma_dir))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        self.collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def delete_where(self, where: Dict[str, Any]) -> None:
        self.collection.delete(where=where)

    def count(self) -> int:
        return self.collection.count()

    def reset(self) -> None:
        name = self.collection.name
        self.client.delete_collection(name=name)
        self.collection = self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def query(self, query_embedding: List[float], top_k: int = 5) -> List[SearchResult]:
        res = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        ids = (res.get("ids") or [[]])[0]

        out: List[SearchResult] = []
        for doc, meta, dist, cid in zip(docs, metas, dists, ids):
            score = 1.0 - float(dist)  # cosine distance -> similarity-ish
            out.append(
                SearchResult(
                    score=score,
                    text=doc,
                    source=str(meta.get("source_path", "")),
                    chunk_id=str(cid),
                    metadata=dict(meta),
                )
            )
        return out
