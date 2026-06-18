---
name: analyze-aliyun-sls-logs
description: Analyze Alibaba Cloud SLS logs through the Alibaba Cloud Observability MCP Server. Use when Codex needs to investigate SLS alerts, error or warn spikes, device/request/trace IDs, service incidents, log pattern changes, deployment regressions, or when the user asks to install, repair, or configure the Alibaba Cloud Observability MCP server for Codex SLS analysis.
---

# Analyze Aliyun SLS Logs

## Overview

Use this skill to turn SLS-backed production questions into evidence-first investigations. Prefer real Alibaba Cloud Observability MCP queries over pasted-log speculation whenever the user provides, or can reasonably infer, region/project/logstore/time-window context.

## Setup

If this skill was installed through the plugin, Codex should already have an `alibaba_cloud_observability` MCP server from the plugin `.mcp.json`. If the tools are still unavailable, first restart Codex so plugin MCP servers are reloaded.

If this skill was installed as a standalone skill rather than through the plugin, run:

```bash
python3 scripts/setup_observability_mcp.py
```

Resolve `scripts/setup_observability_mcp.py` relative to this `SKILL.md`; do not assume the skill is installed under `$CODEX_HOME/skills`, because it may be loaded from a plugin checkout.

The default setup uses `stdio`: Codex starts the local MCP binary on demand and passes credentials through MCP environment variables. The plugin wrapper and setup script both read these variables from the current process environment or from `~/alibabacloud-observability-mcp-server/.env`: `ALIBABA_CLOUD_ACCESS_KEY_ID`, `ALIBABA_CLOUD_ACCESS_KEY_SECRET`, `ALIBABA_CLOUD_SECURITY_TOKEN`, `ALIBABA_CLOUD_REGION`, and `ALIBABA_CLOUD_WORKSPACE`.

The script is idempotent: it checks `~/alibabacloud-observability-mcp-server`, builds the Go server only when the binary is missing, and writes/updates only the `alibaba_cloud_observability` MCP entry in `${CODEX_HOME:-$HOME/.codex}/config.toml`.

Use a persistent local HTTP server only when needed:

```bash
python3 scripts/setup_observability_mcp.py --mode http --start
```

Do not ask the user to paste AccessKey values into chat. If credentials are missing, tell the user to set them in the local shell environment or edit the server `.env` file, then rerun the setup script so Codex MCP env is updated.

Paid-tool guard: `sls_text_to_sql`, `sls_text_to_spl`, `sls_sop`, and `cms_natural_language_query` may create STAROps costs. Prefer free direct tools first. Use paid tools only when the user explicitly asks for natural-language query generation/SOP help or has approved that cost.

## Workflow

1. Fix the investigation frame.
   Capture region, project, logstore, absolute time window, service/app/container, and identifiers such as device ID, request ID, result ID, order ID, trace ID, or error text. If the user gives relative time, restate the concrete dates/times in Asia/Shanghai.

2. Discover before querying broadly.
   Use `sls_list_projects` if the project is unclear, then `sls_list_logstores` if the logstore is unclear. Avoid iterating across many projects unless the user asked for a broad sweep.

3. Start with aggregates.
   Query counts by severity, service, host/container, error class, and short time bucket before reading samples. This prevents overfitting on one scary log line.

4. Pull representative evidence.
   Sample the dominant groups, then query exact identifiers. When timeline context matters, query the target log with `|with_pack_meta`, then use `sls_get_context_logs`.

5. Compare against a control window.
   For spikes or deployment regressions, compare the incident window with the previous equivalent window using `sls_log_compare` or equivalent aggregate SQL.

6. Connect logs to code only after the runtime picture is clear.
   If the current workspace has the relevant service code, search code paths for the exact error strings, event names, and fields observed in SLS. Keep runtime facts and code inferences separate.

7. Report the conclusion with evidence.
   Lead with impact and likely cause, then show the supporting query findings. Distinguish confirmed facts from hypotheses, and call out gaps such as missing logstore, missing index fields, or insufficient permissions.

## References

Read `references/sls-analysis-playbook.md` when doing a real SLS investigation, writing queries, comparing windows, or diagnosing why an alert fired.
