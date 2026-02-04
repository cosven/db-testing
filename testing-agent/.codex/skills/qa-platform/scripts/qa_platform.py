#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

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
    parse_json,
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
    if "FESpecs" in payload or "BESpecs" in payload:
        return "/api/v1/cluster/custom"
    return "/api/v1/cluster/apply"


def request_api(
    ctx: Dict[str, Any],
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, str]] = None,
    require_confirm: bool = False,
    confirmed: bool = False,
) -> Tuple[int, str]:
    endpoint = f"{ctx['base_url']}{path}"

    if ctx["dry_run"]:
        safe_headers = ctx["headers"].copy()
        if ctx["token"]:
            safe_headers[ctx["token_header"]] = mask_sensitive(ctx["token"])
        click.echo(f"[dry-run] {method} {endpoint}")
        click.echo("[dry-run] headers: " + json.dumps(safe_headers, ensure_ascii=False))
        if params:
            click.echo("[dry-run] params: " + json.dumps(params, ensure_ascii=False))
        if payload is not None:
            click.echo("[dry-run] payload: " + json.dumps(payload, ensure_ascii=False, indent=2))
        return 0, ""

    if require_confirm and not confirmed:
        raise click.ClickException("该操作会变更集群状态，请使用 --confirm 明确确认。")

    try:
        resp = requests.request(
            method,
            endpoint,
            json=payload,
            params=params,
            headers=ctx["headers"],
            timeout=ctx["timeout"],
        )
    except requests.RequestException as exc:
        raise click.ClickException(f"请求失败: {exc}") from exc

    body = format_response(resp)
    write_output(ctx["output"], body)
    return resp.status_code, body


def maybe_fail(ctx: Dict[str, Any], status_code: int) -> None:
    if status_code >= 400 and ctx.get("fail_on_non_2xx", True):
        raise click.ClickException(f"HTTP {status_code}")


@click.group()
@click.option("--base-url", default=None, help="QA 平台 Performance 服务 base URL")
@click.option("--env-file", default=".env", show_default=True)
@click.option("--token", default=None, help="可选鉴权 token")
@click.option("--token-header", default=None, help="可选鉴权 header 名")
@click.option("--timeout", default=None, type=int, help="请求超时秒数")
@click.option("--output", "output_path", default=None, help="响应保存路径")
@click.option("--dry-run", is_flag=True, help="仅打印请求信息，不发送")
@click.option(
    "--fail-on-non-2xx/--no-fail-on-non-2xx",
    default=True,
    show_default=True,
    help="非 2xx 响应时返回非零退出码",
)
@click.pass_context
def cli(
    ctx: click.Context,
    base_url: Optional[str],
    env_file: str,
    token: Optional[str],
    token_header: Optional[str],
    timeout: Optional[int],
    output_path: Optional[str],
    dry_run: bool,
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

    ctx.obj = {
        "base_url": base_url.rstrip("/"),
        "headers": build_headers(token, token_header),
        "timeout": timeout_value,
        "output": output_path,
        "dry_run": dry_run,
        "token": token,
        "token_header": token_header,
        "fail_on_non_2xx": fail_on_non_2xx,
    }


@cli.command("apply")
@click.option("--payload", "payload_path", type=click.Path(exists=True, dir_okay=False), required=True)
@click.option(
    "--endpoint",
    type=click.Choice(["auto", "apply", "custom"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="强制指定接口类型",
)
@click.pass_context
def apply_cluster(ctx: click.Context, payload_path: str, endpoint: str) -> None:
    payload = load_payload(Path(payload_path))
    endpoint_path = pick_endpoint(payload, endpoint.lower())
    status_code, body = request_api(ctx.obj, "POST", endpoint_path, payload=payload)
    if status_code:
        click.echo(f"HTTP {status_code}")
        click.echo(body)
    maybe_fail(ctx.obj, status_code)


@cli.command("list")
@click.option("--param", "params", multiple=True, help="查询参数，格式 key=value，可多次指定")
@click.option("--name", default=None, help="按 name 精确过滤")
@click.option("--user", default=None, help="按 user 精确过滤")
@click.option("--status", default=None, help="按 status 精确过滤")
@click.pass_context
def list_clusters(
    ctx: click.Context,
    params: Tuple[str, ...],
    name: Optional[str],
    user: Optional[str],
    status: Optional[str],
) -> None:
    query: Dict[str, str] = {}
    for item in params:
        if "=" not in item:
            raise click.ClickException(f"参数格式应为 key=value: {item}")
        key, value = item.split("=", 1)
        query[key] = value

    status_code, body = request_api(ctx.obj, "GET", "/api/v1/cluster", params=query)
    if status_code:
        click.echo(f"HTTP {status_code}")
        payload = parse_json(body)
        if any((name, user, status)) and isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, list):
                filtered = []
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    if name and item.get("name") != name:
                        continue
                    if user and item.get("user") != user:
                        continue
                    if status and item.get("status") != status:
                        continue
                    filtered.append(item)
                payload["data"] = filtered
                payload["count"] = len(filtered)
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
    maybe_fail(ctx.obj, status_code)


@cli.command("get")
@click.option("--name", "cluster_name", required=True, help="集群名")
@click.pass_context
def get_cluster(ctx: click.Context, cluster_name: str) -> None:
    status, body = request_api(ctx.obj, "GET", f"/api/v1/cluster/{cluster_name}")
    if status:
        click.echo(f"HTTP {status}")
        click.echo(body)
    maybe_fail(ctx.obj, status)


@cli.command("update-ttl")
@click.option("--name", "cluster_name", required=True, help="集群名")
@click.option("--payload", "payload_path", type=click.Path(exists=True, dir_okay=False), default=None)
@click.option("--estimated-release-at", default=None, help="ISO8601 时间字符串")
@click.option("--confirm", is_flag=True, help="确认执行变更")
@click.pass_context
def update_ttl(
    ctx: click.Context,
    cluster_name: str,
    payload_path: Optional[str],
    estimated_release_at: Optional[str],
    confirm: bool,
) -> None:
    if payload_path:
        payload = load_payload(Path(payload_path))
    elif estimated_release_at:
        payload = {"estimated_release_at": estimated_release_at}
    else:
        raise click.ClickException("需要提供 --payload 或 --estimated-release-at")

    status, body = request_api(
        ctx.obj,
        "PUT",
        f"/api/v1/cluster/{cluster_name}",
        payload=payload,
        require_confirm=True,
        confirmed=confirm,
    )
    if status:
        click.echo(f"HTTP {status}")
        click.echo(body)
    maybe_fail(ctx.obj, status)


@cli.command("power-on")
@click.option("--name", "cluster_name", required=True, help="集群名")
@click.option("--confirm", is_flag=True, help="确认执行变更")
@click.pass_context
def power_on(ctx: click.Context, cluster_name: str, confirm: bool) -> None:
    status, body = request_api(
        ctx.obj,
        "POST",
        f"/api/v1/cluster/power-on/{cluster_name}",
        require_confirm=True,
        confirmed=confirm,
    )
    if status:
        click.echo(f"HTTP {status}")
        click.echo(body)
    maybe_fail(ctx.obj, status)


@cli.command("power-off")
@click.option("--name", "cluster_name", required=True, help="集群名")
@click.option("--confirm", is_flag=True, help="确认执行变更")
@click.pass_context
def power_off(ctx: click.Context, cluster_name: str, confirm: bool) -> None:
    status, body = request_api(
        ctx.obj,
        "POST",
        f"/api/v1/cluster/power-off/{cluster_name}",
        require_confirm=True,
        confirmed=confirm,
    )
    if status:
        click.echo(f"HTTP {status}")
        click.echo(body)
    maybe_fail(ctx.obj, status)


@cli.command("start")
@click.option("--name", "cluster_name", required=True, help="集群名")
@click.option("--confirm", is_flag=True, help="确认执行变更")
@click.pass_context
def start_cluster(ctx: click.Context, cluster_name: str, confirm: bool) -> None:
    status, body = request_api(
        ctx.obj,
        "POST",
        f"/api/v1/cluster/start/{cluster_name}",
        require_confirm=True,
        confirmed=confirm,
    )
    if status:
        click.echo(f"HTTP {status}")
        click.echo(body)
    maybe_fail(ctx.obj, status)


@cli.command("stop")
@click.option("--name", "cluster_name", required=True, help="集群名")
@click.option("--confirm", is_flag=True, help="确认执行变更")
@click.pass_context
def stop_cluster(ctx: click.Context, cluster_name: str, confirm: bool) -> None:
    status, body = request_api(
        ctx.obj,
        "POST",
        f"/api/v1/cluster/stop/{cluster_name}",
        require_confirm=True,
        confirmed=confirm,
    )
    if status:
        click.echo(f"HTTP {status}")
        click.echo(body)
    maybe_fail(ctx.obj, status)


@cli.command("release")
@click.option("--name", "cluster_name", required=True, help="集群名")
@click.option("--confirm", is_flag=True, help="确认执行变更")
@click.pass_context
def release_cluster(ctx: click.Context, cluster_name: str, confirm: bool) -> None:
    status, body = request_api(
        ctx.obj,
        "DELETE",
        f"/api/v1/cluster/release/{cluster_name}",
        require_confirm=True,
        confirmed=confirm,
    )
    if status:
        click.echo(f"HTTP {status}")
        click.echo(body)
    maybe_fail(ctx.obj, status)


if __name__ == "__main__":
    sys.exit(cli())
