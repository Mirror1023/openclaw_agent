from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTS = {".pdf", ".txt", ".md", ".docx"}


@dataclass(frozen=True)
class LoadedDoc:
    source_path: Path
    text: str


def list_source_files(raw_dir: Path) -> List[Path]:
    files: List[Path] = []
    if not raw_dir.exists():
        return files
    for p in raw_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            files.append(p)
    return sorted(files)


def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_docx(path: Path) -> str:
    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(parts).strip()


def load_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts).strip()


def load_any(path: Path) -> LoadedDoc:
    ext = path.suffix.lower()
    if ext == ".pdf":
        text = load_pdf(path)
    elif ext in (".txt", ".md"):
        text = load_text_file(path)
    elif ext == ".docx":
        text = load_docx(path)
    else:
        raise ValueError(f"Unsupported file type: {path}")
    return LoadedDoc(source_path=path, text=text)


def load_all(raw_dir: Path, extra_files: Optional[Iterable[Path]] = None) -> List[LoadedDoc]:
    docs: List[LoadedDoc] = []
    for p in list_source_files(raw_dir):
        docs.append(load_any(p))

    if extra_files:
        for p in extra_files:
            if p.exists() and p.is_file():
                docs.append(load_any(p))
    return docs
