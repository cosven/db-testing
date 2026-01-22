#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import click
import requests


DEFAULT_CLUSTER_API = "http://cluster-api.example.com/api/v1/cluster"
DEFAULT_MYSQL_PORT = 9030


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


def extract_clusters(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "result", "clusters", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                for inner_key in ("clusters", "items", "data", "result"):
                    inner = value.get(inner_key)
                    if isinstance(inner, list):
                        return [item for item in inner if isinstance(item, dict)]
        for value in payload.values():
            if isinstance(value, list) and value and all(
                isinstance(item, dict) for item in value
            ):
                return value
    return []


def resolve_value(
    value: Optional[str],
    env_key: str,
    default: Optional[str] = None,
    required: bool = False,
) -> str:
    resolved = value
    if resolved in (None, ""):
        resolved = os.getenv(env_key, default or "")
    if required and not resolved:
        raise click.UsageError(f"Missing required value for {env_key}.")
    return resolved


def get_cluster_name(cluster: Dict[str, Any]) -> Optional[str]:
    for key in ("name", "cluster_name", "clusterName"):
        value = cluster.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def find_cluster(clusters: Sequence[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    for cluster in clusters:
        if get_cluster_name(cluster) == name:
            return cluster
    return None


def extract_fe_value(cluster: Dict[str, Any]) -> Any:
    for key in (
        "fe_addr",
        "feAddr",
        "fe_address",
        "feAddress",
        "fe",
        "fe_host",
        "feHost",
        "fe_endpoint",
        "feEndpoint",
    ):
        value = cluster.get(key)
        if value:
            return value

    for key in (
        "fe_list",
        "feList",
        "fes",
        "fe_nodes",
        "feNodes",
        "frontends",
        "frontend",
    ):
        value = cluster.get(key)
        if isinstance(value, dict):
            for inner_key in ("items", "list", "nodes"):
                inner = value.get(inner_key)
                if inner:
                    return inner
        if value:
            return value
    return None


def parse_host_port(value: Any, default_port: int) -> Optional[Tuple[str, int]]:
    if value is None:
        return None
    if isinstance(value, list) and value:
        return parse_host_port(value[0], default_port)
    if isinstance(value, dict):
        host = (
            value.get("host")
            or value.get("ip")
            or value.get("address")
            or value.get("hostname")
        )
        port = (
            value.get("port")
            or value.get("mysql_port")
            or value.get("query_port")
            or value.get("queryPort")
        )
        if host:
            return host, int(port) if port else default_port
    if isinstance(value, str):
        addr = value.strip()
        for prefix in ("http://", "https://", "mysql://"):
            if addr.startswith(prefix):
                addr = addr[len(prefix) :]
        addr = addr.split("/", 1)[0]
        if "," in addr:
            addr = addr.split(",", 1)[0]
        if ":" in addr:
            host, port_str = addr.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                port = default_port
        else:
            host = addr
            port = default_port
        if host:
            return host, port
    return None


def normalize_items(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("items", "list", "nodes"):
            inner = value.get(key)
            if inner:
                return normalize_items(inner)
        return [value]
    if isinstance(value, str):
        parts = [item.strip() for item in value.split(",") if item.strip()]
        return parts or [value]
    return [value]


def collect_host_ports(cluster: Dict[str, Any], default_port: int) -> List[Tuple[str, int]]:
    items: List[Any] = []

    nodes = cluster.get("nodes")
    if isinstance(nodes, list):
        for node in nodes:
            if not isinstance(node, dict):
                continue
            roles = node.get("role") or node.get("roles")
            if isinstance(roles, str):
                roles = [roles]
            if isinstance(roles, list):
                role_names = {str(role).lower() for role in roles}
                if any(
                    role in role_names
                    for role in ("fe", "femaster", "frontend", "frontend".lower())
                ):
                    host = (
                        node.get("IP")
                        or node.get("ip")
                        or node.get("host")
                        or node.get("hostname")
                    )
                    port = (
                        node.get("queryPort")
                        or node.get("query_port")
                        or node.get("mysql_port")
                        or node.get("port")
                    )
                    if host:
                        items.append({"host": host, "port": port or default_port})

    fe_value = extract_fe_value(cluster)
    for item in normalize_items(fe_value):
        items.append(item)

    host_ports: List[Tuple[str, int]] = []
    seen = set()
    for item in items:
        parsed = parse_host_port(item, default_port)
        if not parsed:
            continue
        if parsed in seen:
            continue
        seen.add(parsed)
        host_ports.append(parsed)
    return host_ports


def fetch_clusters(cluster_api_url: str, timeout: int) -> List[Dict[str, Any]]:
    resp = requests.get(cluster_api_url, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    return extract_clusters(payload)


@click.command(help="Fetch FE info from Doris cluster API")
@click.option(
    "--cluster-name",
    required=True,
    help="Cluster name to match from the cluster API",
)
@click.option(
    "--cluster-api",
    default=None,
    help="Cluster API URL (or DORIS_CLUSTER_API_URL)",
)
@click.option(
    "--env-file",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path(".env"),
    show_default=True,
    help="Env file to load for defaults",
)
@click.option(
    "--output",
    type=click.Choice(["raw", "hostport", "cluster"], case_sensitive=False),
    default="raw",
    show_default=True,
    help="Output format: raw FE data, normalized host:port, or full cluster JSON",
)
@click.option(
    "--timeout",
    type=int,
    default=10,
    show_default=True,
    help="Timeout seconds for HTTP",
)
def main(
    cluster_name: str,
    cluster_api: str,
    env_file: Path,
    output: str,
    timeout: int,
) -> int:
    load_env_file(env_file)

    resolved_cluster_api = resolve_value(
        cluster_api, "DORIS_CLUSTER_API_URL", default=DEFAULT_CLUSTER_API, required=True
    )

    try:
        clusters = fetch_clusters(resolved_cluster_api, timeout)
    except requests.RequestException as exc:
        click.echo(f"Failed to fetch clusters: {exc}", err=True)
        return 2
    if not clusters:
        click.echo("No clusters returned by the cluster API.", err=True)
        return 1

    cluster = find_cluster(clusters, cluster_name)
    if not cluster:
        names = sorted(
            name for name in (get_cluster_name(c) for c in clusters) if name
        )
        click.echo(
            "Cluster not found. Available: " + ", ".join(names) if names else
            "Cluster not found and no names available.",
            err=True,
        )
        return 1

    output = output.lower()
    if output == "cluster":
        click.echo(json.dumps(cluster, ensure_ascii=True, indent=2))
        return 0

    fe_value = extract_fe_value(cluster)
    if fe_value is None and output == "raw":
        click.echo("FE data not found in cluster payload.", err=True)
        return 1

    if output == "raw":
        if isinstance(fe_value, (dict, list)):
            click.echo(json.dumps(fe_value, ensure_ascii=True, indent=2))
        else:
            click.echo("" if fe_value is None else str(fe_value))
        return 0

    host_ports = collect_host_ports(cluster, DEFAULT_MYSQL_PORT)
    if not host_ports:
        click.echo("Failed to resolve FE host:port from cluster payload.", err=True)
        return 1
    for host, port in host_ports:
        click.echo(f"{host}:{port}")
    return 0


if __name__ == "__main__":
    sys.exit(main(standalone_mode=False))
