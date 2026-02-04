---
name: qa-platform
description: 通过 QA 平台 API 管理集群/工作流/发版/伸缩，并解析集群 FE 信息；用于申请集群或查询 QA 平台集群信息时使用。
---

# QA 平台 API

## 适用场景
- 调用 QA 平台 `/api/v1/*` 接口（工作流、集群、发版、伸缩、Agent）。
- 申请集群、更新时长、开关机、停止/启动服务。
- 从 QA 平台集群 API 解析 FE 地址或输出集群 JSON。

## 文档
- 接口说明：`/Users/cosven/flywheels/qa/PLATFORM_API.md`

## 配置（默认读取 `.env`）
- `QA_PLATFORM_URL`：Performance 服务 base URL（例：`http://<host>:8080`）。
- `QA_PLATFORM_TOKEN`：可选鉴权 token。
- `QA_PLATFORM_TOKEN_HEADER`：可选鉴权 header 名（默认 `Authorization`）。
- `QA_PLATFORM_TIMEOUT`：请求超时秒数（默认 30）。
- `DORIS_CLUSTER_API_URL`：集群 API URL（例：`http://<host>/api/v1/cluster`）。

## 脚本

### 统一入口（推荐）
- 脚本：`.codex/skills/qa-platform/scripts/qa_platform.py`
- 常用示例：
  ```bash
  uv run python3 .codex/skills/qa-platform/scripts/qa_platform.py apply \
    --payload .codex/skills/qa-platform/assets/apply_cluster_example.json
  uv run python3 .codex/skills/qa-platform/scripts/qa_platform.py list --name <CLUSTER_NAME> --status Running
  uv run python3 .codex/skills/qa-platform/scripts/qa_platform.py get --name <CLUSTER_NAME>
  ```
  > 说明：`apply` 默认自动判断接口类型；`list` 支持 `--name/--user/--status` 过滤。
  > 提示：示例文件仅供参考，使用前请按实际集群/用户/规格改写。

### 申请集群
- 脚本：`.codex/skills/qa-platform/scripts/apply_cluster.py`
- 用法：
  ```bash
  uv run python3 .codex/skills/qa-platform/scripts/apply_cluster.py \
    --payload .codex/skills/qa-platform/assets/apply_cluster_example.json
  ```
- 说明：payload 含 `FESpecs`/`BESpecs` 时自动走 `/api/v1/cluster/custom`，否则走 `/api/v1/cluster/apply`。
- 可选：`--endpoint apply|custom|auto` 强制指定接口；`--fail-on-non-2xx/--no-fail-on-non-2xx` 控制错误退出。

### 实战示例（本次 rebalance 流程）
- 申请集群（自定义规格）：
  ```bash
  uv run python3 .codex/skills/qa-platform/scripts/apply_cluster.py \
    --payload .codex/skills/qa-platform/assets/apply_cluster_example.json \
    --output ./output/apply_cluster_response.json
  ```
- 查询集群详情并保存：
  ```bash
  uv run python3 .codex/skills/qa-platform/scripts/cluster_ops.py \
    --output ./output/cluster_get_response.json \
    get --name <CLUSTER_NAME>
  ```
- 提交部署 workflow（YAML 已修正 cluster/name）：
  ```bash
  mkdir -p ./output
  curl -sS -X POST \
    -F "file=@.codex/skills/qa-platform/assets/deploy_cluster_example.yaml" \
    "${QA_PLATFORM_URL:-http://<host>:8080}/api/v1/workflow" | tee ./output/deploy_cluster_response.json
  ```
- 跟踪 workflow 状态（10s 轮询直到结束）：
  ```bash
  uv run python3 .codex/skills/qa-platform/scripts/workflow_watch.py \
    --uid f577e68d-b937-469a-b680-3155953654e1 \
    --interval 10 \
    --log-file ./output/deploy_cluster_watch.log \
    --output ./output/deploy_cluster_status.json
  ```

### 集群管理（list/get/update-ttl/start/stop/power/release）
- 脚本：`.codex/skills/qa-platform/scripts/cluster_ops.py`
- 常用示例：
  ```bash
  uv run python3 .codex/skills/qa-platform/scripts/cluster_ops.py list
  uv run python3 .codex/skills/qa-platform/scripts/cluster_ops.py list --name <CLUSTER_NAME> --status Running
  uv run python3 .codex/skills/qa-platform/scripts/cluster_ops.py list --param user=<USER> --param phase=Running
  uv run python3 .codex/skills/qa-platform/scripts/cluster_ops.py get --name <CLUSTER_NAME>
  uv run python3 .codex/skills/qa-platform/scripts/cluster_ops.py update-ttl --name <CLUSTER_NAME> --estimated-release-at 2026-02-01T00:00:00Z --confirm
  uv run python3 .codex/skills/qa-platform/scripts/cluster_ops.py power-off --name <CLUSTER_NAME> --confirm
  ```

### 跟踪 workflow 状态
- 脚本：`.codex/skills/qa-platform/scripts/workflow_watch.py`
- 用法：
  ```bash
  uv run python3 .codex/skills/qa-platform/scripts/workflow_watch.py \
    --uid <WORKFLOW_ID> \
    --interval 10 \
    --log-file ./output/deploy_cluster_watch.log \
    --output ./output/deploy_cluster_status.json
  ```

### 解析 FE 地址
- 脚本：`.codex/skills/qa-platform/scripts/resolve_fe.py`
- 用法：
  ```bash
  uv run python3 .codex/skills/qa-platform/scripts/resolve_fe.py \
    --cluster-name <CLUSTER_NAME> \
    --cluster-api <API_URL> \
    --output hostport
  ```

## 执行注意
- 涉及集群资源申请/释放/扩缩容等操作，必须先给出方案并等待确认再执行。
- 临时一次性操作优先用 shell/curl，便于复现；可复用的流程再沉淀为 Python 脚本。
