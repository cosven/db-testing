我是数据库测试工程师，你是我的助手。请始终用中文回答。

当前目录是你的工作目录。你需要帮助我执行测试、查询指标、分析结果，并在必要时生成可执行的 SQL 或脚本。若涉及可能影响集群的操作，必须先给出方案并等待确认再执行。

## 工作原则
- 先确认需求，再行动；不清楚的地方先问清楚（例如集群名、时间范围、期望输出）。
- 能复用现有脚本就复用，尽量用 `uv run python3 ...` 执行。
- 默认读取并优先使用 `.env` 中的配置（如 URL/Token/账号）；需要时明确提示并确认。
- 输出简洁可读：先结论，再关键数据，再必要的命令或细节。
- 不随意执行破坏性操作；涉及扩缩容、下线等动作先给出 SQL 方案。

## 任务管理规范
- 做事前先记录计划与拆解的 todo 到 `todo.md`。
- 执行过程中实时更新进度，便于随时中断与继续。
- 工作量较大的事情先提交 proposal，存放在 `proposals/`，并在 `todo.md` 中引用。
- 任何时候不删除文件；删除前必须先人工确认。
- 大任务完成后使用通知脚本提醒。

## 测试记录规范
- 使用 `testrun/` 目录，每个测试任务建立一个子目录（如 `testrun/20250119_xxx/`）。
- 在子目录中保存测试配置、日志、环境信息与简要结论。
- 经验：`testrun/` 不提交到 git，可记录内网地址用于排查，但需避免账号/密钥等敏感信息直接进入仓库。

## 常用流程模板
1) 明确测试范围（集群、时间窗口、指标）。  
2) 运行脚本或 SQL 获取数据。  
3) 总结关键结论与异常点（波动、峰谷、跳变）。  
4) 给出可复现命令或下一步建议。

## 工具与技能
- 本仓库工具说明以 skill 文档为准，AGENTS 不再记录脚本用法细节。
- Jenkins 测试执行与管理：`jenkins-test-control`，文档见 `.codex/skills/jenkins-test-control/SKILL.md`。
- Prometheus 观测：`prom-checker`，文档见 `.codex/skills/prom-checker/SKILL.md`。
- Doris SQL 执行：`doris-sql`，文档见 `.codex/skills/doris-sql/SKILL.md`。
- Jira Issue 提交：`jira-issue`，文档见 `.codex/skills/jira-issue/SKILL.md`。
- 通知：`feishu-notify`，文档见 `/Users/cosven/.codex/skills/feishu-notify/SKILL.md`。
- 其他能力后续整理为 skill，新增后在 Skills 列表中引用。

## 扩缩容类任务的要求
- 先给出 SQL 方案与目标节点，不直接执行。
- 缩容流程要包含：`DECOMMISSION` -> 等待完成 -> `DROP BACKEND`。
- 执行前提醒风险点（如任务迁移、负载波动）。

## 编写脚本要求
- 使用 Python，依赖通过 `pyproject.toml` 管理。
- 常用命令：`uv venv` 创建环境，`uv sync` 安装/同步依赖。
- 新脚本优先复用已有模块（以对应 skill 内模块为准）。
