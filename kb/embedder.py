from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Literal, Optional

import time

import requests
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential


Provider = Literal["ollama", "openai", "gemini"]


@dataclass(frozen=True)
class EmbedderSpec:
    provider: Provider
    model: str
    base_url: Optional[str] = None
    timeout_seconds: int = 60


class EmbeddingError(RuntimeError):
    pass


def _normalize(text: str) -> str:
    return " ".join((text or "").split()).strip()


class Embedder:
    def __init__(self, spec: EmbedderSpec, retries: int = 3):
        self.spec = spec
        self.retries = retries

        if spec.provider == "openai":
            self.oa = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        else:
            self.oa = None
        self._gemini_api_key: Optional[str] = os.environ.get("GOOGLE_API_KEY")

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2.0, min=4, max=60))
    def embed_one(self, text: str) -> List[float]:
        t = _normalize(text)
        if not t:
            raise EmbeddingError("Cannot embed empty text.")

        if self.spec.provider == "openai":
            if not os.environ.get("OPENAI_API_KEY"):
                raise EmbeddingError("OPENAI_API_KEY is missing. Put it in .env then run make mode-cloud.")
            resp = self.oa.embeddings.create(model=self.spec.model, input=t)
            return resp.data[0].embedding

        if self.spec.provider == "gemini":
            key = self._gemini_api_key
            if not key:
                raise EmbeddingError("GOOGLE_API_KEY is missing. Get a free key at https://aistudio.google.com/apikey and add it to .env.")
            model = self.spec.model or "text-embedding-004"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={key}"
            r = requests.post(url, json={"content": {"parts": [{"text": t}]}}, timeout=self.spec.timeout_seconds)
            r.raise_for_status()
            return r.json()["embedding"]["values"]

        base = (self.spec.base_url or "http://127.0.0.1:11434").rstrip("/")
        timeout = self.spec.timeout_seconds

        # Try Ollama native endpoints (newer/older variants)
        for endpoint in ("/api/embeddings", "/api/embed"):
            url = f"{base}{endpoint}"
            try:
                r = requests.post(url, json={"model": self.spec.model, "prompt": t}, timeout=timeout)
                if r.status_code == 404:
                    continue
                r.raise_for_status()
                data = r.json()
                emb = data.get("embedding")
                if not emb:
                    raise EmbeddingError(f"Ollama response missing embedding field from {url}: {data}")
                return emb
            except requests.RequestException:
                pass

        # Fallback: OpenAI-compatible endpoint
        try:
            client = OpenAI(base_url=f"{base}/v1", api_key="ollama-local")
            resp = client.embeddings.create(model=self.spec.model, input=t)
            return resp.data[0].embedding
        except Exception as e:
            raise EmbeddingError(
                "Failed to embed via Ollama.\n"
                f"- Is Ollama running on {base}?\n"
                f"- Did you pull the embeddings model: ollama pull {self.spec.model}?\n"
                f"- Raw error: {e}"
            ) from e

    def embed_many(self, texts: List[str]) -> List[List[float]]:
        results = []
        for i, t in enumerate(texts):
            results.append(self.embed_one(t))
            if self.spec.provider == "gemini" and i < len(texts) - 1:
                time.sleep(4.5)  # Stay within Gemini free tier (~13 req/min)
        return results
