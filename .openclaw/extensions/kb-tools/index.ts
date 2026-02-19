import { execFile } from "node:child_process";
import path from "node:path";

function runPython(args: string[], timeoutMs: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const py = process.env.KB_PYTHON || "python3";
    const scriptPath = path.resolve(process.cwd(), "scripts", "kb_cli.py");

    execFile(py, [scriptPath, ...args], { timeout: timeoutMs }, (err, stdout, stderr) => {
      if (err) {
        const msg =
          [
            "KB tool failed.",
            "",
            `Command: ${py} ${scriptPath} ${args.join(" ")}`,
            "",
            "stderr:",
            (stderr || "").trim(),
            "",
            "Common fixes:",
            "1) Activate venv: source .venv/bin/activate",
            "2) Install deps: make install",
            "3) If python3 isn't found, set KB_PYTHON in OpenClaw env (see scripts/sync_openclaw.py)",
            "4) Re-run: make sync",
          ].join("\n");
        return reject(new Error(msg));
      }
      resolve((stdout || "").trim());
    });
  });
}

export default function (api: any) {
  api.registerTool(
    {
      name: "kb_search",
      description: "Search the local Knowledge Base (RAG). Returns top matching snippets and sources.",
      parameters: {
        type: "object",
        additionalProperties: false,
        properties: {
          query: { type: "string", minLength: 1 },
          top_k: { type: "integer", minimum: 1, maximum: 20 },
        },
        required: ["query"],
      },
      async execute(_id: string, params: any) {
        const topK = params.top_k ?? 5;
        const out = await runPython(["search", "--query", params.query, "--top-k", String(topK), "--json"], 120_000);
        return { content: [{ type: "text", text: out }] };
      },
    },
    { optional: true }
  );

  api.registerTool(
    {
      name: "kb_add_note",
      description: "Append a note to knowledge/notes/notes.md (append-only) and optionally ingest it.",
      parameters: {
        type: "object",
        additionalProperties: false,
        properties: {
          text: { type: "string", minLength: 1 },
          ingest: { type: "boolean" },
        },
        required: ["text"],
      },
      async execute(_id: string, params: any) {
        const ingest = params.ingest === true ? ["--ingest"] : [];
        const out = await runPython(["add-note", "--text", params.text, "--json", ...ingest], 120_000);
        return { content: [{ type: "text", text: out }] };
      },
    },
    { optional: true }
  );

  api.registerTool(
    {
      name: "kb_ingest",
      description: "Ingest/rebuild the KB index from files in knowledge/raw and knowledge/notes.",
      parameters: {
        type: "object",
        additionalProperties: false,
        properties: {
          rebuild: { type: "boolean" },
        },
      },
      async execute(_id: string, params: any) {
        const cmd = params.rebuild === true ? "rebuild" : "ingest";
        const out = await runPython([cmd, "--json"], 15 * 60_000);
        return { content: [{ type: "text", text: out }] };
      },
    },
    { optional: true }
  );
}
