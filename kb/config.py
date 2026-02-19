from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import yaml


Mode = Literal["local", "openai"]


@dataclass(frozen=True)
class Paths:
    raw_dir: Path
    notes_file: Path
    processed_dir: Path
    index_dir: Path
    chroma_dir: Path
    manifest_path: Path
    snapshots_dir: Path
    logs_dir: Path


@dataclass(frozen=True)
class Chunking:
    chunk_size: int
    chunk_overlap: int


@dataclass(frozen=True)
class Retrieval:
    top_k_default: int


@dataclass(frozen=True)
class EmbeddingProviderConfig:
    provider: Literal["ollama", "openai", "gemini"]
    model: str
    base_url: Optional[str] = None
    timeout_seconds: int = 60


@dataclass(frozen=True)
class KBConfig:
    paths: Paths
    chunking: Chunking
    retrieval: Retrieval
    local_embeddings: EmbeddingProviderConfig
    openai_embeddings: EmbeddingProviderConfig


@dataclass(frozen=True)
class OpenClawConfig:
    workspace: str
    local_primary: str
    cloud_primary: str
    tools_profile: str
    deny_in_local: list[str]
    allow_in_cloud: list[str]


@dataclass(frozen=True)
class AppConfig:
    agent_name: str
    agent_role: str
    agent_description: str
    mode: Mode
    openclaw: OpenClawConfig
    kb: KBConfig
    retries: int
    retry_backoff_seconds: float


def _as_path(p: str) -> Path:
    return Path(p).expanduser().resolve()


def load_config(config_path: str | Path = "agent_config.yaml") -> AppConfig:
    cp = Path(config_path).expanduser().resolve()
    if not cp.exists():
        raise FileNotFoundError(f"Missing config file: {cp}")

    data: Dict[str, Any] = yaml.safe_load(cp.read_text(encoding="utf-8"))

    agent = data.get("agent", {})
    mode: Mode = data.get("mode", "local")
    if mode not in ("local", "openai"):
        raise ValueError("mode must be 'local' or 'openai'")

    oc = data.get("openclaw", {})
    oc_models = oc.get("models", {})
    oc_tools = oc.get("tools", {})

    kb = data.get("kb", {})
    paths = kb.get("paths", {})
    chunking = kb.get("chunking", {})
    retrieval = kb.get("retrieval", {})
    emb = kb.get("embeddings", {})
    emb_local = emb.get("local", {})
    emb_openai = emb.get("openai", {})

    paths_obj = Paths(
        raw_dir=_as_path(paths["raw_dir"]),
        notes_file=_as_path(paths["notes_file"]),
        processed_dir=_as_path(paths["processed_dir"]),
        index_dir=_as_path(paths["index_dir"]),
        chroma_dir=_as_path(paths["chroma_dir"]),
        manifest_path=_as_path(paths["manifest_path"]),
        snapshots_dir=_as_path(paths["snapshots_dir"]),
        logs_dir=_as_path(paths["logs_dir"]),
    )

    chunk_obj = Chunking(
        chunk_size=int(chunking.get("chunk_size", 900)),
        chunk_overlap=int(chunking.get("chunk_overlap", 150)),
    )
    if chunk_obj.chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if chunk_obj.chunk_overlap < 0:
        raise ValueError("chunk_overlap must be >= 0")
    if chunk_obj.chunk_overlap >= chunk_obj.chunk_size:
        raise ValueError("chunk_overlap must be < chunk_size")

    retr_obj = Retrieval(top_k_default=int(retrieval.get("top_k_default", 5)))

    local_emb = EmbeddingProviderConfig(
        provider="ollama",
        model=str(emb_local.get("model", "nomic-embed-text")),
        base_url=str(emb_local.get("base_url", "http://127.0.0.1:11434")),
        timeout_seconds=int(emb_local.get("timeout_seconds", 60)),
    )
    openai_emb = EmbeddingProviderConfig(
        provider=str(emb_openai.get("provider", "openai")),
        model=str(emb_openai.get("model", "text-embedding-3-small")),
        timeout_seconds=int(emb_openai.get("timeout_seconds", 60)),
    )

    kb_obj = KBConfig(
        paths=paths_obj,
        chunking=chunk_obj,
        retrieval=retr_obj,
        local_embeddings=local_emb,
        openai_embeddings=openai_emb,
    )

    oc_obj = OpenClawConfig(
        workspace=str(oc.get("workspace", ".")),
        local_primary=str(oc_models.get("local_primary", "ollama/gpt-oss:20b")),
        cloud_primary=str(oc_models.get("cloud_primary", "openai/gpt-5.1-codex")),
        tools_profile=str(oc_tools.get("profile", "minimal")),
        deny_in_local=list(oc_tools.get("deny_in_local", [])),
        allow_in_cloud=list(oc_tools.get("allow_in_cloud", [])),
    )

    rel = data.get("reliability", {})
    retries = int(rel.get("retries", 3))
    backoff = float(rel.get("retry_backoff_seconds", 1.5))

    return AppConfig(
        agent_name=str(agent.get("name", "KnowledgeBot")),
        agent_role=str(agent.get("role", "Local-first RAG assistant")),
        agent_description=str(agent.get("description", "")),
        mode=mode,
        openclaw=oc_obj,
        kb=kb_obj,
        retries=retries,
        retry_backoff_seconds=backoff,
    )
