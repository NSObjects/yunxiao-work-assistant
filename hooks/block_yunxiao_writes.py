#!/usr/bin/env python3
"""可选拒绝 Claude Code 中的云效 MCP 写工具调用。"""

from __future__ import annotations

import json
import os
import sys


WRITE_TOOL_SUFFIXES = {
    "add_host_list_to_deploy_group",
    "add_host_list_to_host_group",
    "cancel_app_release_stage_execution",
    "cancel_appstack_change_request",
    "close_appstack_change_request",
    "create_app_orchestration",
    "create_app_tag",
    "create_application",
    "create_appstack_change_request",
    "create_branch",
    "create_change_order",
    "create_change_request",
    "create_change_request_comment",
    "create_commit_comment",
    "create_effort_record",
    "create_estimated_effort",
    "create_file",
    "create_global_var",
    "create_pipeline_from_description",
    "create_pipeline_run",
    "create_resource_member",
    "create_sprint",
    "create_system_release_workflow",
    "create_tag",
    "create_tag_group",
    "create_testcase",
    "create_testcase_directory",
    "create_variable_group",
    "create_version",
    "create_work_item",
    "create_work_item_comment",
    "create_workitem_attachment",
    "delete_app_orchestration",
    "delete_branch",
    "delete_file",
    "delete_resource_member",
    "delete_tag",
    "delete_tag_group",
    "delete_testcase",
    "delete_variable_group",
    "delete_version",
    "execute_app_release_stage",
    "execute_job_action",
    "execute_pipeline_job_run",
    "execute_system_release_stage",
    "pass_app_release_stage_validate",
    "refuse_app_release_stage_validate",
    "resume_vm_deploy_order",
    "retry_app_release_stage_pipeline",
    "retry_vm_deploy_machine",
    "skip_app_release_stage_pipeline",
    "skip_vm_deploy_machine",
    "stop_vm_deploy_order",
    "update_app_orchestration",
    "update_app_release_stage",
    "update_app_tag",
    "update_app_tag_bind",
    "update_application",
    "update_effort_record",
    "update_estimated_effort",
    "update_global_var",
    "update_pipeline",
    "update_resource_member",
    "update_resource_owner",
    "update_sprint",
    "update_system_release_stage",
    "update_tag",
    "update_tag_group",
    "update_test_result",
    "update_variable_group",
    "update_version",
    "update_work_item",
}


def main() -> int:
    # 全量 DevOps skill 需要支持受控写操作；只有显式开启只读保护时才硬拦截。
    guard_enabled = os.environ.get("YUNXIAO_READ_ONLY_GUARD", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not guard_enabled:
        return 0

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("无法解析 hook 输入，拒绝执行云效工具调用。", file=sys.stderr)
        return 2

    tool_name = str(payload.get("tool_name", ""))
    is_yunxiao_tool = "yunxiao" in tool_name.lower()
    is_write_tool = any(tool_name.endswith(suffix) for suffix in WRITE_TOOL_SUFFIXES)

    if is_yunxiao_tool and is_write_tool:
        print(
            "已阻止云效写操作：当前启用了 YUNXIAO_READ_ONLY_GUARD，只允许读取云效数据。",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
