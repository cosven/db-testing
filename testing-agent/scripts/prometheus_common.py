#!/usr/bin/env python3
import requests


PROMETHEUS_URL_DEFAULT = "http://172.20.48.32:9090"


def query_prometheus(prometheus_url: str, promql: str) -> dict:
    query_url = prometheus_url.rstrip("/") + "/api/v1/query"
    resp = requests.get(query_url, params={"query": promql}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def query_prometheus_range(
    prometheus_url: str,
    promql: str,
    start_ts: float,
    end_ts: float,
    step_seconds: int,
) -> dict:
    query_url = prometheus_url.rstrip("/") + "/api/v1/query_range"
    params = {
        "query": promql,
        "start": int(start_ts),
        "end": int(end_ts),
        "step": int(step_seconds),
    }
    resp = requests.get(query_url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()
