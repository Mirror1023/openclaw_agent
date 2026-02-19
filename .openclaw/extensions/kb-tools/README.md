# kb-tools (OpenClaw workspace extension)

This workspace extension exposes three tools to the OpenClaw agent:

- kb_search
- kb_add_note
- kb_ingest

They shell out to: scripts/kb_cli.py

If tools fail:
- Activate venv: source .venv/bin/activate
- Install deps: make install
- Sync OpenClaw config: make sync
- Restart gateway: openclaw gateway restart
