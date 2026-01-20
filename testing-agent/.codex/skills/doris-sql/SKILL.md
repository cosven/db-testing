---
name: doris-sql
description: Doris 集群 SQL 执行与查询。用于通过集群 API 获取 FE 地址并执行 SQL，支持多条 SQL 或文件输入，需输出查询结果或执行状态时使用。
---

# Doris 集群 SQL 执行

## 概述

通过集群 API 解析 FE 地址，然后使用 MySQL 协议执行 SQL。默认读取 `.env` 中 `DORIS_CLUSTER_API_URL`。

## 工作流

1) 明确集群名、SQL 与期望输出。
2) 如涉及影响集群的操作，先给出方案并等待确认。
3) 执行脚本并记录输出结果。

## 脚本

脚本：`.codex/skills/doris-sql/scripts/doris_sql_runner.py`

用法：
```bash
uv run python3 .codex/skills/doris-sql/scripts/doris_sql_runner.py \
  --cluster-name <CLUSTER_NAME> --sql "select 1"
```

常用参数：
- `--cluster-api`：默认读取 `DORIS_CLUSTER_API_URL`
- `--user`/`--password`/`--database`
- `--sql`：可重复传入多条 SQL
- `--sql-file`：从文件读取 SQL（按分号分隔）
- `--port`：覆盖 FE MySQL 端口（默认解析为 9030）
- `--timeout`：HTTP/MySQL 超时秒数

输出：查询返回表格或 `OK (N rows affected)`；FE 地址输出到 stderr。
