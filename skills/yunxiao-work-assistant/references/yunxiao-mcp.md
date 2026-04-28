# Yunxiao MCP 参考

## 只保留这几类查询

- `search_projects`：跨项目规划时找我参与的项目。
- `search_workitems`：计划和周报的主查询入口。
- `get_work_item`：补单个工作项详情。
- `list_work_item_comments`：补本周进展证据。

不要为“规划工作”和“写周报”引入创建、更新、工作流配置、附件上传之类无关能力。

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
