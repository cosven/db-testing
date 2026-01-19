我是一个数据库测试工程师，你是我的助手。后续的对话，请你全部用中文回答我。

当前目录是你的工作目录

## Prometheus CPU 使用率查询工具
脚本位置：`scripts/prometheus_cpu_usage.py`  
依赖：`requests`、`click`（用 uv 管理，先运行 `uv venv` 再运行 `uv sync`）

基本用法（必须指定 BE 集群 ID）：
`python3 scripts/prometheus_cpu_usage.py --be-cluster-id <BE_CLUSTER_ID>`

常用参数：
- `--interval`：PromQL 的区间，默认 `1m`（空数据时可改为 `5m` 等）
- `--prometheus-url`：Prometheus 地址，默认 `http://172.20.48.32:9090`
- `--print-promql`：打印最终 PromQL
- `--debug`：输出 Prometheus 原始 JSON（打印到 stderr）

输出为表格：`job  instance  value  timestamp`，每行对应一个 BE 实例的 CPU 使用率。



## Doris 集群 SQL 执行工具
脚本位置：`scripts/doris_sql_runner.py`  
依赖：`requests`、`click`、`pymysql`（用 uv 管理，先运行 `uv venv` 再运行 `uv sync`）

基本用法（必须指定集群名与 SQL）：
`python3 scripts/doris_sql_runner.py --cluster-name <CLUSTER_NAME> --sql "select 1"`

常用参数：
- `--cluster-api`：集群列表 API，默认 `http://172.20.48.32:8111/api/v1/cluster`
- `--user`/`--password`/`--database`：MySQL 连接信息
- `--sql`：可重复传入多条 SQL
- `--sql-file`：从文件读取 SQL（按分号分隔）
- `--port`：覆盖 FE MySQL 端口（默认解析为 9030）
- `--timeout`：HTTP/MySQL 超时秒数

## 编写脚本时候的 prompt
你可以使用 Python 语言来编写脚本，使用 uv + pyproject.toml 来管理项目。
常用命令：`uv venv` 创建环境，`uv sync` 安装/同步依赖。
