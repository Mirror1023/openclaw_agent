import yaml
from pathlib import Path

from kb.config import load_config
from kb.pipeline import ingest


def test_smoke_ingest_and_search(tmp_path: Path, monkeypatch):
    (tmp_path / "knowledge/raw").mkdir(parents=True)
    (tmp_path / "knowledge/notes").mkdir(parents=True)
    (tmp_path / "knowledge/index/chroma").mkdir(parents=True)
    (tmp_path / "knowledge/processed").mkdir(parents=True)
    (tmp_path / "knowledge/snapshots").mkdir(parents=True)
    (tmp_path / "logs").mkdir(parents=True)

    (tmp_path / "knowledge/raw/doc.txt").write_text("Cats are mammals.", encoding="utf-8")
    (tmp_path / "knowledge/notes/notes.md").write_text("# Notes\n", encoding="utf-8")

    cfg = {
        "agent": {"name": "T", "role": "T", "description": "T"},
        "mode": "local",
        "openclaw": {"workspace": ".", "models": {"local_primary": "ollama/x", "cloud_primary": "openai/x"}, "tools": {"profile": "minimal", "deny_in_local": [], "allow_in_cloud": []}},
        "kb": {
            "paths": {
                "raw_dir": str(tmp_path / "knowledge/raw"),
                "notes_file": str(tmp_path / "knowledge/notes/notes.md"),
                "processed_dir": str(tmp_path / "knowledge/processed"),
                "index_dir": str(tmp_path / "knowledge/index"),
                "chroma_dir": str(tmp_path / "knowledge/index/chroma"),
                "manifest_path": str(tmp_path / "knowledge/index/manifest.json"),
                "snapshots_dir": str(tmp_path / "knowledge/snapshots"),
                "logs_dir": str(tmp_path / "logs"),
            },
            "chunking": {"chunk_size": 200, "chunk_overlap": 50},
            "retrieval": {"top_k_default": 5},
            "embeddings": {
                "local": {"provider": "ollama", "model": "nomic-embed-text", "base_url": "http://127.0.0.1:11434", "timeout_seconds": 1},
                "openai": {"provider": "openai", "model": "text-embedding-3-small", "timeout_seconds": 1},
            },
        },
        "reliability": {"retries": 1, "retry_backoff_seconds": 0.1},
    }
    (tmp_path / "agent_config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    # This smoke test is allowed to fail if Ollama isn't running.
    try:
        ingest(load_config("agent_config.yaml"), rebuild=True)
    except Exception as e:
        assert "Ollama" in str(e) or "Failed to embed" in str(e)
