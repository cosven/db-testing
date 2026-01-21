---
name: jira-issue
description: Jira Issue 创建与提交。用于通过脚本创建/提交 Jira Issue（Bug/Task 等）、设置标签/组件/负责人/优先级，或需要预览/打印请求 payload 时使用。
---

# Jira Issue 创建与提交

## 概述

使用脚本通过 Jira REST API v2 创建 Issue，默认读取 `.env` 中的凭据。

## 工作流

1) 明确项目、Issue 类型、标题与描述。
2) 可先用 `--print-payload` 或 `--dry-run` 预览。
3) 提交后记录返回的 key/self。

## 脚本

脚本：`.codex/skills/jira-issue/scripts/jira_create_issue.py`

用法：
```bash
uv run python3 .codex/skills/jira-issue/scripts/jira_create_issue.py \
  --project-key <PROJECT_KEY> --summary "..." --description "..."
```

常用参数：
- `--env-file`：默认 `.env`，读取 `JIRA_URL`、`JIRA_TOKEN`、`JIRA_USER`
- `--auth`：`bearer` 或 `basic`（默认 bearer）
- `--project-key`：也可用 `JIRA_PROJECT`
- `--issue-type`：也可用 `JIRA_ISSUE_TYPE`，默认 Bug
- `--description-file`：从文件读取描述
- `--label`/`--component`/`--assignee`/`--priority`
- `--affects-version`/`--fix-version`：对应 Affects Version / Fix Version（可重复）
- `--print-payload`/`--dry-run`

输出：`key` 与 `self`（若返回）。

注意事项：
- `--assignee` 使用 Jira 用户名（不是邮箱），如 `laihui`

经验示例（回归发版测试失败用例）：
```bash
uv run python3 .codex/skills/jira-issue/scripts/jira_create_issue.py \
  --project-key DORIS \
  --issue-type Bug \
  --summary "回归发版测试 S3 load 因内存超限失败（regression-release #2318/#2314）" \
  --description "..." \
  --priority Highest \
  --assignee laihui \
  --label 存储小组 \
  --label 导入 \
  --affects-version enter-3.1.4 \
  --fix-version 3.1.4
```
