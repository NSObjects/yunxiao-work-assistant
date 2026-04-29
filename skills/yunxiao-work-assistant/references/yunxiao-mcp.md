# Yunxiao MCP 参考

## 常用工具

- `search_projects`：跨项目规划时找我参与的项目。
- `search_workitems`：计划和周报的主查询入口。
- `get_work_item`：补单个工作项详情。
- `list_work_item_comments`：补本周进展证据。
- `create_work_item_comment`：需求分支管理时记录分支关联说明。
- `list_work_item_types` / `get_work_item_type_field_config`：写回计划开始时间和计划完成时间前查字段 ID。
- `list_estimated_efforts`：写回预计工时前查是否已有记录。
- `create_estimated_effort`：没有预计工时记录时创建。
- `update_estimated_effort`：已有预计工时记录时更新。
- `update_work_item`：只用于写回计划开始时间和计划完成时间对应的自定义字段。
- `list_repositories`：周报需要代码提交证据时定位云效 Codeup 仓库。
- `get_repository`：补仓库默认分支等详情。
- `list_branches`：按仓库确认候选分支或排除目标分支重名。
- `get_branch`：确认来源分支、已有分支或新建后的目标分支。
- `create_branch`：用户确认后为需求创建 Codeup 分支。
- `list_commits`：按仓库、分支和时间范围查询云效代码提交。
- `get_commit`：补单个提交详情。

不要为“规划工作”和“写周报”引入工作项创建、状态流转、评论、附件上传之类无关能力。写回周计划只允许更新预计工时、计划开始时间和计划完成时间。只有用户明确要求需求分支管理时，才允许用 `create_branch` 创建分支、用 `create_work_item_comment` 记录分支关联说明。

## `search_workitems` 常用参数

- `organizationId`：必填。
- `spaceId`：必填。
- `category`：固定使用 `Req,Task,Bug`。
- `assignedTo`：默认 `self`。
- `includeDetails`：默认 `true`。
- `page` / `perPage`：默认 `1 / 100`。
- `updatedAfter` / `updatedBefore`：周报按更新时间筛选。
- `finishTimeAfter` / `finishTimeBefore`：周报按完成时间筛选。

## 计划查询建议

```text
search_workitems(
  organizationId=...,
  spaceId=...,
  category="Req,Task,Bug",
  assignedTo="self",
  status="28,100005,30,32,625489,154395,165115,100010,156603,307012,142838,100011,100012",
  includeDetails=true,
  page=1,
  perPage=100
)
```

这些状态代表待确认、待处理、进行中、开发中、测试中等未完成事项。

## 周报查询建议

```text
search_workitems(..., assignedTo="self", updatedAfter=周一, updatedBefore=周日, includeDetails=true)
search_workitems(..., assignedTo="self", finishTimeAfter=周一, finishTimeBefore=周日, includeDetails=true)
list_commits(..., refName=默认分支或用户指定分支, since=周一T00:00:00Z, until=周日T23:59:59Z)
```

工作项两次结果按工作项 ID 去重后再汇总。代码提交只从云效 Codeup 查询，不读取当前工作目录的 Git 历史。

## 评论补证据

- `list_work_item_comments`：只在工作项标题和状态不足以说明本周进展时调用。
- 不要把评论里的主观承诺直接写进周报，除非有状态变化或代码提交能印证。

## 代码提交补证据

- 用户明确给出仓库时直接使用对应 `repositoryId`；没有仓库信息时先用 `list_repositories` 搜索，不要假设当前目录就是目标仓库。
- `list_commits` 的 `since` / `until` 使用云效接口要求的 `YYYY-MM-DDTHH:MM:SSZ` 格式。
- `committerIds` 只能使用明确的云效提交人 ID；不要把姓名或邮箱当作 ID 写入。
- 提交只能证明代码有变更，不能单独证明工作项已完成、已测试或已上线。

## 需求分支管理

1. 查需求和仓库：

```text
get_work_item(organizationId=..., workItemId=需求ID)
get_repository(organizationId=..., repositoryId=...)
```

2. 关联已有分支：

```text
get_branch(organizationId=..., repositoryId=..., branchName=分支名)
create_work_item_comment(
  organizationId=...,
  workItemId=需求ID,
  content="关联 Codeup 分支：仓库 ...，分支 ...，链接 ..."
)
```

3. 新建分支并记录关联：

```text
get_branch(organizationId=..., repositoryId=..., branchName=来源ref)
get_branch(organizationId=..., repositoryId=..., branchName=目标分支名)
create_branch(
  organizationId=...,
  repositoryId=...,
  branch=目标分支名,
  ref=来源ref
)
create_work_item_comment(
  organizationId=...,
  workItemId=需求ID,
  content="已创建并关联 Codeup 分支：仓库 ...，来源 ...，分支 ...，链接 ..."
)
```

`create_branch` 的输入只包含 `branch` 和 `ref`，当前 Yunxiao MCP 没有直接写入工作项“关联代码分支”区域的工具；不要给 `create_branch` 编造 `workItemIds`、`relationRecords` 或自定义字段参数。需要云效原生关联区可见时，应说明当前 MCP 能力缺口，并让用户改走云效页面或补充专用 MCP 工具。

## 写回预计工时

1. 先查：

```text
list_estimated_efforts(organizationId=..., id=工作项ID)
```

2. 已有记录：

```text
update_estimated_effort(
  organizationId=...,
  id=预计工时记录ID,
  workitemId=工作项ID,
  owner=负责人userId,
  spentTime=小时数,
  description="本周计划估算",
  workType="开发"
)
```

3. 没有记录：

```text
create_estimated_effort(
  organizationId=...,
  id=工作项ID,
  owner=负责人userId,
  spentTime=小时数,
  description="本周计划估算",
  workType="开发"
)
```

## 写回计划日期

1. 先查工作项类型和字段配置，不能猜字段 ID。
2. 计划开始字段名称候选优先级：
   - `计划开始时间`
   - `计划开始日期`
   - `开始时间`
   - `startTime` / `startDate`
3. 计划完成字段名称候选优先级：
   - `计划完成时间`
   - `计划完成日期`
   - `完成时间`
   - `结束时间`
   - `dueDate` / `endTime`
4. 找到唯一可信字段后再调用：

```text
update_work_item(
  organizationId=...,
  workItemId=工作项ID,
  updateWorkItemFields={
    customFieldValues: {
      "字段ID": "YYYY-MM-DD"
    }
  }
)
```

如果字段配置有多个候选或没有候选，输出候选字段给用户确认，不写回对应字段。
