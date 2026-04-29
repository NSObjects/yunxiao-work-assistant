# 云效 MCP 工具目录

按官方 README 的工具列表整理。`模式` 说明：`读` 表示查询；`生成` 表示只在本地生成内容；`写` 表示创建或更新；`高风险` 表示删除、终止、跳过、拒绝、发布、部署、权限移交或可能影响生产的动作。

## 组织管理

| 工具 | 用途 | 模式 |
|---|---|---|
| `get_current_organization_Info` | 获取当前用户所在组织信息 | 读 |
| `get_user_organizations` | 获取当前用户加入的组织列表 | 读 |
| `get_organization_role` | 获取组织角色信息 | 读 |
| `get_organization_departments` | 获取组织中的部门列表 | 读 |
| `get_organization_department_info` | 获取组织中某个部门的信息 | 读 |
| `get_organization_department_ancestors` | 获取组织中部门的上级部门 | 读 |
| `get_organization_members` | 获取组织成员列表 | 读 |
| `get_organization_member_info` | 获取组织成员信息 | 读 |
| `get_organization_member_info_by_user_id` | 通过用户 ID 获取组织成员信息 | 读 |
| `search_organization_members` | 搜索组织成员 | 读 |
| `list_organization_roles` | 列出组织角色 | 读 |

## 代码管理

说明：`create_branch` 只创建 Codeup 分支，当前 MCP 入参没有工作项字段；`create_change_request` 支持通过 `workItemIds` 关联工作项。需求需要追溯分支时，先按 `references/workflows.md` 的“需求与分支”流程确认仓库和分支，再用可用工具记录关联。

| 工具 | 用途 | 模式 |
|---|---|---|
| `create_branch` | 创建分支 | 写 |
| `delete_branch` | 删除分支 | 高风险 |
| `get_branch` | 获取分支信息 | 读 |
| `list_branches` | 获取分支列表 | 读 |
| `create_file` | 创建文件 | 写 |
| `delete_file` | 删除文件 | 高风险 |
| `get_file_blobs` | 获取文件内容 | 读 |
| `list_files` | 查询文件树 | 读 |
| `update_file` | 更新文件内容 | 写 |
| `create_change_request` | 创建合并请求 | 写 |
| `create_change_request_comment` | 创建合并请求评论 | 写 |
| `get_change_request` | 查询合并请求 | 读 |
| `list_change_request_patch_sets` | 查询合并请求版本列表 | 读 |
| `list_change_request` | 查询合并请求列表 | 读 |
| `list_change_request_comments` | 查询合并请求评论列表 | 读 |
| `get_compare` | 代码比较 | 读 |
| `get_repository` | 获取仓库详情 | 读 |
| `list_repositories` | 获取仓库列表 | 读 |
| `list_commits` | 列出代码库提交记录 | 读 |
| `get_commit` | 获取提交详情 | 读 |
| `create_commit_comment` | 创建提交评论 | 写 |

## 项目管理

| 工具 | 用途 | 模式 |
|---|---|---|
| `get_project` | 获取项目详情 | 读 |
| `search_projects` | 搜索项目 | 读 |
| `get_sprint` | 获取迭代详情 | 读 |
| `list_sprints` | 获取项目中的迭代列表 | 读 |
| `create_sprint` | 创建迭代 | 写 |
| `update_sprint` | 更新迭代 | 写 |
| `search_programs` | 搜索项目集 | 读 |
| `list_program_versions` | 列出项目集版本 | 读 |
| `list_versions` | 列出项目版本 | 读 |
| `create_version` | 创建版本 | 写 |
| `update_version` | 更新版本 | 写 |
| `delete_version` | 删除版本 | 高风险 |
| `get_work_item` | 获取工作项详情 | 读 |
| `update_work_item` | 更新工作项 | 写 |
| `search_workitems` | 搜索工作项 | 读 |
| `get_work_item_types` | 获取工作项类型 | 读 |
| `create_work_item` | 创建工作项 | 写 |
| `list_all_work_item_types` | 列出组织中所有工作项类型 | 读 |
| `list_work_item_types` | 列出项目空间中工作项类型 | 读 |
| `get_work_item_type` | 获取特定工作项类型的详细信息 | 读 |
| `list_work_item_relation_work_item_types` | 列出可关联到特定工作项的工作项类型 | 读 |
| `get_work_item_type_field_config` | 获取工作项类型的字段配置 | 读 |
| `get_work_item_workflow` | 获取工作项类型的工作流信息 | 读 |
| `list_work_item_comments` | 列出特定工作项的评论 | 读 |
| `create_work_item_comment` | 为特定工作项创建评论 | 写 |
| `list_current_user_effort_records` | 获取当前用户实际工时明细，时间跨度不能超过 6 个月 | 读 |
| `list_effort_records` | 获取实际工时明细 | 读 |
| `create_effort_record` | 登记实际工时 | 写 |
| `list_estimated_efforts` | 获取预计工时明细 | 读 |
| `create_estimated_effort` | 登记预计工时 | 写 |
| `update_effort_record` | 更新登记实际工时 | 写 |
| `update_estimated_effort` | 更新登记预计工时 | 写 |

## 流水线管理

| 工具 | 用途 | 模式 |
|---|---|---|
| `get_pipeline` | 获取流水线详情 | 读 |
| `list_pipelines` | 获取流水线列表 | 读 |
| `smart_list_pipelines` | 智能查询流水线，支持自然语言时间 | 读 |
| `generate_pipeline_yaml` | 生成流水线 YAML 配置 | 生成 |
| `create_pipeline_from_description` | 根据自然语言描述生成 YAML 并创建流水线 | 写 |
| `update_pipeline` | 更新流水线 YAML 内容 | 写 |
| `create_pipeline_run` | 运行流水线 | 高风险 |
| `get_latest_pipeline_run` | 获取最新运行信息 | 读 |
| `get_pipeline_run` | 获取运行详情 | 读 |
| `list_pipeline_runs` | 获取运行历史 | 读 |
| `list_pipeline_jobs_by_category` | 获取流水线任务 | 读 |
| `list_pipeline_job_historys` | 获取任务历史 | 读 |
| `execute_pipeline_job_run` | 手动运行任务 | 高风险 |
| `get_pipeline_job_run_log` | 获取任务日志 | 读 |
| `list_service_connections` | 获取服务连接列表 | 读 |
| `create_resource_member` | 创建资源成员 | 写 |
| `delete_resource_member` | 删除资源成员 | 高风险 |
| `list_resource_members` | 获取资源成员列表 | 读 |
| `update_resource_member` | 更新资源成员 | 写 |
| `update_resource_owner` | 移交资源对象拥有者 | 高风险 |
| `create_tag` | 创建标签 | 写 |
| `create_tag_group` | 创建标签分类 | 写 |
| `list_tag_groups` | 获取流水线分类列表 | 读 |
| `delete_tag_group` | 删除标签分类 | 高风险 |
| `update_tag_group` | 更新标签分类 | 写 |
| `get_tag_group` | 获取标签分类 | 读 |
| `delete_tag` | 删除标签 | 高风险 |
| `update_tag` | 更新标签 | 写 |
| `stop_vm_deploy_order` | 终止机器部署 | 高风险 |
| `skip_vm_deploy_machine` | 跳过机器部署 | 高风险 |
| `retry_vm_deploy_machine` | 重试机器部署 | 高风险 |
| `resume_vm_deploy_order` | 继续部署单运行 | 高风险 |
| `get_vm_deploy_order` | 获取部署单详情 | 读 |
| `get_vm_deploy_machine_log` | 查询机器部署日志 | 读 |

## 应用交付

| 工具 | 用途 | 模式 |
|---|---|---|
| `create_change_order` | 创建部署单 | 高风险 |
| `list_change_order_versions` | 查看部署单版本列表 | 读 |
| `get_change_order` | 读取部署单物料和工单状态 | 读 |
| `list_change_order_job_logs` | 查询环境部署单日志 | 读 |
| `find_task_operation_log` | 查询部署任务执行日志 | 读 |
| `execute_job_action` | 操作环境部署单 | 高风险 |
| `list_change_orders_by_origin` | 根据创建来源查询部署单 | 读 |
| `create_appstack_change_request` | 创建变更请求 | 写 |
| `get_appstack_change_request_audit_items` | 获取变更请求审批项 | 读 |
| `list_appstack_change_request_executions` | 列出变更请求执行记录 | 读 |
| `list_appstack_change_request_work_items` | 列出变更请求工作项 | 读 |
| `cancel_appstack_change_request` | 取消变更请求 | 高风险 |
| `close_appstack_change_request` | 关闭变更请求 | 高风险 |
| `list_applications` | 分页获取组织中的应用列表 | 读 |
| `get_application` | 根据应用名获取应用详情 | 读 |
| `create_application` | 创建应用 | 写 |
| `update_application` | 更新应用 | 写 |
| `get_latest_orchestration` | 获取环境的最新编排 | 读 |
| `list_app_orchestration` | 列出应用编排 | 读 |
| `create_app_orchestration` | 创建应用编排 | 写 |
| `delete_app_orchestration` | 删除应用编排 | 高风险 |
| `get_app_orchestration` | 获取应用编排 | 读 |
| `update_app_orchestration` | 更新应用编排 | 写 |
| `get_env_variable_groups` | 获取环境的变量组 | 读 |
| `create_variable_group` | 创建变量组 | 写 |
| `delete_variable_group` | 删除变量组 | 高风险 |
| `get_variable_group` | 获取变量组 | 读 |
| `update_variable_group` | 更新变量组 | 高风险 |
| `get_app_variable_groups` | 获取应用的变量组 | 读 |
| `get_app_variable_groups_revision` | 获取应用变量组版本 | 读 |
| `search_app_templates` | 搜索应用模板 | 读 |
| `create_app_tag` | 创建应用标签 | 写 |
| `update_app_tag` | 更新应用标签 | 写 |
| `search_app_tags` | 搜索应用标签 | 读 |
| `update_app_tag_bind` | 更新应用标签绑定 | 写 |
| `create_global_var` | 创建全局变量组 | 写 |
| `get_global_var` | 获取全局变量组 | 读 |
| `update_global_var` | 更新全局变量组 | 高风险 |
| `list_global_vars` | 列出全局变量组 | 读 |
| `get_machine_deploy_log` | 获取机器部署日志 | 读 |
| `add_host_list_to_host_group` | 添加主机列表到主机组 | 高风险 |
| `add_host_list_to_deploy_group` | 添加主机列表到部署组 | 高风险 |
| `list_app_release_workflows` | 查询应用下所有发布流程 | 读 |
| `list_app_release_workflow_briefs` | 查询应用下所有发布流程摘要 | 读 |
| `list_system_release_workflows` | 查询系统下所有发布流程 | 读 |
| `create_system_release_workflow` | 创建系统发布流程 | 写 |
| `update_system_release_stage` | 更新系统发布流程阶段 | 高风险 |
| `execute_system_release_stage` | 执行系统发布流程阶段 | 高风险 |
| `get_app_release_workflow_stage` | 获取发布流程阶段详情 | 读 |
| `list_app_release_stage_briefs` | 查询发布流程阶段摘要列表 | 读 |
| `update_app_release_stage` | 更新应用发布流程阶段 | 高风险 |
| `list_app_release_stage_runs` | 查询发布流程阶段执行记录列表 | 读 |
| `execute_app_release_stage` | 执行变更请求的发布流程阶段 | 高风险 |
| `cancel_app_release_stage_execution` | 取消发布流程阶段执行 | 高风险 |
| `retry_app_release_stage_pipeline` | 重试发布流程阶段流水线 | 高风险 |
| `skip_app_release_stage_pipeline` | 跳过发布流程阶段流水线 | 高风险 |
| `list_app_release_stage_metadata` | 查询研发阶段执行记录集成变更信息 | 读 |
| `get_app_release_stage_pipeline_run` | 获取研发阶段流水线运行实例 | 读 |
| `pass_app_release_stage_validate` | 通过发布流程阶段验证 | 高风险 |
| `get_app_release_stage_job_log` | 查询研发阶段流水线任务运行日志 | 读 |
| `refuse_app_release_stage_validate` | 拒绝发布流程阶段验证 | 高风险 |

## 制品仓库

| 工具 | 用途 | 模式 |
|---|---|---|
| `list_package_repositories` | 查看制品仓库信息 | 读 |
| `list_artifacts` | 查询制品信息 | 读 |
| `get_artifact` | 查看单个制品信息 | 读 |

## 测试管理

| 工具 | 用途 | 模式 |
|---|---|---|
| `list_testcase_directories` | 获取测试用例目录列表 | 读 |
| `create_testcase_directory` | 创建测试用例目录 | 写 |
| `get_testcase_field_config` | 获取测试用例字段配置 | 读 |
| `create_testcase` | 创建测试用例 | 写 |
| `search_testcases` | 搜索测试用例 | 读 |
| `get_testcase` | 获取测试用例信息 | 读 |
| `delete_testcase` | 删除测试用例 | 高风险 |
| `list_test_plans` | 获取测试计划列表 | 读 |
| `get_test_result_list` | 获取测试计划中测试用例列表 | 读 |
| `update_test_result` | 更新测试结果 | 写 |
