---
name: feishu-notify
description: "通过本仓库脚本发送飞书通知（title/markdown 或卡片），支持 webhook 或个人通知；当用户要求发送/补发飞书通知、预览通知卡片或需要生成通知命令时使用。"
---

# Feishu Notify

## Overview

使用 `scripts/notify_feishu.py` 发送飞书通知卡片，默认从 `.env` 读取配置。需要发送通知、补发通知或预览卡片时，按此流程执行。

## Quick Start

- 确认通知目标：webhook 或个人（github name）二选一。
- 确认配置来源：默认加载 `.env`，必要时用 `--env-file` 指定。
- 选择内容：`--title`/`--markdown` 用于简单卡片；`--card-json`/`--card-file` 用于复杂卡片。
- 需要预览时使用 `--print-payload` 或 `--dry-run`。

## 常用命令

发送简单卡片：
```bash
uv run python3 scripts/notify_feishu.py --title "..." --markdown "..."
```

发送复杂卡片：
```bash
uv run python3 scripts/notify_feishu.py --card-file /path/to/card.json
```

仅预览 payload：
```bash
uv run python3 scripts/notify_feishu.py --title "..." --markdown "..." --dry-run
```

## 配置要求

环境变量（默认从 `.env` 读取）：
- `FEISHU_NOTIFY_ENDPOINT`
- `FEISHU_WEBHOOK`
- `FEISHU_GITHUB_NAME`

注意事项：
- `--webhook` 与 `--name` 二选一；都未提供时依赖 `.env`。
- 如果当前目录没有 `scripts/notify_feishu.py`，先定位脚本路径或确认仓库位置。
