---
name: internal-doris-cluster-api
description: 通过集群 API 获取 Doris FE 地址或原始 FE 数据；用于从集群 API 解析 FE 信息时使用。
---

# Doris 集群 API（内部）

## 概述

通过集群 API 获取 Doris 集群信息，并输出 FE 数据或规范化的 `host:port` 列表。

## 用法

脚本：`.codex/skills/internal-doris-cluster-api/scripts/resolve_fe.py`

```bash
uv run python3 .codex/skills/internal-doris-cluster-api/scripts/resolve_fe.py \
  --cluster-name <CLUSTER_NAME> \
  --cluster-api <API_URL> \
  --output raw
```

## 常用参数

- `--cluster-name`：集群名（必填）
- `--cluster-api`：集群 API URL（默认读取 `DORIS_CLUSTER_API_URL`）
- `--output`：输出模式（`raw`/`hostport`/`cluster`）
  - `raw`：输出 FE 原始字段（尽量与 API 语义一致）
  - `hostport`：输出规范化 `host:port` 列表
  - `cluster`：输出完整集群 JSON
- `--env-file`：加载 `.env`（默认 `.env`）
- `--timeout`：HTTP 超时秒数

## 输出说明

- 默认输出 `raw`，用于保留 API 语义。
- 需要直连时可用 `--output hostport` 获取可直接连接的地址。
