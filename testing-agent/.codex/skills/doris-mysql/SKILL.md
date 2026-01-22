---
name: doris-mysql
description: 通过指定 host/port 直连 Doris FE 并执行 SQL；用于已知连接地址时查询或执行 SQL。
---

# Doris MySQL 直连执行

## 概述

通过 MySQL 协议直连 Doris FE 执行 SQL，不依赖集群 API。

## 用法

脚本：`.codex/skills/doris-mysql/scripts/doris_mysql_runner.py`

```bash
uv run python3 .codex/skills/doris-mysql/scripts/doris_mysql_runner.py \
  --host <FE_HOST> --port 9030 --user root --password '***' \
  --sql "show frontends"
```

## 常用参数

- `--host`：FE 地址（或 `.env` 中 `DORIS_HOST`）
- `--port`：FE MySQL 端口（或 `.env` 中 `DORIS_PORT`，默认 9030）
- `--user` / `--password`：账号与密码（或 `.env` 中 `DORIS_USER`/`DORIS_PASSWORD`）
- `--database`：默认库（或 `.env` 中 `DORIS_DATABASE`）
- `--sql`：可重复传入多条 SQL
- `--sql-file`：从文件读取 SQL（按分号拆分）
- `--timeout`：MySQL 超时秒数

## 输出

查询返回表格，执行类语句返回 `OK (N rows affected)`。
