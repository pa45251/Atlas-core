from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def load_dotenv(path: str | Path = ".env") -> None:
    """Load a tiny subset of .env syntax without adding a dependency.

    Existing environment variables always win.
    """

    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


@dataclass(frozen=True)
class ObsidianSettings:
    base_url: str = "https://127.0.0.1:27124"
    api_key: str = ""
    ca_cert: str = ".local/obsidian-local-rest-api.crt"

    @classmethod
    def from_env(cls) -> "ObsidianSettings":
        load_dotenv()
        return cls(
            base_url=os.getenv("OBSIDIAN_API_URL", cls.base_url).rstrip("/"),
            api_key=os.getenv("OBSIDIAN_API_KEY", ""),
            ca_cert=os.getenv("OBSIDIAN_CA_CERT", cls.ca_cert),
        )
