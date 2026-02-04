#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests

DEFAULT_TIMEOUT = 30
DEFAULT_TOKEN_HEADER = "Authorization"


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def resolve_value(value: Optional[str], env_key: str, default: Optional[str] = None) -> str:
    resolved = value
    if resolved in (None, ""):
        resolved = os.getenv(env_key, default or "")
    return resolved or ""


def mask_sensitive(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "***"
    return f"{value[:2]}***{value[-2:]}"


def build_headers(token: str, token_header: str) -> Dict[str, str]:
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if token:
        headers[token_header] = token
    return headers


def format_response(resp: requests.Response) -> str:
    try:
        data = resp.json()
    except ValueError:
        return resp.text
    return json.dumps(data, ensure_ascii=False, indent=2)


def write_output(path: Optional[str], body: str) -> None:
    if not path:
        return
    Path(path).write_text(body, encoding="utf-8")


def parse_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}
