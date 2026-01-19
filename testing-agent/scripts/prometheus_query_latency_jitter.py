#!/usr/bin/env python3
import json
import math
import sys
import time

import click
import requests

from prometheus_common import PROMETHEUS_URL_DEFAULT, query_prometheus_range


PROMQL_TEMPLATE = (
    "sum(doris_fe_query_latency_ms_sum{job=\"$fe_cluster_id\"}) by (instance) / "
    "sum(doris_fe_query_latency_ms_count{job=\"$fe_cluster_id\"}) by (instance)"
)


def build_promql(fe_cluster_id: str) -> str:
    return PROMQL_TEMPLATE.replace("$fe_cluster_id", fe_cluster_id)


def ts_to_local(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def parse_values(raw_values):
    parsed = []
    for ts_str, val_str in raw_values:
        try:
            v = float(val_str)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(v):
            continue
        parsed.append((float(ts_str), v))
    return parsed


def find_max_jump(series):
    best = None
    for item in series:
        metric = item.get("metric", {})
        instance = metric.get("instance", "")
        values = parse_values(item.get("values", []))
        prev_ts, prev_v = None, None
        for ts, v in values:
            if prev_v is not None:
                delta = abs(v - prev_v)
                if best is None or delta > best["delta"]:
                    best = {
                        "instance": instance,
                        "delta": delta,
                        "ts": ts,
                        "prev_ts": prev_ts,
                        "prev_v": prev_v,
                        "v": v,
                    }
            prev_ts, prev_v = ts, v
    return best


@click.command(help="Find the max jitter point for FE query latency")
@click.option(
    "--fe-cluster-id",
    required=True,
    help="FE cluster ID mapped to PromQL job",
)
@click.option(
    "--window-seconds",
    default=7200,
    show_default=True,
    type=click.IntRange(1, None),
    help="Query window in seconds (ignored if --start is provided)",
)
@click.option(
    "--step-seconds",
    default=60,
    show_default=True,
    type=click.IntRange(1, None),
    help="Query range step in seconds",
)
@click.option(
    "--start",
    type=float,
    help="Range start Unix timestamp in seconds",
)
@click.option(
    "--end",
    type=float,
    help="Range end Unix timestamp in seconds",
)
@click.option(
    "--prometheus-url",
    default=PROMETHEUS_URL_DEFAULT,
    show_default=True,
    help="Prometheus URL",
)
@click.option(
    "--print-promql",
    is_flag=True,
    help="Print the final PromQL",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Print raw Prometheus JSON",
)
def main(
    fe_cluster_id: str,
    window_seconds: int,
    step_seconds: int,
    start: float,
    end: float,
    prometheus_url: str,
    print_promql: bool,
    debug: bool,
) -> int:
    promql = build_promql(fe_cluster_id)
    if print_promql:
        click.echo(f"PROMQL: {promql}")

    end_ts = end if end is not None else time.time()
    start_ts = start if start is not None else end_ts - window_seconds

    if start_ts >= end_ts:
        click.echo("Invalid time range: start must be before end.", err=True)
        return 2

    try:
        result = query_prometheus_range(
            prometheus_url, promql, start_ts, end_ts, step_seconds
        )
    except requests.RequestException as exc:
        click.echo(f"Prometheus request failed: {exc}", err=True)
        return 2

    if result.get("status") != "success":
        click.echo(json.dumps(result, indent=2, ensure_ascii=True))
        return 1

    if debug:
        click.echo(json.dumps(result, indent=2, ensure_ascii=True), err=True)

    data = result.get("data", {})
    if data.get("resultType") != "matrix":
        click.echo(json.dumps(result, indent=2, ensure_ascii=True))
        return 1

    series = data.get("result", [])
    click.echo(f"Window: {ts_to_local(start_ts)} -> {ts_to_local(end_ts)}")
    click.echo(f"Series count: {len(series)}")
    if not series:
        click.echo("No series returned.")
        return 0

    best = find_max_jump(series)
    if not best:
        click.echo("No valid samples.")
        return 0

    click.echo(
        "Max jitter jump: {:.2f} ms at {} (instance {})".format(
            best["delta"], ts_to_local(best["ts"]), best["instance"]
        )
    )
    click.echo(
        "Prev sample: {:.2f} ms at {}".format(
            best["prev_v"], ts_to_local(best["prev_ts"])
        )
    )
    click.echo(
        "Current sample: {:.2f} ms at {}".format(
            best["v"], ts_to_local(best["ts"])
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(standalone_mode=False))
