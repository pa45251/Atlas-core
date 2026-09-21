from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from atlas_core.obsidian import ObsidianClient, ObsidianError


class ObsidianSafetyTests(unittest.TestCase):
    def test_requires_https(self) -> None:
        with self.assertRaises(ObsidianError):
            ObsidianClient("http://127.0.0.1:27123", api_key="x")

    def test_rejects_non_loopback_host(self) -> None:
        with self.assertRaises(ObsidianError):
            ObsidianClient("https://example.com:27124", api_key="x")

    def test_missing_key_fails_before_authenticated_request(self) -> None:
        client = ObsidianClient("https://127.0.0.1:27124")
        with self.assertRaises(ObsidianError):
            client.list_files()

    def test_unicode_note_path_is_encoded(self) -> None:
        client = ObsidianClient("https://127.0.0.1:27124", api_key="secret")
        captured = {}

        def fake_open(request):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            captured["auth"] = request.get_header("Authorization")
            return "內容".encode("utf-8")

        client._open = fake_open
        result = client.read_note("英文/多義字解析：Fine.md")

        self.assertEqual(result, "內容")
        self.assertEqual(captured["method"], "GET")
        self.assertIn("%E8%8B%B1%E6%96%87", captured["url"])
        self.assertEqual(captured["auth"], "Bearer secret")

    def test_search_is_read_semantics_only(self) -> None:
        client = ObsidianClient("https://127.0.0.1:27124", api_key="secret")
        captured = {}

        def fake_open(request):
            captured["url"] = request.full_url
            captured["method"] = request.get_method()
            return b"[]"

        client._open = fake_open
        result = client.search("電漿")

        self.assertEqual(result, [])
        self.assertEqual(captured["method"], "POST")
        self.assertIn("/search/simple/", captured["url"])
        self.assertIn("query=%E9%9B%BB%E6%BC%BF", captured["url"])

    @patch("atlas_core.obsidian.urlopen")
    def test_bootstrap_ca_only_saves_pem(self, mocked_urlopen) -> None:
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b"-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----\n"

        mocked_urlopen.return_value = Response()

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "obsidian.crt"
            client = ObsidianClient("https://127.0.0.1:27124")
            saved = client.bootstrap_ca(path)
            self.assertEqual(saved, path)
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
