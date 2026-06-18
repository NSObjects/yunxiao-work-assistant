# 云效工作助手插件

`yunxiao-work-assistant-plugin` 是面向 Codex 和 Claude Code 的云效 MCP 插件。它通过 `npx -y alibabacloud-devops-mcp-server` 接入云效，提供 DevOps 查询与受控变更、Codeup MR 审核、个人工作计划与周报、阿里云 SLS 日志分析四类能力。

插件的默认工作方式是：先查询真实云效数据，再给判断；涉及高风险或非审核类写操作时，先给确认清单，得到明确确认后再执行，并在写入后回查验证。

## 当前能力

| 技能 | 适用场景 | 关键边界 |
|---|---|---|
| `yunxiao-devops-assistant` | 查询或管理云效组织、代码仓库、项目工作项、流水线、制品、应用交付、测试管理 | 不臆造对象 ID；生产、删除、发布、部署、权限、变量等高风险动作必须先确认 |
| `yunxiao-work-assistant` | 生成个人周计划、写回计划字段、需求分支管理、生成周报 | 默认查 `assignedTo: "self"`；周计划默认覆盖当前迭代和延期旧迭代；写回只限预计工时、计划开始时间、计划完成时间 |
| `yunxiao-mr-reviewer` | 审核云效 Codeup MR，读取 MR、patch set、diff、项目指南、规格和已有评论，并写入问题评论与最终总结 | 审核只基于已有证据，不运行本地测试、云效流水线或测试计划；问题评论和最终总结分开写 |
| `analyze-aliyun-sls-logs` | 分析阿里云 SLS 告警、错误峰值、日志模式变化、设备/request/trace ID 排障 | 优先聚合再抽样；缺少 SLS MCP 配置时使用插件内脚本配置 Alibaba Cloud Observability MCP |

## 安装

如果希望让 Codex 自己执行安装和验证，直接让它读取本仓库的 `INSTALL.md`。

### Codex

Codex 当前通过 marketplace snapshot 安装插件。把本插件目录放进一个本地 marketplace 后再安装：

```bash
MARKET_ROOT=/tmp/yunxiao-work-assistant-marketplace
PLUGIN_DIR=/Users/lintao/workspace/tools/yunxiao/yunxiao-work-assistant-plugin

rm -rf "$MARKET_ROOT"
mkdir -p "$MARKET_ROOT/plugins" "$MARKET_ROOT/.agents/plugins"
rsync -a --exclude .git "$PLUGIN_DIR/" "$MARKET_ROOT/plugins/yunxiao-work-assistant-plugin/"

cat > "$MARKET_ROOT/.agents/plugins/marketplace.json" <<'JSON'
{
  "name": "yunxiao-work-assistant-local",
  "plugins": [
    {
      "name": "yunxiao-work-assistant-plugin",
      "source": {"source": "local", "path": "./plugins/yunxiao-work-assistant-plugin"},
      "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
      "category": "Productivity"
    }
  ]
}
JSON

codex plugin marketplace add "$MARKET_ROOT"
codex plugin add yunxiao-work-assistant-plugin@yunxiao-work-assistant-local
codex mcp list
```

Codex 清单文件是 `.codex-plugin/plugin.json`。该清单加载 `./skills/`，并通过 `.mcp.json` 注册 `yunxiao` 和 `alibaba_cloud_observability` MCP 服务。只单独安装 skill 不会自动合并插件里的 `.mcp.json`。

### Claude Code

本地 marketplace 文件是 `.claude-plugin/marketplace.json`，插件清单是 `.claude-plugin/plugin.json`。

```text
/plugin marketplace add /Users/lintao/workspace/tools/yunxiao/yunxiao-work-assistant-plugin
/plugin install yunxiao-work-assistant@yunxiao-work-assistant-local
```

Claude Code 会加载 `./skills/`、`./hooks/hooks.json` 和 `.claude.mcp.json`。云效令牌通过插件用户配置注入到 MCP 服务环境变量中。

## 配置

### 必需条件

- Node.js `>= 18.0.0`
- 云效个人访问令牌
- 令牌权限覆盖实际要查询或变更的云效模块

### 环境变量

Codex 使用 `.mcp.json` 启动 Yunxiao MCP，默认从进程环境读取令牌和 API 地址：

```bash
export YUNXIAO_ACCESS_TOKEN="<your-token>"
export YUNXIAO_API_BASE_URL="https://openapi-rdc.aliyuncs.com"
```

中心站默认 API 地址是 `https://openapi-rdc.aliyuncs.com`。Region 站填写组织实例域名，例如：

```text
https://your-org.devops.aliyuncs.com
```

常用上下文也可以通过环境变量提供，减少每次对话里的参数补充：

```bash
export YUNXIAO_ORGANIZATION_ID="<organization-id>"
export YUNXIAO_SPACE_ID="<space-id>"
```

### Claude Code 用户配置

| 配置项 | 说明 | 默认值 |
|---|---|---|
| `yunxiao_access_token` | 云效个人访问令牌，敏感配置 | 无 |
| `yunxiao_api_base_url` | 云效 API 基础地址 | `https://openapi-rdc.aliyuncs.com` |

### MCP 工具集

不限制 toolsets 时，`alibabacloud-devops-mcp-server` 会暴露全部云效工具。需要缩小工具范围时，可通过命令行参数或环境变量配置：

```bash
npx -y alibabacloud-devops-mcp-server --toolsets=code-management,project-management
```

```bash
export DEVOPS_TOOLSETS="code-management,project-management"
```

常用 toolsets：

| toolset | 范围 |
|---|---|
| `organization-management` | 组织、部门、角色、成员 |
| `code-management` | 仓库、分支、合并请求、文件树、提交 |
| `project-management` | 项目、工作项、字段、评论、工时 |
| `pipeline-management` | 流水线、运行、任务、资源、标签、机器部署 |
| `packages-management` | 制品仓库、制品 |
| `application-delivery` | 部署单、应用、标签、变量组、发布流程 |
| `test-management` | 测试用例、测试计划、测试结果 |

## 使用方式

### DevOps 查询与受控变更

```text
使用 $yunxiao-devops-assistant 帮我检查这个云效流水线最近失败原因，先给证据和处理建议，需要执行变更时先列确认清单。
```

适合组织、项目、仓库、MR、流水线、制品、部署、应用交付、测试管理等云效对象的查询、诊断和受控写操作。写操作前必须明确工具、目标对象、提交字段、影响范围、验证方式和回滚方式。

### 个人周计划与周报

```text
使用 $yunxiao-work-assistant 读取我当前迭代和延期旧迭代的未完成事项，安排这周工作。
```

```text
使用 $yunxiao-work-assistant 根据本周云效工作项和 Codeup 提交生成周报。
```

工作计划默认每天按 8h 常规容量排期，必要时单独标注加班日期、小时数和原因。周报代码证据只来自云效 Codeup 的 `list_commits` / `get_commit`，不读取本地 Git 历史。

写回周计划时，只写：

- 预计工时
- 计划开始时间
- 计划完成时间

写回前会先识别字段 ID，输出写回清单，并等待用户明确确认。不会顺手修改标题、描述、负责人、状态、优先级、迭代或实际工时。

### 需求分支管理

```text
使用 $yunxiao-work-assistant 为这个工作项创建开发分支，来源分支用 main，创建前先确认仓库、分支名和写入方式。
```

当前 Yunxiao MCP 可以创建 Codeup 分支，但没有直接写入工作项“关联代码分支”区域的专用工具。插件会在创建或确认分支后，用工作项评论记录仓库、分支、链接和关联原因。

### Codeup MR 审核

```text
使用 $yunxiao-mr-reviewer 审核这个云效 Codeup MR，读取 diff、项目 AGENT 指南和 specs，发现明确问题就写入评论，最后发布最终总结。
```

MR 审核会形成 Review Package：实现内容、规格/验收场景、目标基线、源分支头部、测试证据、已知风险和缺失上下文。明确且可行动的问题会写成行内评论或全局问题评论；每次完整审核会单独发布最终总结评论。

审核结论使用：

- `APPROVED`
- `NEEDS_CHANGES`
- `NEEDS_CONTEXT`

### SLS 日志分析

```text
使用 $analyze-aliyun-sls-logs 分析这个 SLS 告警，时间窗口是 2026-06-18 10:00 到 10:30，项目和 logstore 是……
```

如果 Codex 里没有可用的 Alibaba Cloud Observability MCP，可以运行：

```bash
python3 skills/analyze-aliyun-sls-logs/scripts/setup_observability_mcp.py
```

通过 Codex 插件安装时，`.mcp.json` 会同时注册 `alibaba_cloud_observability` MCP；Codex 重新加载插件后会按需启动它。首次启动时插件内置 wrapper 会检查 `~/alibabacloud-observability-mcp-server`，缺失时优先下载官方 release 二进制，下载失败时再 fallback 到 clone/build。

如果是单独安装 skill 而不是安装插件，脚本会配置 `alibaba_cloud_observability` MCP，并从当前环境或 `~/alibabacloud-observability-mcp-server/.env` 同步阿里云凭据。不要把 AccessKey 或临时凭据粘贴到对话里。

## 写操作策略

- 默认先查当前状态，再决定是否变更。
- 非 MR 审核评论类写操作必须先给确认清单，并等待用户明确确认。
- 高风险动作包括删除、终止、跳过、重试、发布、部署、权限移交、变量修改、生产环境操作。
- 写入后必须用详情、列表、日志或评论查询回查结果。
- 输出时区分云效返回事实、代码或日志证据、推断建议。
- 不输出访问令牌、流水线密钥、变量组敏感值或日志中的凭据。

Claude Code 可开启只读保护：

```bash
export YUNXIAO_READ_ONLY_GUARD=1
```

启用后，`hooks/block_yunxiao_writes.py` 会拦截云效 MCP 写工具调用。

## 目录结构

```text
.
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
├── .codex-plugin/
│   └── plugin.json
├── .claude.mcp.json
├── .mcp.json
├── hooks/
│   ├── block_yunxiao_writes.py
│   └── hooks.json
├── skills/
│   ├── analyze-aliyun-sls-logs/
│   │   ├── agents/
│   │   ├── references/
│   │   ├── scripts/
│   │   └── SKILL.md
│   ├── yunxiao-devops-assistant/
│   │   ├── agents/
│   │   ├── references/
│   │   └── SKILL.md
│   ├── yunxiao-mr-reviewer/
│   │   ├── agents/
│   │   ├── references/
│   │   └── SKILL.md
│   └── yunxiao-work-assistant/
│       ├── agents/
│       ├── references/
│       └── SKILL.md
├── LICENSE
└── README.md
```

## 排障

1. 确认 Node.js：`node -v`，需要 `>= 18.0.0`。
2. 确认客户端已加载插件，且 `codex mcp list` 里存在 `yunxiao` 和 `alibaba_cloud_observability` MCP。
3. 确认 `YUNXIAO_ACCESS_TOKEN` 有目标模块权限。
4. Region 站优先检查 `YUNXIAO_API_BASE_URL` 是否是组织实例域名。
5. 工具缺失时检查 `DEVOPS_TOOLSETS` 是否只启用了部分模块。
6. 写操作被拒绝时检查 `YUNXIAO_READ_ONLY_GUARD` 是否开启。
7. SLS 分析工具不可用时，先确认是安装了整个 Codex 插件，而不是只安装了 skill；如果是单独 skill 安装，运行 `skills/analyze-aliyun-sls-logs/scripts/setup_observability_mcp.py` 并重启 Codex 会话。

## 许可

本项目使用 MIT License，详见 `LICENSE`。
