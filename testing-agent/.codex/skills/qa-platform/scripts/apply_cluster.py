#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click
import requests

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _common import (  # noqa: E402
    DEFAULT_TIMEOUT,
    DEFAULT_TOKEN_HEADER,
    build_headers,
    format_response,
    load_env_file,
    mask_sensitive,
    resolve_value,
    write_output,
)

def load_payload(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Payload JSON 解析失败: {exc}") from exc


def pick_endpoint(payload: Dict[str, Any], endpoint_mode: str) -> str:
    if endpoint_mode == "apply":
        return "/api/v1/cluster/apply"
    if endpoint_mode == "custom":
        return "/api/v1/cluster/custom"
    # auto
    if "FESpecs" in payload or "BESpecs" in payload:
        return "/api/v1/cluster/custom"
    return "/api/v1/cluster/apply"


@click.command()
@click.option("--payload", "payload_path", type=click.Path(exists=True, dir_okay=False), required=True)
@click.option("--base-url", default=None, help="QA 平台 Performance 服务 base URL")
@click.option("--env-file", default=".env", show_default=True)
@click.option("--token", default=None, help="可选鉴权 token")
@click.option("--token-header", default=None, help="可选鉴权 header 名")
@click.option("--timeout", default=None, type=int, help="请求超时秒数")
@click.option("--output", "output_path", default=None, help="响应保存路径")
@click.option("--dry-run", is_flag=True, help="仅打印请求信息，不发送")
@click.option(
    "--endpoint",
    type=click.Choice(["auto", "apply", "custom"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="强制指定接口类型",
)
@click.option(
    "--fail-on-non-2xx/--no-fail-on-non-2xx",
    default=True,
    show_default=True,
    help="非 2xx 响应时返回非零退出码",
)
def main(
    payload_path: str,
    base_url: Optional[str],
    env_file: str,
    token: Optional[str],
    token_header: Optional[str],
    timeout: Optional[int],
    output_path: Optional[str],
    dry_run: bool,
    endpoint: str,
    fail_on_non_2xx: bool,
) -> None:
    env_path = Path(env_file)
    load_env_file(env_path)

    base_url = resolve_value(base_url, "QA_PLATFORM_URL")
    if not base_url:
        raise click.ClickException("缺少 QA_PLATFORM_URL，请通过 --base-url 或 .env 提供")

    token = resolve_value(token, "QA_PLATFORM_TOKEN")
    token_header = resolve_value(token_header, "QA_PLATFORM_TOKEN_HEADER", DEFAULT_TOKEN_HEADER)
    timeout_value = timeout or int(resolve_value(None, "QA_PLATFORM_TIMEOUT", str(DEFAULT_TIMEOUT)))

    payload = load_payload(Path(payload_path))
    endpoint = f"{base_url.rstrip('/')}{pick_endpoint(payload, endpoint.lower())}"

    headers: Dict[str, str] = build_headers(token, token_header)

    if dry_run:
        safe_headers = headers.copy()
        if token:
            safe_headers[token_header] = mask_sensitive(token)
        click.echo("[dry-run] POST " + endpoint)
        click.echo("[dry-run] headers: " + json.dumps(safe_headers, ensure_ascii=False))
        click.echo("[dry-run] payload: " + json.dumps(payload, ensure_ascii=False, indent=2))
        return

    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=timeout_value)
    except requests.RequestException as exc:
        raise click.ClickException(f"请求失败: {exc}") from exc

    body = format_response(resp)
    write_output(output_path, body)

    click.echo(f"HTTP {resp.status_code}")
    click.echo(body)
    if resp.status_code >= 400 and fail_on_non_2xx:
        raise click.ClickException(f"HTTP {resp.status_code}")


if __name__ == "__main__":
    sys.exit(main())
