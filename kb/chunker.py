from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Chunk:
    text: str
    chunk_index: int


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[Chunk]:
    # Simple character-based chunker that is predictable and beginner-proof.
    t = (text or "").strip()
    if not t:
        return []

    step = chunk_size - chunk_overlap
    if step <= 0:
        raise ValueError("chunk_size must be > chunk_overlap")

    chunks: List[Chunk] = []
    start = 0
    idx = 0
    while start < len(t):
        end = min(start + chunk_size, len(t))
        piece = t[start:end].strip()
        if piece:
            chunks.append(Chunk(text=piece, chunk_index=idx))
            idx += 1
        if end == len(t):
            break
        start += step

    return chunks
