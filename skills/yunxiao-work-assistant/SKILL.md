---
name: yunxiao-work-assistant
description: 基于 Yunxiao MCP 生成个人工作计划与周报。用于用户要求从云效自动获取分配给自己的需求、任务、缺陷、待办工作并排本周计划，要求把周计划写回云效需求的预计工时、计划开始时间，把需求关联到已有分支或为需求新建分支，或要求结合云效工作项与云效代码提交生成周报、工作总结、进展汇报时。
allowed-tools:
  - Read
  - Grep
  - mcp__plugin_yunxiao-work-assistant_yunxiao__get_current_organization_info
  - mcp__plugin_yunxiao-work-assistant_yunxiao__search_projects
  - mcp__plugin_yunxiao-work-assistant_yunxiao__search_workitems
  - mcp__plugin_yunxiao-work-assistant_yunxiao__get_work_item
  - mcp__plugin_yunxiao-work-assistant_yunxiao__list_work_item_types
  - mcp__plugin_yunxiao-work-assistant_yunxiao__get_work_item_type_field_config
  - mcp__plugin_yunxiao-work-assistant_yunxiao__list_work_item_comments
  - mcp__plugin_yunxiao-work-assistant_yunxiao__create_work_item_comment
  - mcp__plugin_yunxiao-work-assistant_yunxiao__list_sprints
  - mcp__plugin_yunxiao-work-assistant_yunxiao__list_estimated_efforts
  - mcp__plugin_yunxiao-work-assistant_yunxiao__create_estimated_effort
  - mcp__plugin_yunxiao-work-assistant_yunxiao__update_estimated_effort
  - mcp__plugin_yunxiao-work-assistant_yunxiao__update_work_item
  - mcp__plugin_yunxiao-work-assistant_yunxiao__list_repositories
  - mcp__plugin_yunxiao-work-assistant_yunxiao__get_repository
  - mcp__plugin_yunxiao-work-assistant_yunxiao__list_branches
  - mcp__plugin_yunxiao-work-assistant_yunxiao__get_branch
  - mcp__plugin_yunxiao-work-assistant_yunxiao__create_branch
  - mcp__plugin_yunxiao-work-assistant_yunxiao__list_commits
  - mcp__plugin_yunxiao-work-assistant_yunxiao__get_commit
---

# 云效工作助手

## 核心原则

- 目标只有四个：`规划工作`、`写回周计划`、`需求分支管理`、`写周报`。无关流程不要展开。
- 默认只查询云效；只有用户明确要求写回周计划，且已经看到写回清单并确认后，才更新计划开始时间、计划完成时间和预计工时。
- 为需求新建分支或记录分支关联属于写操作，必须先展示确认清单并等待明确确认。
- 实际工时不是计划字段，不能根据预计耗时或排期推断写入；只有用户明确要求登记实际工时，并给出真实已投入工时后，才能进入实际工时写回流程。
- 默认用 `assignedTo: "self"` 查询分配给当前账号的工作项。
- 不臆造 `organizationId`、`spaceId`、用户 ID、状态、优先级和完成情况。
- 不臆造“计划开始时间”和“计划完成时间”的字段 ID；必须从工作项字段配置里识别后才能调用 `update_work_item`。
- 所有输出使用简体中文。
- 工作计划可以保留工作项 ID 便于执行跟踪；周报默认不输出工作项 ID、状态 ID、优先级、`待处理/测试中` 这类字段名。

## 必要上下文

- `organizationId`：优先从用户消息、历史上下文、环境变量 `YUNXIAO_ORGANIZATION_ID` 或 `YUNXIAO_ORG_ID` 获取。
- `spaceId` / `projectId`：优先从用户消息、历史上下文、环境变量 `YUNXIAO_SPACE_ID` 或 `YUNXIAO_PROJECT_ID` 获取。
- `sprintId` / 当前迭代：
  - 用户未明确要求“全部未完成事项”“跨迭代”“历史遗留”“TODOLIST”时，工作计划默认覆盖“当前迭代事项 + 已延期的旧迭代未完成事项”。
  - 当前迭代必须通过 `list_sprints` 查询确认。优先选择 `status=DOING` 且 `startDate <= 今天 < endDate` 的迭代；如果多个迭代仍是 `DOING`，不能只看状态，必须用日期排除旧迭代。
  - 日期不覆盖今天但 `endDate < 今天` 且仍有未完成工作项的迭代，视为“延期旧迭代”；延期事项必须进入计划候选，并明确标注所属旧迭代和延期原因。
  - `TODOLIST`、无起止日期迭代默认不属于当前迭代，也不直接视为延期；除非用户明确要求安排 `TODOLIST`，否则只能放入候补或待澄清。
- 时间范围：
  - 工作计划默认使用“今天到当前迭代结束”；如果用户明确要求自然周计划，再使用“今天到本周结束”，但必须标注哪些事项跨迭代。
  - 周报默认使用当前自然周。
- 代码仓库：只查询云效 Codeup 仓库；用户未指定仓库时通过 `list_repositories` 定位，不读取本地 Git 仓库。

参数细节见 `references/yunxiao-mcp.md`，输出格式见 `references/output-formats.md`。

## 规划工作

1. 查询本人工作项：
   - 先调用 `list_sprints` 确认项目当前迭代；跨项目时每个项目分别确认当前迭代。
   - 再从 `list_sprints` 结果中识别延期旧迭代：有起止日期、`endDate < 今天`、状态仍为 `DOING` 或迭代内仍存在未完成事项。
   - 调用 `mcp__yunxiao__search_workitems`。
   - 参数使用 `assignedTo: "self"`、`category: "Req,Task,Bug"`、`includeDetails: true`、`perPage: 100`。
   - 已确认当前迭代时，必须追加 `sprint: <当前迭代ID>` 过滤查询当前迭代事项。
   - 对每个延期旧迭代，必须追加 `sprint: <延期迭代ID>` 单独查询未完成事项；不要先拉全部未完成事项再凭感觉排期。
   - 只查进行中、待处理、待确认、待测试等未完成状态。
2. 边界外事项处理：
   - 用户明确要求跨项目计划时，先用 `mcp__yunxiao__search_projects` 找参与项目，再逐个 `spaceId` 和当前迭代查询。
   - 延期旧迭代事项可以排入 `今日重点` 或 `本周推进`，但必须标注“延期旧迭代”，并优先安排测试中、发布生产、线上问题、阻塞项和小尾巴收尾。
   - 用户未要求安排 `TODOLIST` 时，不把无日期迭代、无迭代事项排入 `今日重点` 或 `本周推进`。
   - 如果发现高优先级、发布生产、线上问题、测试阻塞事项在 `TODOLIST` 或无迭代中，只能放入 `待澄清或依赖`，并说明“无明确迭代，需确认是否插入本周期”。
3. 必要时补充细节：
   - 描述太短、状态不清楚、近期进展缺失时，调用 `get_work_item`。
   - 需要看本周推进痕迹时，调用 `list_work_item_comments`。
4. 估算与排期：
   - 工作计划里的每个工作项都必须包含 `预计耗时` 和 `本周分配时间`，包括今日重点、本周推进、待澄清或候补事项。
   - 如果云效有预计工时字段，优先使用云效字段；如果只有实际工时或历史工时，只能作为参考，不要写成预计工时来源。
   - 云效没有预计工时时，根据需求描述、当前状态、优先级、是否开发完成/测试中做保守估算，并明确使用“建议估算”。
   - 每个排入本周的工作项都要给出 `计划开始日期`，默认取本周实际开始推进的日期；跨天事项只写首次开始日期，不把每个时间段都写进云效字段。
   - 每个排入本周的工作项都要给出 `计划完成日期`，默认取本周最后一次分配时间所在日期；如果计划跨到迭代结束日，取迭代结束日期。
   - `本周分配时间` 要写到具体日期和时间段，例如 `周二上午 2h，周三下午 3h`；不排入本周的事项写 `本周不排`，并说明原因。
   - 默认按剩余工作日做容量规划；没有可靠节假日信息时按普通工作日估算并说明假设。排期总量不要超过可用容量，至少预留 10%-20% 机动时间处理测试反馈、线上问题和会议。
   - 优先把测试中、开发完成、发布生产、阻塞项和线上问题安排在前面；大块新开发如果超过本周剩余容量，应放入候补而不是硬塞进计划。
5. 排序规则：
   - 阻塞项、线上问题、最高优先级事项优先。
   - 已在进行中的事项优先于还未启动的事项。
   - 能在本周形成明确交付的事项优先。
   - 信息缺失或依赖外部确认的事项放入待澄清。
6. 输出格式：
   - `计划边界`：说明组织、项目、当前迭代名称、迭代日期、容量，列出纳入计划的延期旧迭代，以及是否排除了 `TODOLIST`/无迭代事项。
   - `今日重点`
   - `本周推进`
   - `待澄清或依赖`
7. 每项至少包含：
   - 工作项 ID
   - 标题
   - 所属迭代
   - 迭代归类：当前迭代 / 延期旧迭代 / 待澄清
   - 当前状态
   - 预计耗时
   - 计划开始日期
   - 计划完成日期
   - 本周分配时间
   - 建议动作
   - 风险或依赖

## 写回周计划

1. 写回范围：
   - 只写回用户确认的工作项。
   - 默认只写回当前迭代或延期旧迭代内、已排入 `今日重点` 或 `本周推进` 的工作项。
   - 无迭代、`TODOLIST`、待澄清事项默认不写回；除非用户逐项确认“无明确迭代也写回”。
   - 默认只更新 `计划开始时间`、`计划完成时间` 和 `预计工时`，不改标题、描述、负责人、状态、迭代、优先级、实际工时或评论。
   - 不把“待澄清或依赖”“本周不排”的事项写入计划开始时间和计划完成时间；如已有预计工时也不覆盖，除非用户确认覆盖。
2. 字段识别：
   - 预计工时优先用 `list_estimated_efforts` 查询现有记录。
   - 已有预计工时记录时，用 `update_estimated_effort` 更新；没有记录时，用 `create_estimated_effort` 创建。
   - 计划开始时间和计划完成时间不在顶层参数里，必须先用 `list_work_item_types` / `get_work_item_type_field_config` 找到字段 ID。
   - 计划开始字段名称候选：`计划开始时间`、`计划开始日期`、`开始时间`、`startTime`。
   - 计划完成字段名称候选：`计划完成时间`、`计划完成日期`、`完成时间`、`结束时间`、`dueDate`、`endTime`。
   - 如果字段配置里找不到可靠字段，停止写回对应计划字段，只输出需要人工确认的字段候选，不猜字段。
   - 日期字段写入时遵循云效现有格式：开始日期使用当天 `00:00:00`，完成日期使用当天 `23:59:59`；如果字段配置明确是纯日期，则只写日期。
3. 负责人：
   - 预计工时的 `owner` 必须使用工作项负责人 userId；如果 `assignedTo` 不是 userId 或无法确认，先调用 `get_work_item` 补详情。
4. 实际工时：
   - 规划工作和写回周计划时默认不写实际工时。
   - 不能把 `预计耗时`、`本周分配时间`、历史实际工时汇总写成新的实际工时。
   - 用户明确要求登记实际工时时，必须逐项确认工作项 ID、真实已投入工时、工作日期和工作描述。
   - 优先使用云效专门的实际工时登记工具；如果当前工具只暴露 `update_work_item` 自定义字段，不要直接写 `实际工时` 字段，除非字段配置确认可编辑且用户确认“按字段覆盖实际工时”。
5. 确认清单：
   - 写回前输出 `写回清单`，列出每个工作项 ID、标题、预计工时、计划开始日期、计划完成日期、预计工时动作（创建/更新/跳过）、计划开始字段 ID、计划完成字段 ID。
   - 明确说明不会改状态、负责人、优先级、标题、描述和实际工时。
   - 必须等待用户回复“确认写回”或等价明确确认，再调用写工具。
6. 写回后验证：
   - 预计工时写入后调用 `list_estimated_efforts` 验证。
   - 计划开始时间和计划完成时间写入后调用 `get_work_item` 验证字段值。
   - 实际工时如经用户明确确认写入，也必须调用 `get_work_item` 或对应工时查询工具验证。
   - 输出成功项、失败项、未写项和失败原因。

## 需求分支管理

适用范围：用户明确要求把需求、任务或缺陷关联到已有 Codeup 分支，或为某个工作项创建开发分支。

1. 定位对象：
   - 先用 `get_work_item` 确认工作项存在、标题、负责人、状态和所属项目；不要只凭标题猜工作项。
   - 用户未给仓库时，用 `list_repositories` 搜索并让用户从候选中确认；用户给出仓库后用 `get_repository` 补默认分支和仓库地址。
   - 用户未给来源分支时，优先使用仓库默认分支；仍无法确认时停止并要求用户给出 `ref`。
2. 关联已有分支：
   - 用 `get_branch` 或 `list_branches` 确认分支存在，并记录分支 `webUrl`、名称和最近提交。
   - 当前 Yunxiao MCP 未暴露“写入工作项关联代码分支”的专用工具，不要臆造工具名或直接改未知自定义字段。
   - 在没有专用工具时，用 `create_work_item_comment` 在工作项下记录分支关联说明，内容必须包含仓库、分支名、分支链接和关联原因。
3. 新建分支：
   - 创建前用 `get_branch` 确认来源 `ref` 存在，再用 `get_branch` 或 `list_branches` 排除目标分支重名。
   - 输出确认清单：工作项 ID、标题、仓库、来源 `ref`、目标分支名、是否写入工作项评论、验证方式。
   - 必须等待用户回复“确认创建分支”“确认执行”或等价明确确认，再调用 `create_branch`。
   - `create_branch` 成功后，用返回的 `name`、`webUrl` 和来源 `ref` 创建工作项评论；如果 `webUrl` 缺失，只记录仓库 ID、分支名和来源 `ref`，不要拼造链接。
4. 变更后验证：
   - 调用 `get_branch` 验证分支存在。
   - 调用 `list_work_item_comments` 验证关联说明已写入。
   - 输出时明确区分“已创建 Codeup 分支”“已在工作项评论中记录关联”“云效原生关联区是否可见未知”。

## 写周报

1. 明确时间范围；未指定时使用当前自然周。
2. 查询云效工作项：
   - 一次按 `updatedAfter` / `updatedBefore` 查本周有更新的事项。
   - 一次按 `finishTimeAfter` / `finishTimeBefore` 查本周完成的事项。
   - 合并去重。
3. 必要时补充工作项证据：
   - 重点事项调用 `get_work_item`。
   - 需要确认进展痕迹时调用 `list_work_item_comments`。
4. 收集云效代码提交：
   - 用户提供 `repositoryId` 时直接使用；否则先用 `list_repositories` 定位云效 Codeup 仓库，必要时用 `get_repository` 补默认分支等仓库信息。
   - 对选定仓库调用 `list_commits`，按周报时间范围设置 `since` / `until`，按仓库默认分支或用户指定分支设置 `refName`。
   - 用户提供云效提交人 ID 时追加 `committerIds`；不要把 Git 作者姓名或邮箱猜成云效提交人 ID。
   - 需要补充提交详情时调用 `get_commit`。
   - 不运行本地 `git` / `python3` 脚本，不读取当前工作目录的 Git 历史。
5. 关联云效工作项与代码提交：
   - 优先使用提交标题或提交内容里的工作项 ID。
   - 否则用工作项标题关键词和仓库路径辅助判断。
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

## 云效代码提交查询

```text
list_commits(
  organizationId=...,
  repositoryId=...,
  refName=默认分支或用户指定分支,
  since="2026-04-20T00:00:00Z",
  until="2026-04-26T23:59:59Z",
  perPage=100
)
```

云效代码提交只作为进展证据，不能把“已提交代码”直接写成“已完成交付”。提交与工作项的关联只是候选判断，仍要结合云效工作项状态和评论确认。
