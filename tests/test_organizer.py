from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from atlas_core.organizer import ShadowOrganizer, _tokenize, render_summary, write_local_report


class FakeClient:
    def __init__(self, notes):
        self.notes = notes

    def walk_markdown_paths(self):
        return sorted(self.notes)

    def read_note_metadata(self, path):
        return self.notes[path]


class OrganizerTests(unittest.TestCase):
    def test_chinese_tokenization_has_shared_bigrams(self) -> None:
        a = _tokenize("低 duty pulsing", "離子衰減可能影響角度分佈", ())
        b = _tokenize("ion decay", "離子衰減與角度分佈的關係", ())
        self.assertTrue({"離子", "子衰", "衰減"} & a & b)

    def test_shadow_report_finds_structure_without_note_bodies(self) -> None:
        notes = {
            "英文/Fine.md": {
                "content": "# Fine\n多義字與語境",
                "tags": ["english"],
                "frontmatter": {},
                "stat": {"mtime": 10, "size": 20},
                "links": [],
                "backlinks": [],
                "unresolvedLinks": [],
            },
            "英文/Fine 多義字.md": {
                "content": "# Fine 多義字\n語境決定 fine 的意思",
                "tags": ["english"],
                "frontmatter": {},
                "stat": {"mtime": 11, "size": 30},
                "links": [],
                "backlinks": [],
                "unresolvedLinks": [],
            },
            "電漿/RF Pulsing.md": {
                "content": "# RF Pulsing\n離子衰減可能影響角度分佈",
                "tags": ["plasma"],
                "frontmatter": {"type": "hypothesis"},
                "stat": {"mtime": 12, "size": 40},
                "links": [],
                "backlinks": [],
                "unresolvedLinks": ["Ion Decay"],
            },
            "電漿/Ion Decay.md": {
                "content": "# Ion Decay\n離子衰減與角度分佈的關係",
                "tags": ["plasma"],
                "frontmatter": {},
                "stat": {"mtime": 13, "size": 40},
                "links": [],
                "backlinks": [],
                "unresolvedLinks": [],
            },
        }
        report = ShadowOrganizer(FakeClient(notes)).scan()

        self.assertEqual(report["mode"], "SHADOW_READ_ONLY")
        self.assertEqual(report["notes_scanned"], 4)
        self.assertEqual(report["domains"]["英文"], 2)
        self.assertEqual(report["domains"]["電漿"], 2)
        self.assertEqual(report["note_types"]["HYPOTHESIS"], 1)
        self.assertIn("電漿/RF Pulsing.md", report["unresolved_links"])
        self.assertIn("電漿/RF Pulsing.md", report["related_unlinked_notes"])
        self.assertEqual(report["safety"]["vault_modified"], False)
        self.assertEqual(report["safety"]["report_contains_note_bodies"], False)

        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn("離子衰減可能影響角度分佈", serialized)
        self.assertNotIn("語境決定 fine 的意思", serialized)

    def test_language_folder_wins_over_weak_hypothesis_words(self) -> None:
        notes = {
            "英文/Test.md": {
                "content": "# Test\n這個意思可能是語境造成的",
                "tags": [],
                "frontmatter": {},
                "stat": {"mtime": 1, "size": 10},
                "links": [],
                "backlinks": [],
                "unresolvedLinks": [],
            }
        }
        report = ShadowOrganizer(FakeClient(notes)).scan()
        self.assertEqual(report["note_types"]["LANGUAGE"], 1)
        self.assertNotIn("HYPOTHESIS", report["note_types"])

    def test_related_threshold_is_conservative(self) -> None:
        notes = {
            "A/one.md": {
                "content": "# one\nalpha beta gamma delta",
                "tags": [],
                "frontmatter": {},
                "stat": {},
                "links": [],
                "backlinks": [],
                "unresolvedLinks": [],
            },
            "A/two.md": {
                "content": "# two\nalpha beta unrelated",
                "tags": [],
                "frontmatter": {},
                "stat": {},
                "links": [],
                "backlinks": [],
                "unresolvedLinks": [],
            },
        }
        report = ShadowOrganizer(FakeClient(notes)).scan()
        suggestions = report["related_unlinked_notes"].get("A/one.md", [])
        for item in suggestions:
            self.assertGreaterEqual(item["similarity"], 0.35)

    def test_limit_is_respected(self) -> None:
        notes = {
            f"Notes/{i}.md": {
                "content": f"# Note {i}",
                "tags": [],
                "frontmatter": {},
                "stat": {"mtime": i, "size": 5},
                "links": [],
                "backlinks": [],
                "unresolvedLinks": [],
            }
            for i in range(5)
        }
        report = ShadowOrganizer(FakeClient(notes)).scan(limit=2)
        self.assertEqual(report["notes_scanned"], 2)

    def test_local_report_is_written_outside_vault_contract(self) -> None:
        report = {
            "mode": "SHADOW_READ_ONLY",
            "notes_scanned": 0,
            "domains": {},
            "note_types": {},
            "orphan_notes": [],
            "unresolved_links": {},
            "related_unlinked_notes": {},
            "duplicate_candidates": [],
            "domain_members": {},
            "safety": {
                "vault_modified": False,
                "write_methods_available": False,
                "report_contains_note_bodies": False,
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            write_local_report(report, str(path))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["mode"], "SHADOW_READ_ONLY")
            self.assertIn("No Obsidian note was created", render_summary(report))


if __name__ == "__main__":
    unittest.main()
