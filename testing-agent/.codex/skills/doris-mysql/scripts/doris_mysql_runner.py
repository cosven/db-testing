#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence

import click
import pymysql


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


def resolve_port(value: Optional[int], env_key: str, default: int) -> int:
    if value is not None:
        return value
    env_value = os.getenv(env_key, "")
    if env_value:
        try:
            return int(env_value)
        except ValueError as exc:
            raise click.UsageError(f"Invalid {env_key}: {env_value}") from exc
    return default


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
        formatted = ["NULL" if value is None else str(value) for value in row]
        click.echo("\t".join(formatted))


@click.command(help="Run SQL against Doris FE via MySQL protocol")
@click.option(
    "--env-file",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path(".env"),
    show_default=True,
    help="Env file to load for defaults",
)
@click.option("--host", default=None, help="FE host (or DORIS_HOST)")
@click.option("--port", type=int, default=None, help="FE MySQL port (or DORIS_PORT)")
@click.option("--user", default=None, help="MySQL user (or DORIS_USER)")
@click.option("--password", default=None, help="MySQL password (or DORIS_PASSWORD)")
@click.option("--database", default=None, help="Default database (or DORIS_DATABASE)")
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
    help="Timeout seconds for MySQL",
)
def main(
    env_file: Path,
    host: Optional[str],
    port: Optional[int],
    user: Optional[str],
    password: Optional[str],
    database: Optional[str],
    sql_items: Sequence[str],
    sql_file: Optional[Path],
    timeout: int,
) -> int:
    load_env_file(env_file)

    statements = load_sql(sql_items, sql_file)
    if not statements:
        click.echo("No SQL provided. Use --sql and/or --sql-file.", err=True)
        return 2

    resolved_host = resolve_value(host, "DORIS_HOST", required=True)
    resolved_port = resolve_port(port, "DORIS_PORT", DEFAULT_MYSQL_PORT)
    resolved_user = resolve_value(user, "DORIS_USER", default="root")
    resolved_password = resolve_value(password, "DORIS_PASSWORD")
    resolved_database = resolve_value(database, "DORIS_DATABASE")

    try:
        conn = pymysql.connect(
            host=resolved_host,
            port=resolved_port,
            user=resolved_user,
            password=resolved_password,
            database=resolved_database or None,
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
