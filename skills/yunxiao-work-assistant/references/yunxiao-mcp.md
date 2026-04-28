# Yunxiao MCP 参考

## 常用工具

- `search_projects`：跨项目规划时找我参与的项目。
- `search_workitems`：计划和周报的主查询入口。
- `get_work_item`：补单个工作项详情。
- `list_work_item_comments`：补本周进展证据。
- `list_work_item_types` / `get_work_item_type_field_config`：写回计划开始时间前查字段 ID。
- `list_estimated_efforts`：写回预计工时前查是否已有记录。
- `create_estimated_effort`：没有预计工时记录时创建。
- `update_estimated_effort`：已有预计工时记录时更新。
- `update_work_item`：只用于写回计划开始时间对应的自定义字段。

不要为“规划工作”和“写周报”引入工作项创建、状态流转、评论、附件上传之类无关能力。写回周计划只允许更新预计工时和计划开始时间。

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
```

两次结果按工作项 ID 去重后再汇总。

## 评论补证据

- `list_work_item_comments`：只在工作项标题和状态不足以说明本周进展时调用。
- 不要把评论里的主观承诺直接写进周报，除非有状态变化或代码提交能印证。

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

## 写回计划开始时间

1. 先查工作项类型和字段配置，不能猜字段 ID。
2. 字段名称候选优先级：
   - `计划开始时间`
   - `计划开始日期`
   - `开始时间`
   - `startTime` / `startDate`
3. 找到唯一可信字段后再调用：

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

如果字段配置有多个候选或没有候选，输出候选字段给用户确认，不写回。
