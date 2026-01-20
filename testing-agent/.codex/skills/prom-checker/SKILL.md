---
name: prom-checker
description: Prometheus 观测与测试状态检查。用于查询 Doris 集群 CPU 使用率、FE 查询延迟抖动等指标，或需要输出 PromQL/原始响应时使用。
---

# Prometheus 观测与测试状态检查

## 概述

使用内置脚本查询 Prometheus 指标，常用于测试期间观察 Doris 集群 CPU 与 FE 查询延迟抖动。

## 工作流

1) 明确观察目标与范围（集群 ID、时间窗口、步长）。
2) 优先读取 `.env` 中的 `PROMETHEUS_URL`（未设置时脚本使用示例地址）。
3) 选择脚本并执行，必要时开启 `--print-promql` 或 `--debug`。
4) 输出结论：先给结论，再列关键数据与命令。

## 脚本

### 1) CPU 使用率查询

脚本：`.codex/skills/prom-checker/scripts/prometheus_cpu_usage.py`

用法：
```bash
uv run python3 .codex/skills/prom-checker/scripts/prometheus_cpu_usage.py --be-cluster-id <BE_CLUSTER_ID>
```

常用参数：
- `--interval`：PromQL 区间，默认 `1m`
- `--prometheus-url`：默认读取 `PROMETHEUS_URL`
- `--print-promql`：打印最终 PromQL
- `--debug`：打印 Prometheus 原始 JSON（stderr）

输出：`job  instance  value  timestamp`

### 2) 查询延迟抖动分析

脚本：`.codex/skills/prom-checker/scripts/prometheus_query_latency_jitter.py`

用法：
```bash
uv run python3 .codex/skills/prom-checker/scripts/prometheus_query_latency_jitter.py --fe-cluster-id <FE_CLUSTER_ID>
```

常用参数：
- `--window-seconds`：时间窗口，默认 7200 秒
- `--step-seconds`：步长，默认 60 秒
- `--start`/`--end`：Unix 秒级时间戳
- `--prometheus-url`：默认读取 `PROMETHEUS_URL`
- `--print-promql`、`--debug`

输出：窗口范围、序列数量、最大抖动点、前后采样值。

## 公共模块

脚本：`.codex/skills/prom-checker/scripts/prometheus_common.py`  
用途：封装 Prometheus 即时查询与区间查询，新脚本优先复用。
