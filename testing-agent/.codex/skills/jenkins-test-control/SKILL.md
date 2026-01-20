---
name: jenkins-test-control
description: Jenkins 测试执行与管理。用于通过 SSH 查看 Jenkins job/build 日志并归档，同时可通过 Jenkins API 查询、触发、停止、重跑构建；当需要查看测试详情、触发或停止 Jenkins 测试时使用。
---

# Jenkins 测试执行与管理

## 概述

通过 SSH 获取 Jenkins 构建结果与日志，输出结论与建议并归档到 `testrun/`；必要时通过 Jenkins API 触发、停止或重跑构建。

## 工作流

1) 明确输入与操作类型
- Jenkins master 地址、job 名称、build 编号（或“最新”）。
- Jenkins 部署目录（默认 `/mnt/hdd01/jenkins/home/`）。
- 是否需要落盘到 `testrun/` 子目录。

2) 定位 build 目录
- 目录模板：`/mnt/hdd01/jenkins/home/jobs/<job>/builds/<build>/`
- 最新 build 示例：
```bash
ssh <jenkins-host> "ls -1 /mnt/hdd01/jenkins/home/jobs/<job>/builds | grep -E '^[0-9]+$' | sort -n | tail -n 1"
```

3) 判断构建结果
- 读取 `build.xml` 中 `<result>`：
```bash
ssh <jenkins-host> "rg -n '<result>' /mnt/hdd01/jenkins/home/jobs/<job>/builds/<build>/build.xml"
```
- 如无结果，查看是否还在构建或查 console 日志的结束标记。

4) 提取关键异常/失败
- 首选关键字：`FATAL|ERROR|Exception|FAIL|FAILED|streamLoadFailCount`
```bash
ssh <jenkins-host> "rg -n 'FATAL|ERROR|Exception|FAIL|FAILED|streamLoadFailCount' /mnt/hdd01/jenkins/home/jobs/<job>/builds/<build>/log"
```
- 如需要上下文，用 `sed -n '<start>,<end>p'` 取片段。

5) 输出结论
- 先结论（SUCCESS/FAILURE/UNSTABLE），再关键异常与时间点，最后给出建议。
- 若只有构建告警（如依赖重叠），说明其性质是否影响测试结果。

6) 归档到 testrun
- 在 `testrun/<任务名>/README.md` 记录：任务信息、时间、结果、关键日志、结论。
- 内容需脱敏，避免账号/密钥进入仓库（testrun 不提交，可记录内网地址）。

## Jenkins 构建控制（停止/重跑）

脚本：`.codex/skills/jenkins-test-control/scripts/jenkins_build_control.py`  
依赖：`requests`、`click`（用 uv 管理）  

环境变量：
- `JENKINS_URL`
- `JENKINS_USER`
- `JENKINS_TOKEN`

用法：
```bash
uv run python3 .codex/skills/jenkins-test-control/scripts/jenkins_build_control.py --job <JOB> --build <BUILD> --stop --rebuild
```

查询构建状态：
```bash
uv run python3 .codex/skills/jenkins-test-control/scripts/jenkins_build_control.py --job <JOB> --build <BUILD> --status
```

查询最新构建：
```bash
uv run python3 .codex/skills/jenkins-test-control/scripts/jenkins_build_control.py --job <JOB> --latest
```

查询队列状态：
```bash
uv run python3 .codex/skills/jenkins-test-control/scripts/jenkins_build_control.py --job <JOB> --queue-id <QUEUE_ID>
```

等待构建完成并输出结果：
```bash
uv run python3 .codex/skills/jenkins-test-control/scripts/jenkins_build_control.py --job <JOB> --build <BUILD> --wait
```

写入 testrun 记录：
```bash
uv run python3 .codex/skills/jenkins-test-control/scripts/jenkins_build_control.py --job <JOB> --latest --testrun-file testrun/<task>/README.md
```

说明：
- 默认尝试 `/<build>/rebuild`，失败则回退到 `buildWithParameters`（参数来自目标 build）。
- 可用 `--param KEY=VALUE` 覆盖单个参数。
- `--queue-id/--queue-url` 可用于查看队列项是否已分配 build。
- 触发重跑时默认等待 30s 尝试获取 `queue_build_number/queue_build_url`（可用 `--queue-wait-seconds 0` 关闭）。
- `--wait` 可轮询直到构建结束，`--wait-timeout 0` 表示无限等待。
- `--testrun-file` 会追加一行构建信息到指定 README。
- 使用前先确认操作影响与目标 build。

## 注意事项

- SSH 如提示 host key 变更，先人工确认再处理 `known_hosts`。
- 涉及集群影响操作前先征求确认。
