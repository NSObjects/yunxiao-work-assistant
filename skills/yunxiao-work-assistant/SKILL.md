---
name: yunxiao-work-assistant
description: 基于 Yunxiao MCP 和本地 Git 仓库生成个人工作计划与周报。用于用户要求从云效自动获取分配给自己的需求、任务、缺陷、待办工作并排本周计划，要求把周计划写回云效需求的预计工时、计划开始时间，或要求结合云效工作项与本地 Git 提交生成周报、工作总结、进展汇报时。
allowed-tools:
  - Read
  - Grep
  - Bash(git:*)
  - Bash(python3:*)
  - mcp__plugin_yunxiao-work-assistant_yunxiao__get_current_organization_info
  - mcp__plugin_yunxiao-work-assistant_yunxiao__search_projects
  - mcp__plugin_yunxiao-work-assistant_yunxiao__search_workitems
  - mcp__plugin_yunxiao-work-assistant_yunxiao__get_work_item
  - mcp__plugin_yunxiao-work-assistant_yunxiao__list_work_item_types
  - mcp__plugin_yunxiao-work-assistant_yunxiao__get_work_item_type_field_config
  - mcp__plugin_yunxiao-work-assistant_yunxiao__list_work_item_comments
  - mcp__plugin_yunxiao-work-assistant_yunxiao__list_estimated_efforts
  - mcp__plugin_yunxiao-work-assistant_yunxiao__create_estimated_effort
  - mcp__plugin_yunxiao-work-assistant_yunxiao__update_estimated_effort
  - mcp__plugin_yunxiao-work-assistant_yunxiao__update_work_item
---

# 云效工作助手

## 核心原则

- 目标只有三个：`规划工作`、`写回周计划`、`写周报`。无关流程不要展开。
- 默认只查询云效；只有用户明确要求写回周计划，且已经看到写回清单并确认后，才更新预计工时和计划开始时间。
- 默认用 `assignedTo: "self"` 查询分配给当前账号的工作项。
- 不臆造 `organizationId`、`spaceId`、用户 ID、状态、优先级和完成情况。
- 不臆造“计划开始时间”的字段 ID；必须从工作项字段配置里识别后才能调用 `update_work_item`。
- 所有输出使用简体中文。
- 工作计划可以保留工作项 ID 便于执行跟踪；周报默认不输出工作项 ID、状态 ID、优先级、`待处理/测试中` 这类字段名。

## 必要上下文

- `organizationId`：优先从用户消息、历史上下文、环境变量 `YUNXIAO_ORGANIZATION_ID` 或 `YUNXIAO_ORG_ID` 获取。
- `spaceId` / `projectId`：优先从用户消息、历史上下文、环境变量 `YUNXIAO_SPACE_ID` 或 `YUNXIAO_PROJECT_ID` 获取。
- 时间范围：
  - 工作计划默认使用“今天到本周结束”。
  - 周报默认使用当前自然周。
- Git 仓库：默认使用当前工作目录；多个仓库分别收集后合并。

参数细节见 `references/yunxiao-mcp.md`，输出格式见 `references/output-formats.md`。

## 规划工作

1. 查询本人工作项：
   - 调用 `mcp__yunxiao__search_workitems`。
   - 参数使用 `assignedTo: "self"`、`category: "Req,Task,Bug"`、`includeDetails: true`、`perPage: 100`。
   - 只查进行中、待处理、待确认、待测试等未完成状态。
2. 如果用户要求跨项目计划，先用 `mcp__yunxiao__search_projects` 找参与项目，再逐个 `spaceId` 查询。
3. 必要时补充细节：
   - 描述太短、状态不清楚、近期进展缺失时，调用 `get_work_item`。
   - 需要看本周推进痕迹时，调用 `list_work_item_comments`。
4. 估算与排期：
   - 工作计划里的每个工作项都必须包含 `预计耗时` 和 `本周分配时间`，包括今日重点、本周推进、待澄清或候补事项。
   - 如果云效有预计工时字段，优先使用云效字段；如果只有实际工时或历史工时，只能作为参考，不要写成预计工时来源。
   - 云效没有预计工时时，根据需求描述、当前状态、优先级、是否开发完成/测试中做保守估算，并明确使用“建议估算”。
   - 每个排入本周的工作项都要给出 `计划开始日期`，默认取本周实际开始推进的日期；跨天事项只写首次开始日期，不把每个时间段都写进云效字段。
   - `本周分配时间` 要写到具体日期和时间段，例如 `周二上午 2h，周三下午 3h`；不排入本周的事项写 `本周不排`，并说明原因。
   - 默认按剩余工作日做容量规划；没有可靠节假日信息时按普通工作日估算并说明假设。排期总量不要超过可用容量，至少预留 10%-20% 机动时间处理测试反馈、线上问题和会议。
   - 优先把测试中、开发完成、发布生产、阻塞项和线上问题安排在前面；大块新开发如果超过本周剩余容量，应放入候补而不是硬塞进计划。
5. 排序规则：
   - 阻塞项、线上问题、最高优先级事项优先。
   - 已在进行中的事项优先于还未启动的事项。
   - 能在本周形成明确交付的事项优先。
   - 信息缺失或依赖外部确认的事项放入待澄清。
6. 输出格式：
   - `今日重点`
   - `本周推进`
   - `待澄清或依赖`
7. 每项至少包含：
   - 工作项 ID
   - 标题
   - 当前状态
   - 预计耗时
   - 计划开始日期
   - 本周分配时间
   - 建议动作
   - 风险或依赖

## 写回周计划

1. 写回范围：
   - 只写回用户确认的工作项。
   - 默认只更新 `预计工时` 和 `计划开始时间`，不改标题、描述、负责人、状态、迭代、优先级或评论。
   - 不把“待澄清或依赖”“本周不排”的事项写入计划开始时间；如已有预计工时也不覆盖，除非用户确认覆盖。
2. 字段识别：
   - 预计工时优先用 `list_estimated_efforts` 查询现有记录。
   - 已有预计工时记录时，用 `update_estimated_effort` 更新；没有记录时，用 `create_estimated_effort` 创建。
   - 计划开始时间不在顶层参数里，必须先用 `list_work_item_types` / `get_work_item_type_field_config` 找到名称类似 `计划开始时间`、`计划开始日期`、`开始时间`、`startTime` 的字段 ID。
   - 如果字段配置里找不到可靠字段，停止写回计划开始时间，只输出需要人工确认的字段候选，不猜字段。
3. 负责人：
   - 预计工时的 `owner` 必须使用工作项负责人 userId；如果 `assignedTo` 不是 userId 或无法确认，先调用 `get_work_item` 补详情。
4. 确认清单：
   - 写回前输出 `写回清单`，列出每个工作项 ID、标题、预计工时、计划开始日期、预计工时动作（创建/更新/跳过）、计划开始字段 ID。
   - 明确说明不会改状态、负责人、优先级和描述。
   - 必须等待用户回复“确认写回”或等价明确确认，再调用写工具。
5. 写回后验证：
   - 预计工时写入后调用 `list_estimated_efforts` 验证。
   - 计划开始时间写入后调用 `get_work_item` 验证字段值。
   - 输出成功项、失败项、未写项和失败原因。

## 写周报

1. 明确时间范围；未指定时使用当前自然周。
2. 查询云效工作项：
   - 一次按 `updatedAfter` / `updatedBefore` 查本周有更新的事项。
   - 一次按 `finishTimeAfter` / `finishTimeBefore` 查本周完成的事项。
   - 合并去重。
3. 必要时补充工作项证据：
   - 重点事项调用 `get_work_item`。
   - 需要确认进展痕迹时调用 `list_work_item_comments`。
4. 收集 Git 提交：
   - 运行 `scripts/collect_git_activity.py`。
   - 默认按周报时间范围过滤。
   - 用户提供作者姓名或邮箱时追加 `--author`。
5. 关联云效与 Git：
   - 优先使用提交信息里的工作项 ID。
   - 否则用标题关键词和模块路径辅助判断。
   - 无法确认的提交单独放到 `未关联提交`。
6. 输出格式：
   - `本周完成`
   - `本周进展`
   - `问题与风险`
   - `下周计划`
   - `未关联提交`
7. 周报写法要求：
   - 每条都写成自然语言句子，默认不给人展示工作项 ID、优先级、状态字段名。
   - 把云效字段翻译成业务表达，例如把 `测试中` 写成“进入测试验证阶段”，把 `待处理` 写成“已明确、待进入开发”。
   - 先写结果，再写动作或影响，不要写成工单列表。
   - 不要把“提交了代码”写成“已经完成交付”；周报只能写已经查到的事实。

## Git 脚本

```bash
python3 <skill-dir>/scripts/collect_git_activity.py \
  --repo /path/to/repo \
  --since 2026-04-20 \
  --until 2026-04-26 \
  --format markdown
```

脚本只读取 Git 历史，不修改仓库。`work_item_refs` 只是候选引用，仍要结合云效工作项确认。
