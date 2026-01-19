#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import click
import pymysql
import requests


DEFAULT_CLUSTER_API = "http://172.20.48.32:8111/api/v1/cluster"
DEFAULT_MYSQL_PORT = 9030


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


def resolve_fe_host_port(cluster: Dict[str, Any], default_port: int) -> Optional[Tuple[str, int]]:
    product_info = cluster.get("productInfo")
    if isinstance(product_info, dict):
        query_host = product_info.get("queryHost") or product_info.get("query_host")
        query_port = product_info.get("queryPort") or product_info.get("query_port")
        if isinstance(query_host, str) and query_host:
            port = int(query_port) if query_port else default_port
            return query_host, port

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
                    for role in ("fe", "femaster", "frontend", "frontEnd".lower())
                ):
                    host = (
                        node.get("IP")
                        or node.get("ip")
                        or node.get("host")
                        or node.get("hostname")
                    )
                    if host:
                        return str(host), default_port

    fe_value = extract_fe_value(cluster)
    return parse_host_port(fe_value, default_port)


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
        port = value.get("port") or value.get("mysql_port") or value.get("query_port")
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


def fetch_clusters(cluster_api_url: str, timeout: int) -> List[Dict[str, Any]]:
    resp = requests.get(cluster_api_url, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    return extract_clusters(payload)


def load_sql(sql_items: Iterable[str], sql_file: Optional[Path]) -> List[str]:
    statements = [item.strip() for item in sql_items if item.strip()]
    if sql_file:
        text = sql_file.read_text(encoding="utf-8")
        for item in text.split(";"):
            item = item.strip()
            if item:
                statements.append(item)
    return statements


def print_rows(columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    click.echo("\t".join(columns))
    for row in rows:
        formatted = [
            "NULL" if value is None else str(value) for value in row
        ]
        click.echo("\t".join(formatted))


@click.command(help="Fetch Doris cluster FE and run SQL via MySQL")
@click.option(
    "--cluster-name",
    required=True,
    help="Cluster name to match from the cluster API",
)
@click.option(
    "--cluster-api",
    default=DEFAULT_CLUSTER_API,
    show_default=True,
    help="Cluster API URL",
)
@click.option(
    "--user",
    default="root",
    show_default=True,
    help="MySQL user",
)
@click.option(
    "--password",
    default="",
    help="MySQL password",
)
@click.option(
    "--database",
    default="",
    help="Default database to use",
)
@click.option(
    "--port",
    type=int,
    default=None,
    help="Override FE MySQL port",
)
@click.option(
    "--sql",
    "sql_items",
    multiple=True,
    help="SQL to execute, repeatable",
)
@click.option(
    "--sql-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="SQL file to execute (split by semicolon)",
)
@click.option(
    "--timeout",
    type=int,
    default=10,
    show_default=True,
    help="Timeout seconds for HTTP/MySQL",
)
def main(
    cluster_name: str,
    cluster_api: str,
    user: str,
    password: str,
    database: str,
    port: Optional[int],
    sql_items: Sequence[str],
    sql_file: Optional[Path],
    timeout: int,
) -> int:
    statements = load_sql(sql_items, sql_file)
    if not statements:
        click.echo("No SQL provided. Use --sql and/or --sql-file.", err=True)
        return 2

    try:
        clusters = fetch_clusters(cluster_api, timeout)
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

    host_port = resolve_fe_host_port(cluster, DEFAULT_MYSQL_PORT)
    if not host_port:
        click.echo("Failed to resolve FE address from cluster details.", err=True)
        return 1
    host, resolved_port = host_port
    if port:
        resolved_port = port

    click.echo(f"Using FE: {host}:{resolved_port}", err=True)

    try:
        conn = pymysql.connect(
            host=host,
            port=resolved_port,
            user=user,
            password=password,
            database=database or None,
            connect_timeout=timeout,
            read_timeout=timeout,
            write_timeout=timeout,
            autocommit=True,
        )
    except pymysql.MySQLError as exc:
        click.echo(f"Failed to connect to MySQL: {exc}", err=True)
        return 2

    try:
        with conn.cursor() as cursor:
            for stmt in statements:
                try:
                    cursor.execute(stmt)
                except pymysql.MySQLError as exc:
                    click.echo(f"SQL failed: {exc}", err=True)
                    return 1

                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    print_rows(columns, rows)
                else:
                    rowcount = cursor.rowcount
                    click.echo(f"OK ({rowcount} rows affected)")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main(standalone_mode=False))
