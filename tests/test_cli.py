from __future__ import annotations

import json
import unittest

from atlas_core.cli import _console_safe_text


class ConsoleUnicodeTests(unittest.TestCase):
    def test_cp950_preserves_chinese_and_escapes_emoji(self) -> None:
        text = "英文😀"
        safe = _console_safe_text(text, "cp950")
        self.assertTrue(safe.startswith("英文"))
        self.assertNotIn("😀", safe)
        self.assertIn("\\ud83d\\ude00", safe.lower())

    def test_json_remains_valid_after_console_safety_transform(self) -> None:
        payload = {"name": "英文😀", "count": 1}
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
        safe = _console_safe_text(rendered, "cp950")
        self.assertEqual(json.loads(safe), payload)


if __name__ == "__main__":
    unittest.main()
