---
name: iterm-bell-notify
description: 触发 iTerm2 Bell/系统通知，支持按次数与间隔发送；用于测试 iTerm2 通知或在回复/命令结束后提示时使用。
---

# iTerm2 Bell 通知

## 快速使用
- 确认 iTerm2 Profile 已启用 “Send Notification on Bell”。
- 触发一次 Bell：
  `uv run python3 .codex/skills/iterm-bell-notify/scripts/bell.py`

## 参数
- `--count`：触发次数，默认 3。
- `--interval`：两次之间的间隔秒数，默认 0.5。

## 执行策略
- 用户要求连续通知时，按其指定的 `--count` / `--interval` 触发。
- 需要在回复结束后提示时，先完成回复，再执行一次 Bell 脚本。
