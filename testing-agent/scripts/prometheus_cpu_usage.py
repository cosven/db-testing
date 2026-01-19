#!/usr/bin/env python3
import json
import sys

import click
import requests


PROMETHEUS_URL_DEFAULT = "http://172.20.48.32:9090"
PROMQL_TEMPLATE = (
    "((sum(rate(doris_be_cpu{job=\"$be_cluster_id\"}[$interval])) by (job, instance)) - "
    "(sum(rate(doris_be_cpu{mode=\"idle\", job=\"$be_cluster_id\"}[$interval])) by (job, instance)) - "
    "(sum(rate(doris_be_cpu{mode=\"iowait\", job=\"$be_cluster_id\"}[$interval])) by (job, instance))) / "
    "(sum(rate(doris_be_cpu{job=\"$be_cluster_id\"}[$interval])) by (job, instance)) * 100"
)


def build_promql(be_cluster_id: str, interval: str) -> str:
    return (
        PROMQL_TEMPLATE.replace("$be_cluster_id", be_cluster_id)
        .replace("$interval", interval)
    )


def query_prometheus(prometheus_url: str, promql: str) -> dict:
    query_url = prometheus_url.rstrip("/") + "/api/v1/query"
    resp = requests.get(query_url, params={"query": promql}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def print_vector_result(result: dict) -> int:
    data = result.get("data", {})
    if data.get("resultType") != "vector":
        click.echo(json.dumps(result, indent=2, ensure_ascii=True))
        return 1

    rows = data.get("result", [])
    if not rows:
        click.echo("没有返回数据。")
        return 0

    click.echo("job\tinstance\tvalue\ttimestamp")
    for item in rows:
        metric = item.get("metric", {})
        value = item.get("value", [])
        ts = value[0] if len(value) > 0 else ""
        val = value[1] if len(value) > 1 else ""
        click.echo(f"{metric.get('job','')}\t{metric.get('instance','')}\t{val}\t{ts}")
    return 0


@click.command(help="查询 Prometheus 并获取测试集群 CPU 使用率")
@click.option(
    "--be-cluster-id",
    required=True,
    help="BE 集群 ID，映射到 PromQL 中的 job",
)
@click.option(
    "--interval",
    default="1m",
    show_default=True,
    help="PromQL 里的区间变量，比如 1m/5m/10s/1h",
)
@click.option(
    "--prometheus-url",
    default=PROMETHEUS_URL_DEFAULT,
    show_default=True,
    help="Prometheus 地址",
)
@click.option(
    "--print-promql",
    is_flag=True,
    help="打印最终的 PromQL",
)
@click.option(
    "--debug",
    is_flag=True,
    help="打印 Prometheus 返回的原始 JSON",
)
def main(
    be_cluster_id: str,
    interval: str,
    prometheus_url: str,
    print_promql: bool,
    debug: bool,
) -> int:
    promql = build_promql(be_cluster_id, interval)
    if print_promql:
        click.echo(f"PROMQL: {promql}")
    try:
        result = query_prometheus(prometheus_url, promql)
    except requests.RequestException as exc:
        click.echo(f"请求 Prometheus 失败: {exc}", err=True)
        return 2

    if result.get("status") != "success":
        click.echo(json.dumps(result, indent=2, ensure_ascii=True))
        return 1

    if debug:
        click.echo(json.dumps(result, indent=2, ensure_ascii=True), err=True)

    return print_vector_result(result)


if __name__ == "__main__":
    sys.exit(main(standalone_mode=False))
