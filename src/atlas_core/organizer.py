from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import PurePosixPath
import json
import math
import re
from typing import Any

from .obsidian import ObsidianClient


_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_+\-]{1,}|[\u3400-\u9fff]{2,}")
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
_STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from", "into", "your", "about",
    "what", "when", "where", "how", "why", "are", "was", "were", "have", "has",
    "一個", "一些", "這個", "那個", "以及", "因為", "所以", "如果", "可以", "需要",
}


@dataclass(frozen=True)
class NoteRecord:
    path: str
    title: str
    domain: str
    note_type: str
    tags: tuple[str, ...]
    links: tuple[str, ...]
    backlinks: tuple[str, ...]
    unresolved_links: tuple[str, ...]
    mtime: float
    size: int
    tokens: frozenset[str]


def _basename(path: str) -> str:
    return PurePosixPath(path).stem


def _domain_from_path(path: str, tags: tuple[str, ...]) -> str:
    parts = PurePosixPath(path).parts
    if len(parts) > 1:
        return parts[0]
    if tags:
        return tags[0].lstrip("#")
    return "Unclassified"


def _note_type(path: str, content: str, frontmatter: dict[str, Any]) -> str:
    explicit = frontmatter.get("type") or frontmatter.get("note_type")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().upper().replace(" ", "_")

    probe = (path + "\n" + content[:1200]).lower()
    rules = (
        ("HYPOTHESIS", ("hypothesis", "假說", "假設", "推測", "可能是")),
        ("QUESTION", ("question", "問題", "為什麼", "如何", "？", "?")),
        ("IDEA", ("idea", "想法", "靈感", "點子")),
        ("REFERENCE", ("paper", "reference", "文獻", "論文", "source:")),
        ("LANGUAGE", ("英文", "english", "vocabulary", "grammar", "單字", "片語")),
    )
    for kind, cues in rules:
        if any(cue.lower() in probe for cue in cues):
            return kind
    return "CONCEPT"


def _tokenize(title: str, content: str, tags: tuple[str, ...]) -> frozenset[str]:
    text = " ".join([title, *tags, *_HEADING_RE.findall(content), content[:6000]])
    tokens: set[str] = set()
    for match in _WORD_RE.finditer(text):
        token = match.group(0).lower()
        if token in _STOPWORDS or len(token) < 2:
            continue
        if re.fullmatch(r"[\u3400-\u9fff]+", token):
            # Chinese text has no spaces. Character bigrams provide a lightweight,
            # dependency-free similarity signal without pretending to be a tokenizer.
            if len(token) == 2:
                tokens.add(token)
            else:
                tokens.update(token[i : i + 2] for i in range(len(token) - 1))
        else:
            tokens.add(token)
    return frozenset(tokens)


def _similarity(a: NoteRecord, b: NoteRecord) -> float:
    if not a.tokens or not b.tokens:
        return 0.0
    overlap = len(a.tokens & b.tokens)
    if overlap == 0:
        return 0.0
    cosine = overlap / math.sqrt(len(a.tokens) * len(b.tokens))
    domain_bonus = 0.08 if a.domain == b.domain else 0.0
    return min(1.0, cosine + domain_bonus)


def _normal_title(title: str) -> str:
    return re.sub(r"[^a-z0-9\u3400-\u9fff]+", "", title.lower())


class ShadowOrganizer:
    """Builds a knowledge-management report without changing the vault."""

    def __init__(self, client: ObsidianClient) -> None:
        self.client = client

    def scan(self, *, limit: int | None = None) -> dict[str, Any]:
        paths = self.client.walk_markdown_paths()
        if limit is not None:
            paths = paths[: max(0, limit)]

        notes: list[NoteRecord] = []
        for path in paths:
            payload = self.client.read_note_metadata(path)
            content = str(payload.get("content", ""))
            tags = tuple(str(x) for x in payload.get("tags", []) if isinstance(x, str))
            links = tuple(str(x) for x in payload.get("links", []) if isinstance(x, str))
            backlinks = tuple(str(x) for x in payload.get("backlinks", []) if isinstance(x, str))
            unresolved = tuple(
                str(x) for x in payload.get("unresolvedLinks", []) if isinstance(x, str)
            )
            frontmatter = payload.get("frontmatter")
            if not isinstance(frontmatter, dict):
                frontmatter = {}
            stat = payload.get("stat")
            if not isinstance(stat, dict):
                stat = {}
            title = _basename(path)
            notes.append(
                NoteRecord(
                    path=path,
                    title=title,
                    domain=_domain_from_path(path, tags),
                    note_type=_note_type(path, content, frontmatter),
                    tags=tags,
                    links=links,
                    backlinks=backlinks,
                    unresolved_links=unresolved,
                    mtime=float(stat.get("mtime", 0) or 0),
                    size=int(stat.get("size", len(content.encode("utf-8"))) or 0),
                    tokens=_tokenize(title, content, tags),
                )
            )

        by_path = {n.path: n for n in notes}
        linked_names: dict[str, set[str]] = {}
        for note in notes:
            names = {_normal_title(PurePosixPath(x).stem) for x in note.links}
            linked_names[note.path] = names

        related: dict[str, list[dict[str, Any]]] = {}
        duplicate_candidates: list[dict[str, Any]] = []
        for i, note in enumerate(notes):
            scored: list[tuple[float, NoteRecord]] = []
            for j, other in enumerate(notes):
                if i == j:
                    continue
                score = _similarity(note, other)
                if score >= 0.16:
                    scored.append((score, other))
                if i < j:
                    same_title = _normal_title(note.title) == _normal_title(other.title)
                    if same_title or score >= 0.72:
                        duplicate_candidates.append(
                            {
                                "a": note.path,
                                "b": other.path,
                                "similarity": round(score, 3),
                                "reason": "same_normalized_title" if same_title else "high_content_overlap",
                            }
                        )
            scored.sort(key=lambda item: (-item[0], item[1].path))
            suggestions: list[dict[str, Any]] = []
            for score, other in scored[:8]:
                already_linked = _normal_title(other.title) in linked_names[note.path]
                if already_linked:
                    continue
                suggestions.append(
                    {
                        "path": other.path,
                        "similarity": round(score, 3),
                        "same_domain": note.domain == other.domain,
                    }
                )
                if len(suggestions) >= 5:
                    break
            if suggestions:
                related[note.path] = suggestions

        domains = Counter(n.domain for n in notes)
        types = Counter(n.note_type for n in notes)
        orphans = [n.path for n in notes if not n.links and not n.backlinks]
        unresolved = {
            n.path: list(n.unresolved_links)
            for n in notes
            if n.unresolved_links
        }

        clusters: dict[str, list[str]] = defaultdict(list)
        for note in notes:
            clusters[note.domain].append(note.path)

        return {
            "mode": "SHADOW_READ_ONLY",
            "notes_scanned": len(notes),
            "domains": dict(sorted(domains.items(), key=lambda x: (-x[1], x[0]))),
            "note_types": dict(sorted(types.items(), key=lambda x: (-x[1], x[0]))),
            "orphan_notes": orphans,
            "unresolved_links": unresolved,
            "related_unlinked_notes": related,
            "duplicate_candidates": duplicate_candidates[:100],
            "domain_members": {k: sorted(v) for k, v in sorted(clusters.items())},
            "safety": {
                "vault_modified": False,
                "write_methods_available": False,
                "report_contains_note_bodies": False,
            },
        }


def render_summary(report: dict[str, Any]) -> str:
    lines = [
        "Atlas Knowledge Organizer — SHADOW MODE",
        f"Notes scanned: {report['notes_scanned']}",
        "",
        "Domains:",
    ]
    for name, count in list(report.get("domains", {}).items())[:15]:
        lines.append(f"  - {name}: {count}")

    lines += ["", "Note types:"]
    for name, count in report.get("note_types", {}).items():
        lines.append(f"  - {name}: {count}")

    lines += [
        "",
        f"Orphan notes: {len(report.get('orphan_notes', []))}",
        f"Notes with unresolved links: {len(report.get('unresolved_links', {}))}",
        f"Notes with related-unlinked suggestions: {len(report.get('related_unlinked_notes', {}))}",
        f"Possible duplicate pairs: {len(report.get('duplicate_candidates', []))}",
        "",
        "No Obsidian note was created, edited, moved, or deleted.",
    ]
    return "\n".join(lines)


def write_local_report(report: dict[str, Any], path: str) -> None:
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
