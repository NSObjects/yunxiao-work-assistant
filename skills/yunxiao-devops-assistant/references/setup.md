# 云效 MCP 配置参考

来源：`https://raw.githubusercontent.com/aliyun/alibabacloud-devops-mcp-server/refs/heads/master/README.zh-cn.md`，按 2026-04-28 内容整理。

## 前置条件

- Node.js 版本需要 `>= 20.0.0`。
- 需要云效个人访问令牌，按实际任务授予组织管理、项目协作、代码管理、流水线、制品仓库、应用交付、测试管理等 API 权限。
- 中心站默认 API 地址为 `https://openapi-rdc.aliyuncs.com`。
- Region 站使用组织专属域名，例如 `https://your-org.devops.aliyuncs.com`，需要配置 `YUNXIAO_API_BASE_URL`。

## Stdio 模式

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

中心站可省略 `YUNXIAO_API_BASE_URL`；Region 站必须换成组织实例地址。

## 工具集

没有指定 toolsets 时，服务默认启用全部工具。需要减少暴露工具数量时，可以用命令行参数或环境变量筛选。

```bash
npx -y alibabacloud-devops-mcp-server --toolsets=code-management,project-management
```

```bash
DEVOPS_TOOLSETS=code-management,project-management npx -y alibabacloud-devops-mcp-server
```

可用 toolsets：

| toolset | 范围 |
|---|---|
| `organization-management` | 组织、部门、角色、成员 |
| `code-management` | 仓库、分支、合并请求、文件树、提交 |
| `project-management` | 项目、工作项、字段、评论、工时 |
| `pipeline-management` | 流水线、运行、任务、资源、标签、机器部署 |
| `packages-management` | 制品仓库、制品 |
| `application-delivery` | 部署单、应用、标签、变量组、发布流程 |
| `test-management` | 测试用例、测试计划、测试结果 |

## SSE 和 Docker

SSE 适合独立运行服务或多人共享服务。服务端可以通过 `yunxiao_access_token` 查询参数或 `x-yunxiao-token` 请求头传递用户令牌。

```json
{
  "mcpServers": {
    "yunxiao": {
      "url": "http://localhost:3000/sse?yunxiao_access_token=YOUR_TOKEN_HERE"
    }
  }
}
```

如果用 Docker，官方镜像名为：

```text
build-steps-public-registry.cn-beijing.cr.aliyuncs.com/build-steps/alibabacloud-devops-mcp-server:latest
```

## 排障顺序

1. 先确认 MCP 客户端实际加载了 `yunxiao` 服务。
2. 再确认 `node -v`、`YUNXIAO_ACCESS_TOKEN`、`YUNXIAO_API_BASE_URL`。
3. Region 站报错时，优先检查 API base URL 是否写成组织实例域名。
4. 工具不存在时，检查 `DEVOPS_TOOLSETS` 是否只启用了部分模块。
5. 权限不足时，检查个人访问令牌是否包含目标模块读写权限。
