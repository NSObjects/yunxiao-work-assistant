# 云效工作助手

面向 Codex、Claude Code 等 Agent 的云效 Skills 集合，通过 [Alibaba Cloud DevOps MCP Server](https://github.com/aliyun/alibabacloud-devops-mcp-server) 查询和管理云效数据，并提供 Codeup MR 审核、个人工作计划、周报和阿里云 SLS 日志分析能力。

默认原则：先查询真实数据，再给判断；除 MR 审核评论外，写操作先展示确认清单，执行后回查验证。

## Skills

| Skill | 用途 |
|---|---|
| `yunxiao-devops-assistant` | 组织、代码仓库、项目、工作项、流水线、制品、应用交付和测试管理 |
| `yunxiao-work-assistant` | 个人工作计划、计划字段写回、需求分支管理和周报 |
| `yunxiao-mr-reviewer` | Codeup MR diff、规格、项目指南和评论审核 |
| `analyze-aliyun-sls-logs` | SLS 告警、错误峰值、日志模式、request/trace ID 排障 |

## 安装

前置条件：

- Node.js `>= 18`
- 云效个人访问令牌
- 已为令牌授予任务所需的云效 API 权限

安装 Skills：

```bash
npx skills add NSObjects/yunxiao-work-assistant
```

更新已安装 Skills：

```bash
# 当前项目
npx skills update --project --yes

# 全局安装
npx skills update --global --yes
```

`npx skills add` 只安装 Skills，不会自动注册 MCP Server。首次使用前还需要完成下面的云效 MCP 配置。

## 配置云效 MCP

在 MCP 客户端中添加一个 stdio 服务：

```json
{
  "mcpServers": {
    "yunxiao": {
      "command": "npx",
      "args": ["-y", "alibabacloud-devops-mcp-server"],
      "env": {
        "YUNXIAO_ACCESS_TOKEN": "<YOUR_TOKEN>",
        "YUNXIAO_API_BASE_URL": "https://openapi-rdc.aliyuncs.com"
      }
    }
  }
}
```

- 中心站可使用默认地址 `https://openapi-rdc.aliyuncs.com`。
- Region 站必须把 `YUNXIAO_API_BASE_URL` 改为组织实例域名，例如 `https://your-org.devops.aliyuncs.com`。
- 不要把访问令牌提交到仓库或粘贴到对话中；优先使用客户端的敏感配置或本机环境变量。

常用上下文也可以放在 Agent 运行环境中：

```bash
export YUNXIAO_ORGANIZATION_ID="<organization-id>"
export YUNXIAO_SPACE_ID="<space-id>"
```

默认启用全部云效工具。需要缩小范围时设置：

```bash
export DEVOPS_TOOLSETS="code-management,project-management"
```

可用 toolsets：`organization-management`、`code-management`、`project-management`、`pipeline-management`、`packages-management`、`application-delivery`、`test-management`。

## 使用示例

### DevOps 查询与变更

```text
使用 $yunxiao-devops-assistant 检查这个云效流水线最近失败的原因，先给证据和处理建议，需要变更时先列确认清单。
```

### 工作计划与周报

```text
使用 $yunxiao-work-assistant 读取我当前迭代和延期旧迭代的未完成事项，安排本周工作。
```

```text
使用 $yunxiao-work-assistant 根据本周云效工作项和 Codeup 提交生成周报。
```

计划写回仅处理预计工时、计划开始时间和计划完成时间；不会顺手修改状态、负责人、优先级或实际工时。

### 需求分支

```text
使用 $yunxiao-work-assistant 为这个工作项创建开发分支，来源分支用 main，执行前先确认仓库和分支名。
```

当前 MCP 没有工作项原生分支关联工具，因此 Skill 会使用工作项评论记录仓库、分支和关联原因。

### MR 审核

```text
使用 $yunxiao-mr-reviewer 审核这个云效 Codeup MR，读取 latest patch set diff、项目 AGENT 指南和 specs，并发布问题评论和最终总结。
```

审核范围锁定 latest patch set 的 base/source commit，只评价该 diff 内的变更。结论为 `APPROVED`、`NEEDS_CHANGES` 或 `NEEDS_CONTEXT`。

### SLS 日志分析

```text
使用 $analyze-aliyun-sls-logs 分析这个 SLS 告警，时间窗口、region、project 和 logstore 是……
```

该 Skill 需要 Alibaba Cloud Observability MCP。Codex 用户可运行 Skill 自带的配置脚本：

```bash
python3 <analyze-aliyun-sls-logs-skill-dir>/scripts/setup_observability_mcp.py
```

凭据通过本机环境变量或 `~/alibabacloud-observability-mcp-server/.env` 提供：

- `ALIBABA_CLOUD_ACCESS_KEY_ID`
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`
- `ALIBABA_CLOUD_SECURITY_TOKEN`（可选）
- `ALIBABA_CLOUD_REGION`
- `ALIBABA_CLOUD_WORKSPACE`（可选）

## 安全边界

- 不臆造组织、项目、仓库、工作项、流水线或字段 ID。
- 删除、发布、部署、终止、跳过、重试、权限和变量修改等高风险操作必须先确认。
- 写入后通过详情、列表、日志或评论查询验证结果。
- 不输出访问令牌、AccessKey、流水线密钥或变量组敏感值。
- 云效返回事实、代码或日志证据、推断建议在输出中明确区分。

## 排障

1. 运行 `node -v`，确认版本不低于 18。
2. 确认 Agent 已安装目标 Skill，并已加载名为 `yunxiao` 的 MCP Server。
3. 检查 `YUNXIAO_ACCESS_TOKEN` 权限和 `YUNXIAO_API_BASE_URL`。
4. 工具缺失时检查 `DEVOPS_TOOLSETS` 是否限制了模块。
5. SLS 工具缺失时运行 Observability MCP 配置脚本，并重启 Agent 会话。

## 开发与验证

仓库使用标准的 `skills/<name>/SKILL.md` 结构，可直接用 Skills CLI 检查发现结果：

```bash
npx skills add . --list
```

`.codex-plugin/`、`.claude-plugin/`、`.mcp.json`、`.claude.mcp.json` 和 `hooks/` 保留用于插件集成与本地开发；通过 `npx skills add` 安装时不会加载这些文件。

## License

[MIT](LICENSE)
