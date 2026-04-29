# 云效工作助手插件

`yunxiao-work-assistant-plugin` 是面向 Claude Code 与 Codex 的云效 MCP 插件，内置两套技能：

- `yunxiao-devops-assistant`：覆盖组织、代码、项目/工作项、流水线、制品、应用交付、测试管理。
- `yunxiao-work-assistant`：聚焦个人周计划、计划写回、需求分支管理、周报生成。

插件通过 `npx -y alibabacloud-devops-mcp-server` 连接云效，并遵循“先查询、再判断、后变更”的执行模式。

## 技能总览

### `yunxiao-devops-assistant`

定位：通用云效 DevOps 助手，用于查询、诊断、变更规划与受控写操作。

能力范围：

- 组织管理：组织、角色、部门、成员查询。
- 代码管理：仓库、分支、提交、MR、文件树与评论。
- 项目协作：项目、迭代、版本、工作项、字段、评论、工时。
- 流水线：运行记录、任务日志、YAML 更新、资源成员与标签。
- 应用交付：部署单、变更请求、编排、变量组、发布阶段。
- 测试管理：测试目录、用例、测试计划、结果更新。

执行约束：

- 高风险动作（删除、终止、跳过、重试、发布、部署、权限移交等）必须先输出确认清单。
- 不臆造组织/项目/仓库/流水线/应用等对象 ID。
- 写操作后必须回查验证结果。

### `yunxiao-work-assistant`

定位：个人工作流助手，目标固定为四类任务：

- 规划工作
- 写回周计划
- 需求分支管理
- 写周报

关键规则：

- 默认按 `assignedTo: "self"` 查询。
- 工作计划默认覆盖“当前迭代 + 延期旧迭代未完成事项”。
- 未经用户明确确认，不执行计划写回或分支创建。
- 周报代码证据只来自云效 Codeup（`list_commits` / `get_commit`），不读取本地 Git 历史。
- 当前 MCP 不支持直接写入工作项“关联代码分支”原生区域时，改为写工作项评论记录关联。

## 与旧版相比的重点变化

- 技能结构已从“单段说明”升级为“SKILL + references + agents”三层结构。
- `yunxiao-work-assistant` 强化了计划边界：当前迭代、延期旧迭代、`TODOLIST` 区分处理。
- 写回规则收敛为：仅 `预计工时 + 计划开始时间 + 计划完成时间`，并要求字段 ID 先识别再写回。
- 周报规则收敛为：工作项双查询去重 + 云效代码提交证据 + 未关联提交单列。
- 分支管理新增明确边界：`create_branch` 只建分支，关联信息默认落评论。

## 安装

### Claude Code

从 marketplace 安装（已发布时）：

```text
/plugin marketplace add <marketplace>
/plugin install yunxiao-work-assistant@<marketplace-name>
```

本地调试：

```bash
claude --plugin-dir <plugin-dir>
```

相关清单文件：

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`

### Codex

本地安装：

```text
/plugin install <plugin-dir>
```

注意：

- Codex 清单位于 `.codex-plugin/plugin.json`。
- 本地目录名需与 `.codex-plugin/plugin.json` 的 `name` 一致（当前为 `yunxiao-work-assistant-plugin`）。
- Codex 通过 `.codex.mcp.json` 启动 Yunxiao MCP，默认从进程环境读取云效配置。
- 启动 Codex 前建议先设置 `YUNXIAO_ACCESS_TOKEN` 与 `YUNXIAO_API_BASE_URL`。

## 配置

### 必需环境

- Node.js `>= 20.0.0`
- 云效个人访问令牌（按实际任务授予权限）

### 推荐环境变量

```bash
export YUNXIAO_ACCESS_TOKEN="<your-token>"
export YUNXIAO_API_BASE_URL="https://openapi-rdc.aliyuncs.com"
```

Region 站请使用组织专属域名，例如：

```text
https://your-org.devops.aliyuncs.com
```

### Claude 用户配置项

| 配置项 | 说明 | 默认值 |
|---|---|---|
| `yunxiao_access_token` | 云效个人访问令牌（敏感） | 无 |
| `yunxiao_api_base_url` | 云效 API 基础地址 | `https://openapi-rdc.aliyuncs.com` |

## 技能使用建议

### 触发 `yunxiao-devops-assistant`

适用于：流水线失败诊断、部署问题排查、MR/仓库治理、云效模块化查询与受控变更。

示例：

```text
使用 $yunxiao-devops-assistant 帮我检查云效项目、流水线和部署风险；需要写操作时先给出确认清单。
```

### 触发 `yunxiao-work-assistant`

适用于：个人周计划、计划写回、需求分支协作、周报汇总。

示例：

```text
使用 $yunxiao-work-assistant 帮我读取云效待办，安排本周工作；需要写回计划日期、预计工时或创建需求分支时先给我确认清单。
```

## 写操作安全策略

- 默认只读查询；写操作需要用户明确确认。
- 写前应展示：工具、目标对象、提交字段、影响范围、验证方式、回滚方式。
- 写后应执行回查，输出成功项、失败项与未写项。

如需强制只读（Claude Code）：

```bash
export YUNXIAO_READ_ONLY_GUARD=1
```

启用后，`hooks/block_yunxiao_writes.py` 会拦截匹配到的云效写工具调用。

## 更新机制

- 本插件不提供独立“更新工具”。
- 技能更新时，直接让 AI 拉取或同步插件内 `skills/` 目录即可。
- `.claude-plugin/plugin.json` 与 `.codex-plugin/plugin.json` 都配置了 `"skills": "./skills/"`，会自动加载该目录。

## 目录结构

```text
.
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
├── .codex-plugin/
│   └── plugin.json
├── .mcp.json
├── .codex.mcp.json
├── hooks/
│   ├── block_yunxiao_writes.py
│   └── hooks.json
├── skills/
│   ├── yunxiao-devops-assistant/
│   │   ├── agents/
│   │   │   └── openai.yaml
│   │   ├── references/
│   │   │   ├── setup.md
│   │   │   ├── tool-catalog.md
│   │   │   └── workflows.md
│   │   └── SKILL.md
│   └── yunxiao-work-assistant/
│       ├── agents/
│       │   └── openai.yaml
│       ├── references/
│       │   ├── output-formats.md
│       │   └── yunxiao-mcp.md
│       └── SKILL.md
└── LICENSE
```

## 排障

1. 检查 Node.js：`node -v`，需 `>= 20.0.0`。
2. 检查插件是否加载，且 Yunxiao MCP 是否出现在工具列表。
3. 检查 `YUNXIAO_ACCESS_TOKEN` 权限是否覆盖目标模块。
4. Region 站错误优先核对 `YUNXIAO_API_BASE_URL`。
5. 工具缺失时检查是否限制了 `toolsets`。
6. 写操作被拒绝时检查 `YUNXIAO_READ_ONLY_GUARD=1` 是否开启。

## 许可

本项目使用 MIT License，详见 `LICENSE`。
