from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

from kb.config import load_config


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, text=True, capture_output=True)
    if r.returncode != 0:
        msg = (
            "OpenClaw sync failed.\n\n"
            f"Command: {' '.join(cmd)}\n\n"
            f"stdout:\n{r.stdout}\n\n"
            f"stderr:\n{r.stderr}\n\n"
            "Next steps:\n"
            "1) Ensure OpenClaw is installed: openclaw --version\n"
            "2) Run: openclaw doctor\n"
            "3) If OpenClaw config is invalid, fix it or reinstall.\n"
        )
        raise RuntimeError(msg)
    if r.stdout.strip():
        print(r.stdout.strip())


def main() -> int:
    # Loads project .env (NOT ~/.openclaw/.env)
    load_dotenv()
    cfg = load_config("agent_config.yaml")

    project_root = Path.cwd().resolve()
    workspace = str(project_root)

    # 1) Set the agent workspace to this repo
    run(["openclaw", "config", "set", "agents.defaults.workspace", workspace])

    # 2) Ensure plugin tool runner Python is available to the Gateway process
    kb_python = os.environ.get("KB_PYTHON", "python3").strip() or "python3"
    run(["openclaw", "config", "set", "env.KB_PYTHON", kb_python])

    # 3) Configure mode-specific model + tool policy
    if cfg.mode == "local":
        # Ollama doesn't require a real key. Any string enables provider checks.
        run(["openclaw", "config", "set", "env.OLLAMA_API_KEY", "ollama-local"])
        run(["openclaw", "config", "set", "agents.defaults.model.primary", cfg.openclaw.local_primary])

        deny = cfg.openclaw.deny_in_local
        run(["openclaw", "config", "set", "tools.profile", cfg.openclaw.tools_profile])
        run(["openclaw", "config", "set", "tools.deny", json.dumps(deny)])
    else:
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key or key.startswith("sk-REPLACE_ME"):
            raise RuntimeError(
                "OPENAI_API_KEY is missing.\n"
                "Fix: edit .env and set OPENAI_API_KEY, then run: make mode-cloud"
            )
        run(["openclaw", "config", "set", "env.OPENAI_API_KEY", key])
        run(["openclaw", "config", "set", "agents.defaults.model.primary", cfg.openclaw.cloud_primary])

        run(["openclaw", "config", "set", "tools.profile", cfg.openclaw.tools_profile])

    # 4) Add plugin tools on top of the profile via alsoAllow
    # (tools.allow is an exclusive allowlist; alsoAllow appends to the profile set)
    run(["openclaw", "config", "set", "tools.alsoAllow", json.dumps(["kb_search", "kb_add_note", "kb_ingest"])])
    run(["openclaw", "config", "set", "tools.allow", json.dumps([])])
    run(["openclaw", "config", "set", "tools.deny", json.dumps([])])

    print("\n✅ OpenClaw sync complete.")
    print(f"- mode: {cfg.mode}")
    print(f"- workspace: {workspace}")
    print("\nIMPORTANT: plugin load + tool policy changes require a gateway restart:")
    print("  openclaw gateway restart")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
