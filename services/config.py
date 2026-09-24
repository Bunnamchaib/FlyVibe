from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .paths import config_path


def default_config() -> dict[str, Any]:
    return {
        "app": {
            "name": "LOCAL VOICE",
            "subtitle": "Private WebRTC Voice Server",
            "version": "0.1.0",
        },
        "debug": False,
        "server": {
            "host": "0.0.0.0",
            "port": 4545,
        },
        "room": {
            "name": "Home",
            "capacity": 6,
            "requireInvitationToken": True,
        },
        "webrtc": {
            "iceServers": [
                {
                    "urls": ["stun:stun.l.google.com:19302"],
                }
            ],
        },
        "turn": {
            "enabled": False,
            "urls": ["turn:turn.example.com:3478"],
            "username": "",
            "credential": "",
        },
        "cloudflare": {
            "path": "",
        },
        "ui": {
            "autoCopyPublicUrl": False,
            "autoOpenBrowser": False,
        },
    }


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    target = Path(path) if path is not None else config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    defaults = default_config()
    if not target.exists():
        save_config(defaults, target)
        return defaults
    try:
        loaded = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = target.with_suffix(".broken.json")
        target.replace(backup)
        save_config(defaults, target)
        return defaults
    config = deep_merge(defaults, loaded)
    save_config(config, target)
    return config


def save_config(config: dict[str, Any], path: str | Path | None = None) -> None:
    target = Path(path) if path is not None else config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

