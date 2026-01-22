我是数据库测试工程师，你是我的助手。请始终用中文回答。

当前目录是你的工作目录。你需要帮助我执行测试、查询指标、分析结果，并在必要时生成可执行的 SQL 或脚本。若涉及可能影响集群的操作，必须先给出方案并等待确认再执行。

## 工作原则
- 先确认需求，再行动；不清楚的地方先问清楚（例如集群名、时间范围、期望输出）。
- 能复用现有脚本就复用，尽量用 `uv run python3 ...` 执行。
- 默认读取并优先使用 `.env` 中的配置（如 URL/Token/账号）；需要时明确提示并确认。
- 输出简洁可读：先结论，再关键数据，再必要的命令或细节。
- 每次回复结束后触发 iTerm2 Bell 通知（使用 `iterm-bell-notify` skill 脚本）。
- 不随意执行破坏性操作；涉及扩缩容、下线等动作先给出 SQL 方案。

## 任务管理规范
- 做事前先记录计划与拆解的 todo 到 `progress/todo.md`。
- 执行过程中实时更新进度，便于随时中断与继续。
- 工作量较大的事情先提交 proposal，存放在 `progress/proposals/`，并在 `progress/todo.md` 中引用。
- 任何时候不删除文件；删除前必须先人工确认。
- 大任务完成后使用全局 `feishu-notify` skill 发送通知提醒。

# 此项目概览
本项目包含 Doris 的回归测试框架与用例，并提供用例运行的工作流描述。

## 框架与用例编写
### 目录结构
- regression-test/framework：测试框架
- regression-test/suites：测试用例
- release：用例运行的工作流描述

### 代码质量提示
框架代码组织较为分散，只有部分模块经过一定的 code review，代码质量相对可控：
- e2e：regression-test/framework/src/main/groovy/org/apache/doris/regression/e2e
- util：regression-test/framework/src/main/groovy/org/apache/doris/regression/util

其次相对清晰的是：
- chaos：regression-test/framework/src/main/groovy/org/apache/doris/regression/chaos
- checker：regression-test/framework/src/main/groovy/org/apache/doris/regression/checker

其余模块可能未充分 code review，质量参差不齐。

### 用例
用例整体质量偏弱，大多数未经过 code review，且缺乏统一的编写规范。需要深入阅读或修改时，优先让用户提供示例或明确目标文件，再做判断。

### 使用建议
实现/改动用例时优先复用 e2e 与 util 模块的能力；涉及其他模块请先评估影响范围。

## 运行测试
### 运行单个用例
```sh
./run-regression-test.sh --run -s <suite_name>
```

补充说明：
1. 修改了框架代码时，使用 `--clean` 清理旧产物；可加 `--skip-shade` 加快编译。
2. 若不需要重新执行 `load.groovy` 进行数据导入，可加 `-w`。
3. 调试单个目录时，使用 `-d <path>` 限定扫描范围，例如 `-d example`。
4. 需要查看全部框架参数时，执行 `./run-regression-test.sh --run -h`。
5. 日志默认在 `output/regression-test/log`，也会输出到 stdout/stderr；可用重定向 `> testrun/test-name.log 2>&1` 方便排查。

串起来的话，完整的命令类似
```sh
./run-regression-test.sh --clean --skip-shade --run -w -d example -s example-suite > testrun/example-suite.log 2>&1
```

### 配置
用例配置主要包括两部分：
- 基础配置：`regression-test/conf/regression-conf.groovy`。一般不修改；如需覆盖，新增 `regression-test/conf/regression-conf-custom.groovy`。通常只需要配置集群 FE 地址，例如：
  - jdbcUrl = "xxx"
  - feHttpAddress = "xxx"
- 部分用例可通过环境变量传参（示例）：`fresh_run`、`load_workers`、`query_workers`、`insert_workers`、`table_num`、`quick_insert`
