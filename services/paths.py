from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def resource_path(*parts: str) -> Path:
    root = app_root()
    candidate = root.joinpath(*parts)
    if candidate.exists():
        return candidate
    bundle_root = Path(getattr(sys, "_MEIPASS", root))
    return bundle_root.joinpath(*parts)


def config_path() -> Path:
    return app_root() / "config" / "config.json"


def web_dir() -> Path:
    return resource_path("web")


def cloudflared_path(config: dict | None = None) -> Path:
    configured = ""
    if config:
        configured = str(config.get("cloudflare", {}).get("path", "")).strip()
    if configured:
        return Path(configured)
    return app_root() / "cloudflared.exe"

