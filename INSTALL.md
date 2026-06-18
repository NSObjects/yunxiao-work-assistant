# Codex 插件安装执行规约

你是 Codex。按本文件安装并验证当前仓库对应的 Codex plugin。

## 目标

把 `yunxiao-work-assistant-plugin` 安装为 Codex plugin，使 Codex 加载：

- `skills/` 下的全部 skill
- `yunxiao` MCP server
- 用于阿里云 SLS 分析的 `alibaba_cloud_observability` MCP server

不要把“只安装 skill”视为完成。只安装 skill 不会自动注册 MCP server。

## 执行边界

- 每一步执行前先判断当前状态，不要跳过验证。
- 不要把 AccessKey、云 token、临时凭据或任何 secret 写入本仓库。
- 用户只要求测试、dry run 或临时验证时，不要修改真实 `~/.codex/config.toml`。
- 非侵入式测试必须使用临时 `CODEX_HOME`。
- 默认通过本地 marketplace snapshot 安装整个 plugin。
- 只有在用户明确要求“只安装 skill 并手动配置 MCP”时，才使用 `skills/analyze-aliyun-sls-logs/scripts/setup_observability_mcp.py`。
- 安装后必须用 `codex mcp list` 验证 MCP 注册状态。
- 最终回复必须说明安装了什么、验证了什么、凭据是否仍缺失。

## 定位插件根目录

插件根目录必须包含 `.codex-plugin/plugin.json`、`.mcp.json` 和 `skills/`。

如果当前目录已经是插件根目录，直接使用当前目录；否则先定位插件根目录再继续。

```bash
test -f .codex-plugin/plugin.json
test -f .mcp.json
test -d skills
command -v codex
```

任意检查失败时，停止安装并报告缺失的前置条件。

## 检查当前状态

修改任何配置前，先检查当前插件和 MCP 状态：

```bash
codex plugin list
codex mcp list
```

如果 `yunxiao-work-assistant-plugin` 已安装，并且 `yunxiao` 与 `alibaba_cloud_observability` 都已启用，不要重复安装，除非用户明确要求重装或更新。直接进入验证步骤。

## 安装 Plugin

Codex 从 marketplace snapshot 安装 plugin。先基于当前仓库创建本地 marketplace snapshot，再安装 plugin。

```bash
set -euo pipefail

PLUGIN_DIR="$(pwd)"
MARKET_ROOT="${TMPDIR:-/tmp}/yunxiao-work-assistant-marketplace"

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
```

如果 `codex plugin marketplace add` 提示 marketplace 已存在，先确认它是否指向同一个 `$MARKET_ROOT`。如果指向其他目录，使用下面命令检查后再向用户报告，不要直接覆盖：

```bash
codex plugin marketplace list
```

## 验证 Plugin 和 MCP 注册

执行：

```bash
codex plugin list
codex mcp list
```

`codex mcp list` 必须包含：

```text
alibaba_cloud_observability
yunxiao
```

其中 `alibaba_cloud_observability` 应该从已安装的 plugin cache 目录启动：

```text
python3 ./skills/analyze-aliyun-sls-logs/scripts/run_observability_mcp.py
```

如果缺少 `alibaba_cloud_observability`，plugin 安装不完整，不能汇报成功。

## 验证 Observability MCP Wrapper

从 `codex plugin list` 找到已安装 plugin 路径，然后执行：

```bash
python3 /path/to/installed/yunxiao-work-assistant-plugin/skills/analyze-aliyun-sls-logs/scripts/run_observability_mcp.py --check
```

可接受结果：

- `credentials=present`：wrapper 已安装，且能看到凭据。
- `credentials=missing:ALIBABA_CLOUD_ACCESS_KEY_ID,ALIBABA_CLOUD_ACCESS_KEY_SECRET`：wrapper 已安装，但本机还需要配置凭据。

首次运行时，wrapper 可能会把官方 `aliyun/alibabacloud-observability-mcp-server` release 二进制下载到 `~/alibabacloud-observability-mcp-server`。

如果 wrapper 在输出凭据状态前失败，报告失败命令和原始错误，不要吞掉错误。

## 凭据配置

只有当用户明确要求配置本机凭据，或提供了确认可用的安全凭据来源时，才配置凭据。

推荐把阿里云凭据放到本机用户目录，不要写入仓库：

```bash
mkdir -p ~/alibabacloud-observability-mcp-server
chmod 700 ~/alibabacloud-observability-mcp-server

cat > ~/alibabacloud-observability-mcp-server/.env <<'EOF'
ALIBABA_CLOUD_ACCESS_KEY_ID=your-access-key-id
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your-access-key-secret
ALIBABA_CLOUD_REGION=cn-hangzhou
ALIBABA_CLOUD_WORKSPACE=
EOF

chmod 600 ~/alibabacloud-observability-mcp-server/.env
```

使用前必须替换占位值。不要提交这个 `.env`。

云效凭据也必须来自本机环境变量或用户确认的安全来源：

```bash
export YUNXIAO_ACCESS_TOKEN="your-yunxiao-token"
export YUNXIAO_API_BASE_URL="https://openapi-rdc.aliyuncs.com"
```

## MCP 启动语义

安装 plugin 只是注册 MCP server，不代表 MCP 会常驻后台。

当 Codex 需要列工具或调用 Observability 工具时，Codex 会按需启动 `alibaba_cloud_observability`。wrapper 随后以 stdio 模式启动官方 MCP server。

除非用户明确要求 HTTP 模式，否则不要期待或启动持久 HTTP daemon。

## 只安装 Skill 的兜底方案

仅当不能安装 plugin，且用户接受手动注册 MCP 时，才使用本方案。

```bash
codex mcp add alibaba_cloud_observability -- \
  python3 ~/.codex/skills/analyze-aliyun-sls-logs/scripts/run_observability_mcp.py

codex mcp list
python3 ~/.codex/skills/analyze-aliyun-sls-logs/scripts/run_observability_mcp.py --check
```

如果 skill 安装在其他目录，替换为实际脚本路径。

这个兜底方案不等价于完整 plugin 安装，因为它不会安装其他 plugin skills，也不会加载 plugin metadata。

## 非侵入式测试模式

当用户只要求测试安装，不允许配置真实本机 Codex 环境时，使用本模式。

```bash
set -euo pipefail

PLUGIN_DIR="$(pwd)"
TEST_CODEX_HOME="$(mktemp -d /tmp/codex-plugin-test-home.XXXXXX)"
MARKET_ROOT="$(mktemp -d /tmp/codex-plugin-marketplace.XXXXXX)"

mkdir -p "$MARKET_ROOT/plugins" "$MARKET_ROOT/.agents/plugins"
rsync -a --exclude .git "$PLUGIN_DIR/" "$MARKET_ROOT/plugins/yunxiao-work-assistant-plugin/"

cat > "$MARKET_ROOT/.agents/plugins/marketplace.json" <<'JSON'
{
  "name": "local-yunxiao-test",
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

CODEX_HOME="$TEST_CODEX_HOME" codex plugin marketplace add "$MARKET_ROOT"
CODEX_HOME="$TEST_CODEX_HOME" codex plugin add yunxiao-work-assistant-plugin@local-yunxiao-test
CODEX_HOME="$TEST_CODEX_HOME" codex mcp list
```

只有当临时 `codex mcp list` 同时包含 `alibaba_cloud_observability` 和 `yunxiao` 时，测试才算通过。

## 最终汇报

最终回复必须包含：

- 本次是真实安装还是临时测试
- plugin 安装状态
- `yunxiao` MCP 注册状态
- `alibaba_cloud_observability` MCP 注册状态
- Observability wrapper 检查结果
- 凭据已存在还是仍缺失
- 如果有失败，给出失败命令和下一步处理动作
