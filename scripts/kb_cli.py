from __future__ import annotations

import argparse
import json

from dotenv import load_dotenv

from kb.config import load_config
from kb.pipeline import ingest, search


def main() -> int:
    load_dotenv()

    p = argparse.ArgumentParser(prog="kb_cli", description="Knowledge Base CLI (ingest/search/notes).")
    p.add_argument("--config", default="agent_config.yaml", help="Path to agent_config.yaml")

    sub = p.add_subparsers(dest="cmd", required=True)

    s_ingest = sub.add_parser("ingest", help="Ingest new/changed documents incrementally.")
    s_ingest.add_argument("--json", action="store_true", help="Machine-readable JSON output")

    s_rebuild = sub.add_parser("rebuild", help="Rebuild index from scratch (deletes old index).")
    s_rebuild.add_argument("--json", action="store_true", help="Machine-readable JSON output")

    s_search = sub.add_parser("search", help="Search the knowledge base.")
    s_search.add_argument("--query", required=True, help="Search query text")
    s_search.add_argument("--top-k", type=int, default=5, help="How many results to return")
    s_search.add_argument("--json", action="store_true", help="Machine-readable JSON output")

    s_note = sub.add_parser("add-note", help="Append a note to knowledge/notes/notes.md")
    s_note.add_argument("--text", required=True, help="Note text to append")
    s_note.add_argument("--ingest", action="store_true", help="Ingest after writing the note")
    s_note.add_argument("--json", action="store_true", help="Machine-readable JSON output")

    args = p.parse_args()
    cfg = load_config(args.config)

    if args.cmd in ("ingest", "rebuild"):
        res = ingest(cfg, rebuild=(args.cmd == "rebuild"))
        if getattr(args, "json", False):
            print(json.dumps(res, indent=2))
        else:
            print("\nKB index updated.")
            for k, v in res.items():
                print(f"- {k}: {v}")
        return 0

    if args.cmd == "search":
        res = search(cfg, query=args.query, top_k=args.top_k)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"\nQuery: {res['query']}\n")
            for i, r in enumerate(res["results"], start=1):
                print(f"[{i}] score={r['score']:.3f} source={r['source']} chunk_id={r['chunk_id']}")
                print(r["text"][:800].strip())
                print("-" * 60)
        return 0

    if args.cmd == "add-note":
        notes_path = cfg.kb.paths.notes_file
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        if not notes_path.exists():
            notes_path.write_text("# Notes\n", encoding="utf-8")

        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n\n## {ts}\n\n{args.text.strip()}\n"
        with notes_path.open("a", encoding="utf-8") as f:
            f.write(entry)

        out = {
            "notes_file": str(notes_path),
            "appended_chars": len(entry),
            "ingested": False,
        }

        if args.ingest:
            ingest(cfg, rebuild=False)
            out["ingested"] = True

        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print("Note saved.")
            print(f"- notes_file: {out['notes_file']}")
            print(f"- ingested: {out['ingested']}")
        return 0

    raise RuntimeError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
