from pathlib import Path
from kb.manifest import Manifest


def test_manifest_roundtrip(tmp_path: Path):
    p = tmp_path / "manifest.json"
    m = Manifest.load(p)
    m.set_signature("sig1")
    m.upsert_doc("a.txt", "hash", 3)
    m.save()

    m2 = Manifest.load(p)
    assert m2.get_signature() == "sig1"
    assert m2.get_doc("a.txt")["num_chunks"] == 3
