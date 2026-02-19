# OpenClaw Agent Template (Local-first + OpenAI)

This repo is a plug-and-play starter for an OpenClaw agent that supports:

- Mode A: Offline/local-first (Ollama chat + Ollama embeddings + Chroma)
- Mode B: Cloud (OpenAI chat + OpenAI embeddings + Chroma)

## Quick start (Mac)

```bash
# 1) Create venv + install deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2) Install OpenClaw (see docs) and Ollama (for local mode)
# 3) Sync project config -> OpenClaw
make sync

# 4) Ingest docs and search
echo "Hello KB" > knowledge/raw/hello.txt
make kb-ingest
make kb-search q="Hello"
```

## Notes

- Add docs into: `knowledge/raw/`
- Append notes with: `make kb-add-note t="Remember this..."`
# openclaw_agent
# openclaw_agent
