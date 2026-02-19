from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict

from kb.chunker import chunk_text
from kb.config import AppConfig
from kb.embedder import Embedder, EmbedderSpec
from kb.loaders import LoadedDoc, load_all
from kb.logging_setup import setup_logging
from kb.manifest import Manifest, sha256_file, now_iso
from kb.vectordb import VectorDB


def compute_signature(cfg: AppConfig) -> str:
    payload = {
        "mode": cfg.mode,
        "chunk_size": cfg.kb.chunking.chunk_size,
        "chunk_overlap": cfg.kb.chunking.chunk_overlap,
        "local_embed_model": cfg.kb.local_embeddings.model,
        "openai_embed_model": cfg.kb.openai_embeddings.model,
    }
    return json.dumps(payload, sort_keys=True)


def _write_processed(processed_dir: Path, doc: LoadedDoc) -> Path:
    processed_dir.mkdir(parents=True, exist_ok=True)
    out = processed_dir / (doc.source_path.stem + ".txt")
    out.write_text(doc.text, encoding="utf-8")
    return out


def ingest(cfg: AppConfig, rebuild: bool = False) -> Dict[str, Any]:
    logger = setup_logging(cfg.kb.paths.logs_dir, name="kb")

    cfg.kb.paths.notes_file.parent.mkdir(parents=True, exist_ok=True)
    if not cfg.kb.paths.notes_file.exists():
        cfg.kb.paths.notes_file.write_text("# Notes\n", encoding="utf-8")

    manifest = Manifest.load(cfg.kb.paths.manifest_path)
    sig = compute_signature(cfg)
    prev_sig = manifest.get_signature()

    vdb = VectorDB(cfg.kb.paths.chroma_dir, collection_name="kb_store")

    if rebuild:
        logger.warning("Rebuild requested: resetting vector DB and processed cache.")
        vdb.reset()
        if cfg.kb.paths.processed_dir.exists():
            shutil.rmtree(cfg.kb.paths.processed_dir, ignore_errors=True)
        manifest = Manifest.load(cfg.kb.paths.manifest_path)
        prev_sig = None

    if prev_sig and prev_sig != sig and not rebuild:
        raise RuntimeError(
            "KB config changed since last index build (chunking or embedding model).\n"
            "Run: make kb-rebuild\n"
            f"Old signature: {prev_sig}\nNew signature: {sig}"
        )

    manifest.set_signature(sig)

    docs = load_all(cfg.kb.paths.raw_dir, extra_files=[cfg.kb.paths.notes_file])

    if cfg.mode == "openai":
        emb_cfg = cfg.kb.openai_embeddings
        embedder = Embedder(
            EmbedderSpec(
                provider=emb_cfg.provider,
                model=emb_cfg.model,
                timeout_seconds=emb_cfg.timeout_seconds,
            ),
            retries=cfg.retries,
        )
        embedder_name = f"{emb_cfg.provider}:{emb_cfg.model}"
    else:
        embedder = Embedder(
            EmbedderSpec(
                provider="ollama",
                model=cfg.kb.local_embeddings.model,
                base_url=cfg.kb.local_embeddings.base_url,
                timeout_seconds=cfg.kb.local_embeddings.timeout_seconds,
            ),
            retries=cfg.retries,
        )
        embedder_name = f"ollama:{cfg.kb.local_embeddings.model}"

    added_chunks = 0
    updated_docs = 0
    skipped_docs = 0

    for doc in docs:
        _write_processed(cfg.kb.paths.processed_dir, doc)

        rel_source = str(doc.source_path.relative_to(Path.cwd()))
        doc_hash = sha256_file(doc.source_path)

        prev = manifest.get_doc(rel_source)
        if prev and prev.get("sha256") == doc_hash:
            skipped_docs += 1
            continue

        vdb.delete_where({"source_path": rel_source})

        chunks = chunk_text(doc.text, cfg.kb.chunking.chunk_size, cfg.kb.chunking.chunk_overlap)
        if not chunks:
            logger.warning("No text extracted from %s (skipping).", rel_source)
            continue

        texts = [c.text for c in chunks]
        embeddings = embedder.embed_many(texts)

        ids = [f"{doc_hash}:{c.chunk_index}" for c in chunks]
        metadatas = [
            {
                "source_path": rel_source,
                "chunk_index": c.chunk_index,
                "sha256": doc_hash,
                "ingested_at": now_iso(),
                "embedder": embedder_name,
            }
            for c in chunks
        ]

        vdb.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
        manifest.upsert_doc(rel_source, doc_hash, len(chunks))
        updated_docs += 1
        added_chunks += len(chunks)
        logger.info("Indexed %s (%d chunks).", rel_source, len(chunks))

    manifest.save()

    result = {
        "mode": cfg.mode,
        "embedder": embedder_name,
        "added_chunks": added_chunks,
        "updated_docs": updated_docs,
        "skipped_docs": skipped_docs,
        "total_chunks": vdb.count(),
        "manifest_path": str(cfg.kb.paths.manifest_path),
        "chroma_dir": str(cfg.kb.paths.chroma_dir),
    }
    logger.info("Ingest done: %s", result)
    return result


def search(cfg: AppConfig, query: str, top_k: int) -> Dict[str, Any]:
    logger = setup_logging(cfg.kb.paths.logs_dir, name="kb")
    q = (query or "").strip()
    if not q:
        raise ValueError("Query must be non-empty.")

    if cfg.mode == "openai":
        emb_cfg = cfg.kb.openai_embeddings
        embedder = Embedder(
            EmbedderSpec(
                provider=emb_cfg.provider,
                model=emb_cfg.model,
                timeout_seconds=emb_cfg.timeout_seconds,
            ),
            retries=cfg.retries,
        )
    else:
        embedder = Embedder(
            EmbedderSpec(
                provider="ollama",
                model=cfg.kb.local_embeddings.model,
                base_url=cfg.kb.local_embeddings.base_url,
                timeout_seconds=cfg.kb.local_embeddings.timeout_seconds,
            ),
            retries=cfg.retries,
        )

    vdb = VectorDB(cfg.kb.paths.chroma_dir, collection_name="kb_store")
    qe = embedder.embed_one(q)
    results = vdb.query(qe, top_k=top_k)

    out = {
        "query": q,
        "top_k": top_k,
        "results": [
            {
                "score": r.score,
                "source": r.source,
                "chunk_id": r.chunk_id,
                "text": r.text,
                "metadata": r.metadata,
            }
            for r in results
        ],
    }
    logger.info("Search query=%r top_k=%d results=%d", q, top_k, len(results))
    return out
