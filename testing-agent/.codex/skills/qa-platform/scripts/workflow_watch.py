#!/usr/bin/env python3
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _common import (  # noqa: E402
    DEFAULT_TIMEOUT,
    DEFAULT_TOKEN_HEADER,
    build_headers,
    load_env_file,
    parse_json,
    resolve_value,
    write_output,
)

DEFAULT_INTERVAL = 10
TERMINAL_PHASES = {"succeeded", "failed", "error", "cancelled"}


def extract_phase(payload: Any) -> Tuple[str, str]:
    if not isinstance(payload, dict):
        return "", ""
    data = payload.get("data")
    if not isinstance(data, dict):
        return "", ""
    status = data.get("status")
    if not isinstance(status, dict):
        return "", ""
    phase = status.get("phase") or ""
    message = status.get("message") or ""
    return str(phase), str(message)


def append_log(path: Optional[str], line: str) -> None:
    if not path:
        return
    Path(path).open("a", encoding="utf-8").write(line + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch QA platform workflow status.")
    parser.add_argument("--uid", required=True, help="workflow uid")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="poll interval seconds")
    parser.add_argument("--timeout", type=int, default=None, help="request timeout seconds")
    parser.add_argument("--max-wait", type=int, default=None, help="max wait seconds")
    parser.add_argument("--max-errors", type=int, default=3, help="max consecutive errors before exit")
    parser.add_argument("--base-url", default=None, help="QA platform base URL")
    parser.add_argument("--env-file", default=".env", help="env file path")
    parser.add_argument("--token", default=None, help="auth token")
    parser.add_argument("--token-header", default=None, help="auth header name")
    parser.add_argument("--output", default=None, help="write last response to file")
    parser.add_argument("--log-file", default=None, help="append status lines to log file")
    parser.add_argument("--once", action="store_true", help="fetch once and exit")
    args = parser.parse_args()

    load_env_file(Path(args.env_file))
    base_url = resolve_value(args.base_url, "QA_PLATFORM_URL")
    if not base_url:
        raise SystemExit("missing QA_PLATFORM_URL")

    token = resolve_value(args.token, "QA_PLATFORM_TOKEN")
    token_header = resolve_value(args.token_header, "QA_PLATFORM_TOKEN_HEADER", DEFAULT_TOKEN_HEADER)
    timeout = args.timeout or int(resolve_value(None, "QA_PLATFORM_TIMEOUT", str(DEFAULT_TIMEOUT)))

    headers = build_headers(token, token_header)

    endpoint = f"{base_url.rstrip('/')}/api/v1/workflow/{args.uid}"

    start = time.time()
    error_count = 0
    while True:
        try:
            resp = requests.get(endpoint, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            error_count += 1
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            line = f"{ts} ERROR {exc}"
            print(line, flush=True)
            append_log(args.log_file, line)
            if error_count >= args.max_errors:
                return 1
            time.sleep(args.interval)
            continue

        payload = parse_json(resp.text)
        formatted = (
            json.dumps(payload, ensure_ascii=False, indent=2)
            if not isinstance(payload, str)
            else payload
        )
        write_output(args.output, formatted)

        phase, message = extract_phase(payload)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts} HTTP={resp.status_code} phase={phase or 'unknown'}"
        if message:
            line += f" message={message}"
        print(line, flush=True)
        append_log(args.log_file, line)

        if resp.status_code >= 400:
            error_count += 1
            if error_count >= args.max_errors:
                return 1
        else:
            error_count = 0

        if args.once:
            return 0
        if phase.lower() in TERMINAL_PHASES:
            return 0
        if args.max_wait and (time.time() - start) >= args.max_wait:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
