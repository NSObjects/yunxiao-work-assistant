# 云效工作助手插件

`yunxiao-work-assistant` 是一个面向 Claude Code 的云效 DevOps 插件。它通过 `alibabacloud-devops-mcp-server` 连接阿里云云效，提供组织、代码、项目、流水线、制品、应用交付、测试管理查询和受控变更能力，并保留个人工作计划与周报生成能力。

## 功能

- `yunxiao-devops-assistant`：面向云效 DevOps 日常操作，覆盖组织管理、代码管理、项目/工作项、流水线、制品仓库、应用交付和测试管理。
- `yunxiao-work-assistant`：面向个人工作流，支持查询本人工作项、生成本周工作计划、按确认清单写回预计工时和计划开始时间、结合本地 Git 生成周报。
- 内置 Yunxiao MCP 配置：通过 `npx -y alibabacloud-devops-mcp-server` 启动云效 MCP 服务。
- 可选只读保护：设置 `YUNXIAO_READ_ONLY_GUARD=1` 后，hook 会阻止云效写工具调用。

## 前置条件

- Node.js `>= 20.0.0`
- 可访问云效 OpenAPI 的个人访问令牌
- Claude Code 插件环境
- 如需生成周报中的 Git 活动，需要本地仓库可执行 `git log`

云效访问令牌需要按实际使用范围授予权限。只查询工作项时使用项目协作读权限即可；涉及流水线、代码、应用交付、测试管理或写操作时，需要补齐对应模块权限。

## 安装

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

## 配置

安装后配置插件参数：

| 配置项 | 说明 | 默认值 |
|---|---|---|
| `yunxiao_access_token` | 云效个人访问令牌，敏感字段 | 无 |
| `yunxiao_api_base_url` | 云效 API 基础地址 | `https://openapi-rdc.aliyuncs.com` |

中心站通常使用默认地址。Region 站需要填写组织专属域名，例如：

```text
https://your-org.devops.aliyuncs.com
```

插件内置 MCP 配置等价于：

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
把刚才确认的本周计划写回云效预计工时和计划开始时间。
```

插件会先输出写回清单，只有在用户明确回复“确认写回”后才执行写操作。

生成周报：

```text
结合云效工作项和当前 Git 仓库提交，生成本周周报。
```

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

## 目录结构

```text
.
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
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
2. 确认插件已加载，并且 Yunxiao MCP 服务出现在 Claude Code MCP 列表中。
3. 确认 `yunxiao_access_token` 有目标模块权限。
4. Region 站报错时，优先检查 `yunxiao_api_base_url` 是否为组织实例域名。
5. 工具不存在时，检查云效 MCP 是否启用了对应 toolset。
6. 写操作被拒绝时，检查是否设置了 `YUNXIAO_READ_ONLY_GUARD=1`。

## 许可

本项目使用 MIT License，详见 `LICENSE`。
