# 云效工作助手插件

`yunxiao-work-assistant` 是一个面向 Claude Code 和 Codex 的云效 DevOps 插件。它通过 `alibabacloud-devops-mcp-server` 连接阿里云云效，提供组织、代码、项目、流水线、制品、应用交付、测试管理查询和受控变更能力，并保留个人工作计划与周报生成能力。

## 功能

- `yunxiao-devops-assistant`：面向云效 DevOps 日常操作，覆盖组织管理、代码管理、项目/工作项、流水线、制品仓库、应用交付和测试管理。
- `yunxiao-work-assistant`：面向个人工作流，支持查询本人工作项、按当前迭代和延期旧迭代生成本周工作计划、按确认清单写回计划开始时间、计划完成时间和预计工时、为需求关联已有分支或新建开发分支、结合云效代码提交生成周报。
- 内置 Yunxiao MCP 配置：通过 `npx -y alibabacloud-devops-mcp-server` 启动云效 MCP 服务。
- 可选只读保护：设置 `YUNXIAO_READ_ONLY_GUARD=1` 后，hook 会阻止云效写工具调用。

## 前置条件

- Node.js `>= 20.0.0`
- 可访问云效 OpenAPI 的个人访问令牌
- Claude Code 或 Codex 插件环境
- 如需生成周报中的代码提交活动，需要访问云效代码管理并具备目标仓库只读权限。

云效访问令牌需要按实际使用范围授予权限。只查询工作项时使用项目协作读权限即可；涉及流水线、代码、应用交付、测试管理或写操作时，需要补齐对应模块权限。

## 安装

### Claude Code

如果插件已经发布到 Claude Code marketplace，可以在 Claude Code 中执行：

```text
/plugin marketplace add <marketplace>
/plugin install yunxiao-work-assistant@<marketplace-name>
```

本地开发或调试时，可以直接加载当前插件目录：

```bash
claude --plugin-dir /Users/lintao/workspace/tools/yunxiao/yunxiao-work-assistant-plugin
```

当前本地 marketplace 元信息位于 `.claude-plugin/marketplace.json`，插件清单位于 `.claude-plugin/plugin.json`。

### Codex

Codex 插件入口位于 `.codex-plugin/plugin.json`，可从当前插件目录作为本地插件加载：

```text
/plugin install /Users/lintao/workspace/tools/yunxiao/yunxiao-work-assistant-plugin
```

Codex manifest 使用插件目录名 `yunxiao-work-assistant-plugin` 作为插件名，符合 Codex 对“目录名与 `plugin.json` 的 `name` 一致”的要求。

Codex 使用 `.codex.mcp.json` 启动云效 MCP，默认从进程环境继承云效配置。启动 Codex 前设置：

```bash
export YUNXIAO_ACCESS_TOKEN="<your-token>"
export YUNXIAO_API_BASE_URL="https://openapi-rdc.aliyuncs.com"
```

如果使用 Region 站，把 `YUNXIAO_API_BASE_URL` 改为组织专属域名。

## 配置

Claude Code 安装后配置插件参数：

| 配置项 | 说明 | 默认值 |
|---|---|---|
| `yunxiao_access_token` | 云效个人访问令牌，敏感字段 | 无 |
| `yunxiao_api_base_url` | 云效 API 基础地址 | `https://openapi-rdc.aliyuncs.com` |

中心站通常使用默认地址。Region 站需要填写组织专属域名，例如：

```text
https://your-org.devops.aliyuncs.com
```

Claude Code 内置 MCP 配置等价于：

```json
{
  "yunxiao": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "alibabacloud-devops-mcp-server"],
    "env": {
      "YUNXIAO_ACCESS_TOKEN": "${user_config.yunxiao_access_token}",
      "YUNXIAO_API_BASE_URL": "${user_config.yunxiao_api_base_url}"
    }
  }
}
```

## 使用示例

查询云效上下文：

```text
查看我当前云效组织下参与的项目。
```

生成本周计划：

```text
根据云效里分配给我的需求、任务和缺陷，生成本周工作计划。
```

写回周计划：

```text
把刚才确认的本周计划写回云效预计工时、计划开始时间和计划完成时间。
```

插件会先输出写回清单，只有在用户明确回复“确认写回”后才执行写操作。

生成周报：

```text
结合云效工作项和云效代码提交，生成本周周报。
```

需求分支管理：

```text
给需求 ABC-123 在仓库 frontend 基于 main 新建 feature/ABC-123-login 分支，并关联到需求。
```

插件会先确认需求、仓库、来源分支和目标分支名，再等待“确认创建分支”后执行。当前 Yunxiao MCP 没有直接写入工作项“关联代码分支”区域的专用工具，插件会在工作项评论里记录仓库、分支和链接，避免臆造不存在的工具调用。

诊断流水线或部署问题：

```text
帮我查看某条流水线最近一次失败原因，并给出处理建议。
```

## 写操作安全策略

插件默认遵循“先查询、再判断、后变更”的流程。对创建、更新、删除、运行、终止、跳过、重试、发布、部署、权限移交、变量修改等动作，会先说明工具名、目标对象、提交字段、影响范围、验证方式和回滚方式。

如需强制只读，可在启动 Claude Code 前设置：

```bash
export YUNXIAO_READ_ONLY_GUARD=1
```

启用后，`hooks/block_yunxiao_writes.py` 会拒绝匹配到的云效写工具调用，只允许读取云效数据。

当前只读保护 hook 使用 Claude Code 的 `${CLAUDE_PLUGIN_ROOT}` 变量，Codex manifest 暂不挂载该 hook，避免在 Codex 下引用不存在的运行时变量。

## 目录结构

```text
.
├── .codex-plugin/
│   └── plugin.json
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
├── .codex.mcp.json
├── .mcp.json
├── hooks/
│   ├── block_yunxiao_writes.py
│   └── hooks.json
├── skills/
│   ├── yunxiao-devops-assistant/
│   └── yunxiao-work-assistant/
└── LICENSE
```

## 排障

1. 确认 Node.js 版本：`node -v`，需要 `>= 20.0.0`。
2. 确认插件已加载，并且 Yunxiao MCP 服务出现在 Claude Code 或 Codex 的 MCP 列表中。
3. 确认 `yunxiao_access_token` 有目标模块权限。
4. Region 站报错时，优先检查 `yunxiao_api_base_url` 是否为组织实例域名。
5. 工具不存在时，检查云效 MCP 是否启用了对应 toolset。
6. 写操作被拒绝时，检查是否设置了 `YUNXIAO_READ_ONLY_GUARD=1`。

## 许可

本项目使用 MIT License，详见 `LICENSE`。
