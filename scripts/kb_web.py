from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from kb.config import load_config
from kb.pipeline import search

load_dotenv()
app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home(q: str = ""):
    cfg = load_config("agent_config.yaml")
    html = ["<html><body style='font-family: sans-serif; max-width: 900px; margin: 40px;'>"]
    html.append("<h1>KnowledgeBot KB Search</h1>")
    html.append("<form method='get'>")
    html.append("<input name='q' style='width: 70%; padding: 8px;' placeholder='Search your KB...'/>")
    html.append("<button style='padding: 8px;'>Search</button>")
    html.append("</form>")

    if q.strip():
        res = search(cfg, query=q, top_k=5)
        html.append(f"<h2>Results for: {q}</h2>")
        for r in res["results"]:
            html.append("<div style='border: 1px solid #ddd; padding: 12px; margin: 12px 0;'>")
            html.append(f"<div><b>Score:</b> {r['score']:.3f} <b>Source:</b> {r['source']}</div>")
            html.append("<pre style='white-space: pre-wrap;'>")
            html.append((r["text"][:1200]).replace("<", "&lt;"))
            html.append("</pre>")
            html.append("</div>")

    html.append("</body></html>")
    return "\n".join(html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8099)
