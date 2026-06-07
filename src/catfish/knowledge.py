"""Ingest -> normalized markdown -> Map of Content -> JSONL spine.

Core handles .md/.txt/.eml on the standard library alone. docx/pdf/pptx route through
markitdown only if the optional [ingest] extra is installed. Tagging/summary are deterministic
heuristics at MVP (no LLM call), so ingest is free and reproducible.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .models import Note

SUPPORTED_CORE = {".md", ".txt", ".markdown", ".eml"}
SUPPORTED_MARKITDOWN = {".pdf", ".docx", ".pptx", ".xlsx", ".html"}

# keyword -> tag (constrained vocab the persona filters key on). This is the DEFAULT, in-code
# vocabulary (software / product / eng). To retarget Catfish to another domain, override it
# WITHOUT editing this file via config/tags.yaml — see load_tag_vocab() below and ADAPTING.md.
# The tags here must match the filter.tags_any lists in personas/*.yaml (they are a matched pair).
DEFAULT_TAG_VOCAB = {
    "auth": "auth", "login": "auth", "oauth": "auth", "session token": "auth",
    "security": "security", "vulnerab": "security", "auth-07": "security", "finding": "security",
    "migrat": "migration", "cutover": "migration",
    "billing": "billing", "invoice": "billing", "revenue": "billing",
    "launch": "launch", "go-live": "launch",
    "deadline": "timeline", " q3": "timeline", " q4": "timeline", "sprint": "timeline", "schedule": "timeline",
    "capacity": "resource", "headcount": "resource", "the team": "resource", "hire": "resource",
    "depend": "dependency", "blocker": "dependency", "blocks": "dependency",
    "risk": "risk",
    "pii": "pii", "credential": "credential", "password": "credential",
    "permission": "permission", "access control": "permission",
    "external": "external", "third-party": "external", "vendor": "external",
    "scope": "scope", "constraint": "constraint", "assume": "assumption",
}

_SENT = re.compile(r"(?<=[.!?])\s+")


def _hash(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()[:32]


def _eml_to_text(raw: bytes) -> tuple[str, str]:
    import email
    from email import policy
    msg = email.message_from_bytes(raw, policy=policy.default)
    subject = msg.get("subject", "")
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content()
                break
    else:
        body = msg.get_content()
    frm = msg.get("from", "")
    return subject, f"From: {frm}\nSubject: {subject}\n\n{body}".strip()


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    """If the text opens with a YAML frontmatter block (``---`` … ``---``), return its ``title:``
    value (if present) and the body after the block; otherwise ``(None, text)``.

    The Foam wiki and cognition pages Catfish generates carry frontmatter, so title/summary
    extraction has to look past the opening ``---`` fence instead of grabbing it as the title.
    """
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    block, body = text[3:end], text[end + 4:].lstrip("\n")
    title = None
    for line in block.splitlines():
        if line.strip().lower().startswith("title:"):
            title = line.split(":", 1)[1].strip().strip("\"'") or None
            break
    return title, body


def _extract(path: Path) -> tuple[str, str, str]:
    """Return (source_type, title, body)."""
    ext = path.suffix.lower()
    raw = path.read_bytes()
    if ext == ".eml":
        subject, body = _eml_to_text(raw)
        return "eml", (subject or path.stem), body
    if ext in SUPPORTED_CORE:
        text = raw.decode("utf-8", errors="replace").lstrip("﻿")
        meta_title, body = _split_frontmatter(text)   # skip YAML frontmatter if present
        title = meta_title or path.stem
        if not meta_title:
            for line in body.splitlines():
                if line.startswith("#"):
                    title = line.lstrip("# ").strip()
                    break
                if line.strip():
                    title = line.strip()
                    break
        return ext.lstrip("."), title, body
    if ext in SUPPORTED_MARKITDOWN:
        try:
            from markitdown import MarkItDown  # optional [ingest] extra
        except ImportError as e:
            raise RuntimeError(f"{path.name}: needs `pip install catfish[ingest]` for {ext}") from e
        md = MarkItDown().convert(str(path))
        return ext.lstrip("."), (md.title or path.stem), md.text_content
    raise RuntimeError(f"unsupported source type: {ext}")


def _summarize(body: str) -> str:
    text = " ".join(body.split())
    if not text:
        return ""
    sent = _SENT.split(text)[0]
    words = sent.split()
    return " ".join(words[:24]) + (" …" if len(words) > 24 else "")


def load_tag_vocab(config_dir: Path | str = "config") -> dict[str, str]:
    """Keyword->tag vocabulary the persona filters key on.

    Reads ``<config_dir>/tags.yaml`` if present; otherwise returns DEFAULT_TAG_VOCAB. Mirrors
    ``personas.load_personas``: graceful fallback when the file or pyyaml is absent, so a fresh
    install with no config still tags deterministically. This is the first retarget seam
    (see ADAPTING.md) — a new domain ships its own tags.yaml, never a source edit.
    """
    path = Path(config_dir) / "tags.yaml"
    if not path.is_file():
        return dict(DEFAULT_TAG_VOCAB)
    try:
        import yaml  # graceful: fall back to defaults if pyyaml absent
    except ImportError:
        return dict(DEFAULT_TAG_VOCAB)
    data = yaml.safe_load(path.read_text()) or {}
    vocab = {str(k).lower(): str(v) for k, v in data.items()}
    return vocab or dict(DEFAULT_TAG_VOCAB)


def _tag(body: str, vocab: dict[str, str]) -> list[str]:
    low = " " + body.lower() + " "
    tags: list[str] = []
    for kw, tag in vocab.items():
        if kw in low and tag not in tags:
            tags.append(tag)
    return tags


def ingest(source: Path, vocab: dict[str, str] | None = None) -> list[Note]:
    source = Path(source)
    vocab = vocab if vocab is not None else DEFAULT_TAG_VOCAB
    paths = []
    if source.is_file():
        paths = [source]
    else:
        for p in sorted(source.rglob("*")):
            # Skip anything under a dot-dir (.catfish, .memory, .pytest_cache, .git, …) or a
            # dotfile. Checked relative to source, so a dot in the source's own path (e.g. a
            # repo living under ~/.config) doesn't wrongly exclude everything.
            if p.is_file() and p.suffix.lower() in (SUPPORTED_CORE | SUPPORTED_MARKITDOWN) \
                    and not any(part.startswith(".") for part in p.relative_to(source).parts):
                paths.append(p)

    notes: list[Note] = []
    seen: set[str] = set()
    n = 0
    for p in paths:
        try:
            stype, title, body = _extract(p)
        except RuntimeError:
            continue  # skip unsupported / missing-extra files rather than crash the run
        h = _hash(p.read_bytes())
        if h in seen:
            continue
        seen.add(h)
        n += 1
        notes.append(Note(
            id=f"nt-{n:04d}", title=title, type="source", tags=_tag(body, vocab),
            summary=_summarize(body), status="seedling", source_hash=h,
            source_type=stype, path=str(p), body=body,
        ))
    return notes


def _frontmatter(note: Note) -> str:
    fm = {
        "id": note.id, "title": note.title, "type": note.type,
        "tags": "[" + ", ".join(note.tags) + "]", "summary": note.summary,
        "status": note.status, "source_type": note.source_type, "source_hash": note.source_hash,
    }
    lines = ["---"] + [f"{k}: {v}" for k, v in fm.items()] + ["---"]
    return "\n".join(lines)


def build_spine(notes: list[Note], catfish_dir: Path) -> Path:
    catfish_dir = Path(catfish_dir)
    notes_dir = catfish_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    spine = catfish_dir / "_graph_index.jsonl"
    # UPSERT keyed by source_hash (fallback id for legacy rows): load existing rows, then merge in
    # this run's notes so re-ingesting an unchanged corpus is idempotent and earlier-added notes
    # (e.g. a decision Note) survive later ingests. Order-preserving: existing first, new appended.
    rows: dict[str, dict] = {}
    if spine.is_file():
        for line in spine.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                rows[row.get("source_hash") or row.get("id")] = row
    for note in notes:
        (notes_dir / f"{note.id}.md").write_text(_frontmatter(note) + "\n\n" + note.body)
        rows[note.source_hash or note.id] = note.spine_row()
    with spine.open("w") as fh:
        for row in rows.values():
            fh.write(json.dumps(row) + "\n")
    return spine
