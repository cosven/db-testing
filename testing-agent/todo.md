## 任务：脚本与依赖/文档维护（Prometheus + Doris 工具）
- [x] 创建 pyproject.toml 并声明 requests/click 依赖
- [x] 在 pyproject.toml 增加 PyMySQL 依赖
- [x] 修复 uv sync 构建失败（添加最小包目录）
- [x] 为脚本增加 PromQL/响应调试输出选项并调整行为
- [x] 调整脚本默认 interval 为 1m
- [x] 新增 Doris 集群 SQL 执行脚本（自动获取 FE 地址）
- [x] 在 copilot.md 添加 Prometheus 工具使用说明
- [x] 在 copilot.md 添加 Doris SQL 脚本使用说明
- [x] 更新 copilot.md 增加 uv 管理依赖的用法

## 任务：集群 CPU 指标分析（近 3 小时）
- [x] 查询近 3 小时集群 CPU 统计数据
- [x] 给出 CPU 抖动结论
- [x] 定位近 3 小时 CPU 波动时间点

## 任务：todo.md 维护规范
- [x] 创建并记录待办列表到 todo.md
- [x] 更新 todo.md 标记完成并说明运行方式
- [x] 需求更新：每个事情需在 todo.md 记录
- [x] 需求更新：琐碎事项合并到一个任务记录
- [x] 更新 AGENTS.md：记录计划、拆解 todo、实时更新进度
- [x] 更新 AGENTS.md：大任务先提 proposal，存放于 proposals 并在 todo 引用
- [x] 创建 proposals 目录
- [x] 更新 AGENTS.md：任何时候不删除文件，删除前需人工确认

## 任务：定位 Jenkins 回归任务导入失败原因（streamLoadFailCount=1）
- [x] 明确 Jenkins master 登录方式与日志路径
- [x] 获取 console/构建日志并定位失败导入片段
- [x] 总结失败原因与复现/排查建议
- [x] 补充输出关键错误信息
- [x] 整理测试上下文（开始时间/报错时间/耗时）
- [x] 草拟 Jira 反馈内容
- [x] 提交 Jira（DORIS / Bug）

## 任务：配置 Jira 凭据与忽略规则
- [x] 保存 Jira 凭据到 .env
- [x] 添加 .env 到 .gitignore
- [x] 添加 .env.example 模板
- [x] 将 .env.example 中的 URL 改为示例地址
- [x] 补充 .env.example 的 Jira 默认字段

## 任务：Jira 提交脚本与能力列表
- [x] 新增 Jira 提交脚本
- [x] 更新 AGENTS.md 能力列表

## 任务：通知脚本与能力集成
- [x] 新增 Feishu 通知脚本
- [x] 更新 AGENTS.md 通知能力与规范
- [x] 更新 .env.example 通知相关变量
- [x] 配置 FEISHU_GITHUB_NAME=cosven
- [x] 发送测试通知

## 任务：内网 http 地址转 env（proposal: proposals/replace_internal_http_to_env.md）
- [x] 盘点 http:// 并分类内网地址
- [x] 设计 env 映射并更新 .env.example
- [x] 逐文件替换并复核
- [x] 将 proposal 改为中文
- [x] 完成后发送通知

## 任务：排查内网地址残留
- [x] 扫描内网 IP 与内网域名
- [x] 汇总结果与建议

## 任务：testrun 机制落地
- [x] 在 AGENTS.md 集成 testrun 记录规范
- [x] 将 testrun.md 迁移为 testrun 子任务
- [x] 完成后发送通知
- [x] 将 testrun/ 加入 .gitignore
