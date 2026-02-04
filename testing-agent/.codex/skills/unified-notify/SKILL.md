---
name: unified-notify
description: 对话结束或任务完成时发送统一通知，覆盖 terminal/gui/VSCode 等环境。
---

# 统一通知（terminal/gui/VSCode）

## 适用场景
- 对话结束或任务完成，需要提醒用户
- 在 terminal、Codex GUI、VSCode 都希望有提示
 - 默认不主动使用，仅在用户明确要求或需要验证通知时使用

## 快速使用
`uv run python3 .codex/skills/unified-notify/scripts/notify.py --title "Done" --message "Task finished."`

## 参数
- `--title`：通知标题，默认 `Codex`
- `--message`：通知内容，默认 `Task finished.`
- `--mode`：`auto|terminal|gui|vscode|all`，默认 `auto`
- `--count`：bell 次数，默认 `1`
- `--interval`：bell 间隔秒，默认 `0.5`

## 执行策略
- `auto`：若检测到终端则发送 bell；同时尝试系统通知
- `terminal`：仅 bell
- `gui`：仅系统通知
- `vscode`：系统通知 + 若在终端则 bell
- `all`：系统通知 + bell

## 环境识别
- VSCode：`TERM_PROGRAM=vscode` 或存在 `VSCODE_*` 环境变量
- iTerm：`TERM_PROGRAM=iTerm.app` 或 `ITERM_SESSION_ID`
- 终端：`stdout` 为 TTY 或存在 `TERM`/`TERM_PROGRAM`

## 注意
- macOS 使用 `osascript`
- Linux 使用 `notify-send`（如存在）
- Windows 默认仅 bell + 控制台提示
