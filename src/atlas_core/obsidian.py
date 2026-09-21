from __future__ import annotations

import json
from pathlib import Path
import ssl
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


class ObsidianError(RuntimeError):
    """Raised when the local Obsidian API cannot be used safely."""


def _validate_loopback_https(base_url: str) -> None:
    parsed = urlparse(base_url)
    if parsed.scheme != "https":
        raise ObsidianError("Atlas v1 requires HTTPS for the Obsidian connector.")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ObsidianError(
            "Atlas v1 only connects to loopback Obsidian endpoints "
            "(127.0.0.1, localhost, or ::1)."
        )


class ObsidianClient:
    """Read-only client for Obsidian Local REST API.

    Intentionally exposes no PUT, PATCH, DELETE, note-create, command-execute,
    or other vault-mutating operation.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        ca_cert: str | Path | None = None,
        timeout: float = 10.0,
    ) -> None:
        _validate_loopback_https(base_url)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.ca_cert = Path(ca_cert) if ca_cert else None

    def _ssl_context(self) -> ssl.SSLContext:
        if self.ca_cert and self.ca_cert.exists():
            return ssl.create_default_context(cafile=str(self.ca_cert))
        return ssl.create_default_context()

    def _headers(self, *, require_auth: bool = True, accept: str | None = None) -> dict[str, str]:
        headers: dict[str, str] = {}
        if require_auth:
            if not self.api_key:
                raise ObsidianError(
                    "OBSIDIAN_API_KEY is missing. Put it only in your local .env file."
                )
            headers["Authorization"] = f"Bearer {self.api_key}"
        if accept:
            headers["Accept"] = accept
        return headers

    def _open(self, request: Request) -> bytes:
        try:
            with urlopen(
                request,
                context=self._ssl_context(),
                timeout=self.timeout,
            ) as response:
                return response.read()
        except HTTPError as exc:
            raise ObsidianError(f"Obsidian API returned HTTP {exc.code}.") from exc
        except ssl.SSLCertVerificationError as exc:
            raise ObsidianError(
                "Obsidian HTTPS certificate is not trusted yet. "
                "Run: atlas obsidian bootstrap-ca"
            ) from exc
        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, ssl.SSLCertVerificationError):
                raise ObsidianError(
                    "Obsidian HTTPS certificate is not trusted yet. "
                    "Run: atlas obsidian bootstrap-ca"
                ) from exc
            raise ObsidianError(
                "Cannot reach Obsidian. Confirm Obsidian is open and "
                "Local REST API is enabled on https://127.0.0.1:27124."
            ) from exc

    def status(self) -> Any:
        request = Request(
            f"{self.base_url}/",
            method="GET",
            headers=self._headers(require_auth=False, accept="application/json"),
        )
        return _decode_json_or_text(self._open(request))

    def list_files(self, path: str = "") -> Any:
        clean = path.strip("/")
        encoded = quote(clean, safe="/")
        suffix = f"/vault/{encoded}/" if encoded else "/vault/"
        request = Request(
            f"{self.base_url}{suffix}",
            method="GET",
            headers=self._headers(accept="application/json"),
        )
        return _decode_json_or_text(self._open(request))

    def search(self, query: str) -> Any:
        if not query.strip():
            raise ObsidianError("Search query cannot be empty.")
        params = urlencode({"query": query})
        request = Request(
            f"{self.base_url}/search/simple/?{params}",
            data=b"",
            method="POST",
            headers=self._headers(accept="application/json"),
        )
        return _decode_json_or_text(self._open(request))

    def read_note(self, path: str) -> str:
        if not path.strip():
            raise ObsidianError("Note path cannot be empty.")
        encoded = quote(path.strip("/"), safe="/")
        request = Request(
            f"{self.base_url}/vault/{encoded}",
            method="GET",
            headers=self._headers(accept="text/markdown"),
        )
        return self._open(request).decode("utf-8")

    def read_note_metadata(self, path: str) -> dict[str, Any]:
        """Read note content plus Obsidian-resolved metadata without mutating it."""

        if not path.strip():
            raise ObsidianError("Note path cannot be empty.")
        encoded = quote(path.strip("/"), safe="/")
        request = Request(
            f"{self.base_url}/vault/{encoded}",
            method="GET",
            headers=self._headers(accept="application/vnd.olrapi.note+json"),
        )
        value = _decode_json_or_text(self._open(request))
        if not isinstance(value, dict):
            raise ObsidianError("Obsidian note metadata response was not a JSON object.")
        return value

    def walk_markdown_paths(self, path: str = "") -> list[str]:
        """Recursively enumerate Markdown notes using read-only directory listing."""

        results: list[str] = []
        stack = [path.strip("/")]
        ignored_roots = {".obsidian", ".trash", ".git", ".local"}

        while stack:
            current = stack.pop()
            listing = self.list_files(current)
            if isinstance(listing, dict):
                entries = listing.get("files", [])
            elif isinstance(listing, list):
                entries = listing
            else:
                raise ObsidianError("Obsidian directory listing had an unexpected format.")

            if not isinstance(entries, list):
                raise ObsidianError("Obsidian directory listing did not contain a file list.")

            for raw_entry in entries:
                if not isinstance(raw_entry, str):
                    continue
                is_dir = raw_entry.endswith("/")
                name = raw_entry.rstrip("/")
                child = f"{current}/{name}".strip("/") if current else name
                root = child.split("/", 1)[0]
                if root in ignored_roots:
                    continue
                if is_dir:
                    stack.append(child)
                elif child.lower().endswith(".md"):
                    results.append(child)

        return sorted(set(results))

    def bootstrap_ca(self, output_path: str | Path) -> Path:
        """Fetch the plugin's local CA once, then use normal TLS verification.

        The one unverified request is restricted to a validated HTTPS loopback
        endpoint and only fetches the fixed CA-certificate route.
        """

        _validate_loopback_https(self.base_url)
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        request = Request(
            f"{self.base_url}/obsidian-local-rest-api.crt",
            method="GET",
        )
        insecure_context = ssl._create_unverified_context()
        try:
            with urlopen(
                request,
                context=insecure_context,
                timeout=self.timeout,
            ) as response:
                payload = response.read()
        except (HTTPError, URLError) as exc:
            raise ObsidianError(
                "Could not download the local Obsidian CA certificate."
            ) from exc

        if b"BEGIN CERTIFICATE" not in payload:
            raise ObsidianError("Downloaded data did not look like a PEM certificate.")

        target.write_bytes(payload)
        return target


def _decode_json_or_text(raw: bytes) -> Any:
    text = raw.decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text
