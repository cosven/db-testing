---
name: jenkins-test-result
description: Jenkins 测试结果排查与归档。用于通过 SSH 查看 Jenkins master 的 job/build 日志，定位最新构建、解析 build.xml/log、判断 SUCCESS/FAILURE、提取关键异常与统计，并将结论记录到 testrun/任务目录。 当用户请求“看测试结果/回归结果/最新构建日志”时使用。
---

# Jenkins 测试结果排查

## 概述

通过 SSH 获取 Jenkins 最新构建结果、关键信息与异常日志，输出结论与建议，并归档到 `testrun/` 子目录。

## 工作流

1) 明确输入
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
- 内容需脱敏，避免内网地址/账号/密钥进入仓库。

## 注意事项

- SSH 如提示 host key 变更，先人工确认再处理 `known_hosts`。
- 涉及集群影响操作前先征求确认。
