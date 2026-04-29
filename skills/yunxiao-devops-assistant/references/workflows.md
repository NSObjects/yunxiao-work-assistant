# 云效 DevOps 工作流

## 通用上下文获取

1. 如果用户没有提供组织，先用 `get_current_organization_Info` 或 `get_user_organizations` 确认 `organizationId`。
2. 如果任务涉及项目协作，先用 `search_projects` 找到 `spaceId`，再查工作项、迭代、版本、字段和工作流。
3. 如果任务涉及代码，先用 `list_repositories` 或 `get_repository` 确认仓库 ID，再查分支、文件树、提交或合并请求。
4. 如果任务涉及流水线，先用 `list_pipelines` 或 `smart_list_pipelines` 定位流水线，再查运行、任务和日志。
5. 如果任务涉及应用交付，先用 `list_applications`、`get_application`、`list_app_orchestration`、`get_env_variable_groups` 确认应用、环境和变量上下文。
6. 如果任务涉及测试，先查 `list_testcase_directories`、`get_testcase_field_config`、`list_test_plans`，再创建或更新测试对象。

## 项目与工作项

- 查任务列表：用 `search_workitems`，必要时按 `assignedTo`、`category`、`updatedAfter`、`finishTimeAfter`、状态、迭代或关键字筛选。
- 补详情：对重点工作项调用 `get_work_item`，对进展证据调用 `list_work_item_comments`。
- 查字段和工作流：创建或更新工作项前，必须读取 `list_work_item_types`、`get_work_item_type_field_config`、`get_work_item_workflow`，避免提交不存在的字段或非法状态。
- 登记工时：先查 `list_current_user_effort_records`、`list_effort_records` 或 `list_estimated_efforts`，再决定是否创建或更新记录。
- 写操作：创建、更新工作项、评论、预计工时和实际工时前，明确标题、类型、负责人、字段、状态、工时日期和关联对象。

## 代码仓库与合并请求

- 查仓库：先用 `list_repositories` 定位仓库，再用 `get_repository` 补详情。
- 查分支：用 `list_branches`、`get_branch` 确认源分支和目标分支。
- 查代码：用 `list_files` 查看目录，用 `get_file_blobs` 读取具体文件；不要在没读当前内容前调用 `update_file`。
- 查提交：用 `list_commits`、`get_commit` 追溯变更，必要时结合合并请求、流水线或部署记录交叉验证。
- 合并请求：创建前用 `get_compare` 确认 diff，用 `list_change_request` 排除重复 MR；创建后用 `get_change_request` 和评论列表验证。
- 文件写入：`create_file`、`update_file`、`delete_file` 都要确认分支、路径、提交信息、旧内容或删除原因。

## 需求与分支

- 需求、任务、缺陷都按工作项处理；先用 `get_work_item` 确认工作项，再用 `get_repository`、`get_branch` 或 `list_branches` 确认仓库和分支。
- 新建需求分支前，确认来源 `ref` 存在、目标分支不存在，并输出工作项、仓库、来源 `ref`、目标分支名、验证方式和回滚方式。
- 用户确认后调用 `create_branch`；成功后调用 `get_branch` 验证分支存在。
- 当前 Yunxiao MCP 未暴露直接写入工作项“关联代码分支”区域的专用工具，不要臆造工具名或把分支写入未知字段。需要记录关联时，用 `create_work_item_comment` 写清仓库、分支、分支链接和关联原因；后续创建合并请求时，可用 `create_change_request` 的 `workItemIds` 关联工作项。
- 输出结果时区分“已创建分支”“已在工作项评论中记录关联”“是否进入云效原生关联区未知”。

## 流水线

- 查状态：用 `smart_list_pipelines` 或 `list_pipelines` 找流水线，再用 `get_latest_pipeline_run`、`list_pipeline_runs` 和 `get_pipeline_run` 看最近运行。
- 查失败原因：先定位失败任务，再用 `list_pipeline_jobs_by_category`、`list_pipeline_job_historys`、`get_pipeline_job_run_log` 查日志。
- 运行流水线：执行 `create_pipeline_run` 前说明流水线、分支、变量、环境、是否触发部署和预期产物。
- 手动任务：执行 `execute_pipeline_job_run` 前确认任务属于哪个 run、是否会发布、是否可重复执行。
- 改 YAML：先 `get_pipeline` 读取现有配置，修改后说明差异和回滚方式，再 `update_pipeline`。
- 资源与标签：成员、owner、标签分类变更会影响权限和可见性，按高风险动作处理。

## 制品仓库

- 查仓库：用 `list_package_repositories` 确认仓库类型和范围。
- 查制品：用 `list_artifacts` 按仓库、包名、版本或时间范围筛选。
- 查详情：用 `get_artifact` 获取单个制品信息，再与流水线运行或部署物料关联。
- 输出时区分“制品已构建”“制品已发布到仓库”“制品已部署到环境”，不要把制品存在推断成已上线。

## 应用交付

- 查应用：用 `list_applications` 和 `get_application` 确认应用名称、归属和可用环境。
- 查部署：用 `list_change_orders_by_origin`、`get_change_order`、`list_change_order_versions` 和日志工具确认部署单状态。
- 查变更请求：用 `get_appstack_change_request_audit_items`、`list_appstack_change_request_executions`、`list_appstack_change_request_work_items` 汇总审批、执行和关联工作项。
- 查编排和变量：用 `list_app_orchestration`、`get_latest_orchestration`、`get_env_variable_groups`、`get_variable_group`、`list_global_vars`；输出变量值时必须脱敏。
- 创建部署单或执行发布阶段前，确认应用、环境、版本、物料、审批状态、是否生产、回滚入口和验证方式。
- 终止、取消、关闭、跳过、重试、通过/拒绝验证都按高风险动作处理。

## 测试管理

- 创建用例前，先查 `list_testcase_directories` 和 `get_testcase_field_config`，确认目录和字段配置。
- 查用例：用 `search_testcases` 和 `get_testcase`，按需求、模块、目录、负责人或状态筛选。
- 查计划：用 `list_test_plans` 获取计划，再用 `get_test_result_list` 查看计划内用例结果。
- 更新测试结果前，确认测试计划、用例、执行人、结果状态、缺陷关联和备注。
- 删除测试用例属于高风险动作，必须说明影响范围和是否有测试计划引用。

## 诊断输出模板

```markdown
**结论**
一句话说明当前状态或最可能原因。

**证据**
- 云效对象：工具返回的关键 ID、状态、时间、负责人或日志片段摘要。
- 关联证据：提交、MR、流水线运行、制品、部署单、测试结果。

**建议动作**
1. 先做低风险查询或修复。
2. 再做需要确认的写操作。
3. 最后做发布、部署或回滚相关动作。

**风险**
- 权限、状态前置条件、生产影响、回滚限制或数据缺口。
```

## 变更后验证

- 创建类：重新查询列表或详情，确认对象存在、字段正确、负责人和关联关系正确。
- 更新类：重新读取详情，确认旧值已变更为目标值。
- 运行类：查询运行详情和日志，确认状态进入预期阶段。
- 部署类：查询部署单、机器日志、发布阶段记录和关联流水线。
- 测试类：查询测试计划结果或用例详情，确认结果和备注已落库。
