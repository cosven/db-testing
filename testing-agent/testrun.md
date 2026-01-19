本次任务上下文摘要（便于恢复）

1) Prometheus CPU 使用率脚本
- 脚本：`scripts/prometheus_cpu_usage.py`
- Prometheus 地址：`http://172.20.48.32:9090`
- 默认 interval：`1m`（10s 会出现空结果）
- 参数：`--be-cluster-id`、`--interval`、`--prometheus-url`、`--print-promql`、`--debug`
- 依赖：`requests`、`click`

2) Doris 集群 SQL 执行脚本
- 脚本：`scripts/doris_sql_runner.py`
- 集群列表 API：`http://172.20.48.32:8111/api/v1/cluster`
- 功能：按集群名匹配集群，解析 FE（优先 `productInfo.queryHost/queryPort`，其次 FE/节点角色）后通过 MySQL 执行 SQL
- 参数：`--cluster-name`、`--cluster-api`、`--user/--password/--database`、`--sql`、`--sql-file`、`--port`、`--timeout`
- 依赖：`requests`、`click`、`pymysql`

3) 依赖与环境
- 使用 `uv` 管理依赖，`pyproject.toml` 已配置依赖
- 初始化：`uv venv`，安装依赖：`uv sync`
- 为解决 uv 构建错误，新增最小包目录 `testing_agent/__init__.py`

4) 已验证的关键执行记录
- `uv run python3 scripts/doris_sql_runner.py --cluster-name ysw-rebalance-test-0116 --sql "show data"` 可用
- FE 解析结果：`172.20.57.63:9030`
- `show data` 总量约 192,913,693,064 字节（约 179.66 GiB）

5) 近 3 小时 CPU 抖动分析（集群 ysw-rebalance-test-0116）
- 使用 Prometheus 3h 区间计算集群平均 CPU 的 min/max/stddev
- 集群平均波动：min 42.34%，max 65.17%，range 22.83%
- 波动时间（本机本地时间）：峰值约 14:25–14:45，低谷集中在 14:54 左右
- 波动较大的实例：
  - 172.20.57.64:8040（峰 14:34:51，谷 14:36:51）
  - 172.20.57.69:8040（峰 14:44:51，谷 14:54:51）
  - 172.20.57.71:8040（峰 14:25:51，谷 14:54:51）
