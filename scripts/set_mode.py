from __future__ import annotations

import sys
from pathlib import Path

import yaml


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("local", "openai"):
        print("Usage: python scripts/set_mode.py (local|openai)")
        return 2

    mode = sys.argv[1]
    p = Path("agent_config.yaml")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    data["mode"] = mode
    p.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print(f"Set mode -> {mode} in agent_config.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
