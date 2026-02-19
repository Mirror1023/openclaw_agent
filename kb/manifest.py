from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Manifest:
    path: Path
    data: Dict[str, Any]

    @classmethod
    def load(cls, manifest_path: Path) -> "Manifest":
        if manifest_path.exists():
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        else:
            data = {"version": 1, "created_at": now_iso(), "docs": {}, "signature": None}
        return cls(path=manifest_path, data=data)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, sort_keys=True), encoding="utf-8")

    def get_doc(self, source_path: str) -> Optional[Dict[str, Any]]:
        return self.data.get("docs", {}).get(source_path)

    def set_signature(self, signature: str) -> None:
        self.data["signature"] = signature

    def get_signature(self) -> Optional[str]:
        return self.data.get("signature")

    def upsert_doc(self, source_path: str, sha256: str, num_chunks: int) -> None:
        self.data.setdefault("docs", {})
        self.data["docs"][source_path] = {
            "sha256": sha256,
            "num_chunks": num_chunks,
            "ingested_at": now_iso(),
        }
