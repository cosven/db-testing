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

## 任务：查看 Jenkins 新测试结果
- [x] 确认任务链接/编号与日志路径
- [x] 拉取并定位关键失败/异常日志
- [x] 汇总结论与建议
- [x] 写入 testrun 子目录记录

## 任务：创建 Jenkins 测试结果排查技能
- [x] 读取 skill-creator 指南
- [x] 设计并生成技能文档
- [x] 说明使用方式并记录到能力列表
- [x] 校验并打包 skill

## 任务：移动 skills 到 ~/.codex/skills
- [x] 确认是否需要保留仓库中的 skills 副本
- [x] 执行移动并更新说明

## 任务：共享 Jenkins 技能到仓库
- [x] 拷贝 skill 到 `skills/jenkins-test-result/`
- [x] 在 AGENTS.md 标注仓库路径

## 任务：查看 skill-installer 技能说明
- [x] 读取 skill-installer 的 SKILL.md
- [x] 总结安装流程与关键注意事项

## 任务：修复 feishu-notify 技能脚本未同步问题
- [x] 明确缺失的脚本与目标位置
- [x] 核对 feishu-notify 的 SKILL.md 要求
- [x] 给出补齐方案并确认后执行

## 任务：分析 testrun/c-project-ha-test 测试状态与错误原因
- [x] 查看 testrun/c-project-ha-test 记录内容
- [x] 补充本次经验到 testrun/c-project-ha-test 记录
- [x] 获取 Jenkins SSH 连接信息/确认访问方式
- [x] 定位查询与导入报错的关键原因
- [x] 汇总当前运行状态与结论

## 任务：读取 .env 获取 Jenkins 配置并更新 AGENTS.md 约定
- [x] 查看 .env 中 Jenkins 相关配置
- [x] 在 AGENTS.md 记录自动加载 .env 的要求

## 任务：补充 Jenkins master 地址到 .env
- [x] 更新 .env 增加 JENKINS_URL

## 任务：允许 testrun 记录内网地址并更新记录
- [x] 在 AGENTS.md 更新 testrun 内网地址记录规则
- [x] 在 AGENTS.md 明确“经验”说明内网地址可记录
- [x] 在 testrun/c-project-ha-test 记录 Jenkins master 地址

## 任务：补发 c-project-ha-test 分析通知
- [x] 使用 Feishu 通知脚本发送分析结果

## 任务：停止并重建 Jenkins 测试
- [x] 明确 Jenkins job/build 与参数
- [x] 停止指定运行中的 build
- [x] 触发 rebuild 并记录触发结果
- [x] 更新 testrun 记录与通知
- [x] 新增 Jenkins 控制脚本（stop/rebuild）
- [x] 更新 jenkins-test-result 技能说明（含 stop/rebuild）

## 任务：创建 Feishu 通知 skill 并安装到全局
- [x] 初始化全局 skill 目录结构（feishu-notify）
- [x] 编写 SKILL.md 使用说明
- [x] 校验并安装到 ~/.codex/skills

## 任务：重命名 Jenkins skill（扩大范围）
- [x] 重命名目录与 frontmatter（jenkins-test-result -> jenkins-test-control）
- [x] 更新 AGENTS.md 中的名称与路径说明
- [x] 调整 SKILL.md 描述与标题

## 任务：查看重跑构建运行状态
- [x] 查询 Jenkins queue/build 状态
- [x] 更新 testrun 记录

## 任务：定位 regression-debug #93 失败原因
- [x] 获取 build #93 日志与结果
- [x] 提取关键错误与失败统计
- [x] 更新 testrun 记录并反馈

## 任务：重跑 regression-debug（用例已修复）
- [x] 明确重跑目标 build 与参数
- [x] 触发 rebuild
- [x] 更新 testrun 记录与通知

## 任务：改进 Jenkins 控制工具与技能说明
- [x] 梳理改进点并落地到脚本
- [x] 更新 jenkins-test-control 技能说明

## 任务：优化队列等待输出 build 链接
- [x] 重跑后等待 30s 获取 queue 可执行 build
- [x] 更新 jenkins-test-control 技能说明

## 任务：增强 Jenkins 控制脚本（wait/testrun）
- [x] 增加构建完成等待能力（--wait）
- [x] 增加 testrun 自动记录能力（--testrun-file）
- [x] 更新 jenkins-test-control 技能说明

## 任务：补充 queue 5606 对应 build 信息
- [x] 记录 build #94 与链接

## 任务：查看 build #94 运行状态与失败
- [x] 获取 build #94 结果与统计
- [x] 记录查询/导入失败现象

## 任务：补充 build #94 commitTxn failed 详情
- [x] 提取 commitTxn failed 上下文与交易信息
- [x] 更新 testrun 记录

## 任务：提取 build #94 commitTxn failed 完整上下文并通知
- [x] 生成 commitTxn failed 上下文日志文件
- [x] 更新 testrun 记录引用
- [x] 发送通知

## 任务：重组织高可用测试 testrun（c-project-ha-test）
- [x] 更新 testrun 结构与说明

## 任务：迁移 Jenkins 脚本并更新 AGENTS.md
- [x] 移动 Jenkins 脚本到 jenkins-test-control skill
- [x] 更新 jenkins-test-control 技能说明中的脚本路径
- [x] 更新 AGENTS.md 仅引用 skill

## 任务：创建 Prometheus 观测 skill（prom-checker）
- [x] 初始化 prom-checker skill 目录与说明
- [x] 迁移 Prometheus 脚本到 skill
- [x] 更新 AGENTS.md 引用 prom-checker

## 任务：创建 Jira skill 并迁移脚本
- [x] 初始化 jira-issue skill 目录与说明
- [x] 迁移 Jira 脚本到 skill
- [x] 更新 AGENTS.md 引用 Jira skill

## 任务：创建 Doris skill 并迁移脚本
- [x] 初始化 doris-sql skill 目录与说明
- [x] 迁移 Doris 脚本到 skill
- [x] 更新 AGENTS.md 引用 Doris skill

## 任务：重命名 testrun 目录（regression-debug-92 -> c-project-ha-test）
- [x] 确认实际目录名并执行重命名
- [x] 同步更新引用路径

## 任务：重触发高可用测试 Jenkins 任务（build #88/#94，更新标题日期）
- [x] 明确 job 名称与标题参数 key/新日期
- [x] 确认影响后触发重跑
- [x] 记录触发结果（如需写入 testrun/通知）

## 任务：停止旧的 Jenkins 构建（高可用测试）
- [x] 确认需停止的 build 编号/范围
- [x] 说明停止方案并等待确认
- [x] 执行停止并记录结果

## 任务：查看新构建运行状态与报错（build #95/#96）
- [x] 查询构建状态与日志关键报错
- [x] 记录结果并反馈
