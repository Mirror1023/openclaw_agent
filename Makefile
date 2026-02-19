SHELL := /bin/bash

.PHONY: help install mode-local mode-cloud sync kb-ingest kb-rebuild kb-search kb-add-note kb-web chat-ui chat-cli test

help:
	@echo "Commands:"
	@echo "  make install              - install python deps"
	@echo "  make mode-local           - set Mode A (Ollama local) + sync OpenClaw"
	@echo "  make mode-cloud           - set Mode B (OpenAI) + sync OpenClaw"
	@echo "  make sync                 - sync agent_config.yaml -> OpenClaw config"
	@echo "  make kb-ingest            - ingest new/changed docs from knowledge/raw"
	@echo "  make kb-rebuild           - rebuild vector index from scratch"
	@echo "  make kb-search q='...'    - search KB"
	@echo "  make kb-add-note t='...'  - append note + ingest"
	@echo "  make kb-web               - run optional KB web UI on http://127.0.0.1:8099"
	@echo "  make chat-ui              - open OpenClaw dashboard (web UI)"
	@echo "  make chat-cli m='...'     - run one OpenClaw CLI turn"
	@echo "  make test                 - run pytest"

install:
	@source .venv/bin/activate && pip install -r requirements.txt

mode-local:
	@source .venv/bin/activate && python scripts/set_mode.py local
	@source .venv/bin/activate && python scripts/sync_openclaw.py

mode-cloud:
	@source .venv/bin/activate && python scripts/set_mode.py openai
	@source .venv/bin/activate && python scripts/sync_openclaw.py

sync:
	@source .venv/bin/activate && python scripts/sync_openclaw.py

kb-ingest:
	@source .venv/bin/activate && python scripts/kb_cli.py ingest

kb-rebuild:
	@source .venv/bin/activate && python scripts/kb_cli.py rebuild

kb-search:
	@source .venv/bin/activate && python scripts/kb_cli.py search --query "$(q)" --top-k 5

kb-add-note:
	@source .venv/bin/activate && python scripts/kb_cli.py add-note --text "$(t)" --ingest

kb-web:
	@source .venv/bin/activate && python scripts/kb_web.py

chat-ui:
	@openclaw dashboard

chat-cli:
	@openclaw agent --message "$(m)" --timeout 120

test:
	@source .venv/bin/activate && pytest -q
