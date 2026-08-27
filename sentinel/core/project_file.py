"""Load sentinel.yaml / sentinel.json project files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .health_spec import HealthExpect

PROJECT_FILENAMES = (
    "sentinel.yaml",
    "sentinel.yml",
    "sentinel.json",
    ".sentinel/services.yaml",
    ".sentinel/services.json",
)

SAMPLE_YAML = """# DevOps Sentinel project file — commit this next to the repo.
# sentinel up   monitors every service here.
services:
  - name: example
    url: https://example.com
    interval: 30
    failure_threshold: 3
    recovery_threshold: 2
    expect:
      status: [200, 301, 302]
      ssl_min_days: 14
"""


def find_project_file(start: Path | None = None) -> Path | None:
    root = start or Path.cwd()
    for name in PROJECT_FILENAMES:
        path = root / name
        if path.exists():
            return path
    return None


def _parse_yaml(text: str) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as error:
        raise RuntimeError(
            "PyYAML is required to read sentinel.yaml. Install devops-sentinel-next or use sentinel.json."
        ) from error
    loaded = yaml.safe_load(text) or {}
    if not isinstance(loaded, dict):
        raise ValueError("Project file must be a mapping")
    return loaded


def load_project_config(path: Path | None = None) -> dict[str, Any]:
    file_path = path or find_project_file()
    if file_path is None:
        return {"services": [], "path": None}
    text = file_path.read_text(encoding="utf-8")
    if file_path.suffix == ".json":
        data = json.loads(text)
    else:
        data = _parse_yaml(text)
    services = data.get("services") or []
    if not isinstance(services, list):
        raise ValueError("services must be a list")
    normalized = []
    for item in services:
        if not isinstance(item, dict) or not item.get("url"):
            continue
        normalized.append(
            {
                "name": str(item.get("name") or item["url"]),
                "url": str(item["url"]),
                "interval": int(item.get("interval") or item.get("check_interval") or 30),
                "failure_threshold": int(item.get("failure_threshold") or 3),
                "recovery_threshold": int(item.get("recovery_threshold") or 2),
                "expect": HealthExpect.from_mapping(item.get("expect") or {}),
            }
        )
    return {"services": normalized, "path": str(file_path)}


def write_sample_project_file(directory: Path | None = None) -> Path:
    path = (directory or Path.cwd()) / "sentinel.yaml"
    if not path.exists():
        path.write_text(SAMPLE_YAML, encoding="utf-8")
    return path


def expect_for_url(config: dict[str, Any], url: str, name: str | None = None) -> HealthExpect:
    for item in config.get("services") or []:
        if item.get("url") == url or item.get("name") == name:
            expect = item.get("expect")
            return expect if isinstance(expect, HealthExpect) else HealthExpect()
    return HealthExpect()
