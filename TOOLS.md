# TOOLS.md — KnowledgeBot Tools

## Knowledge Base tools (preferred)

### 1) kb_search
Use this to search the KB for relevant passages.
- Input: a natural language query and (optionally) top_k.
- Output: ranked snippets with source file paths.

When to use:
- Any time the user asks about their docs/notes.
- Before answering “I don't know”.

### 2) kb_add_note
Use this to save user notes as append-only memory.
- Input: text to append.
- Output: confirmation + where it was saved.

When to use:
- User says “remember this”, “note that”, “save this”, “add to KB”.

### 3) kb_ingest
Use this only when explicitly asked to ingest/rebuild knowledge.
- Typically the user runs `make kb-ingest` or `make kb-rebuild`.
- This tool exists for completeness, but do not run it automatically.

## Web tools (cloud mode only)
OpenClaw provides:
- `web_search`
- `web_fetch`

Only use web tools if:
- They are enabled, AND
- The user asks for web lookups, AND
- The KB does not contain the answer.
