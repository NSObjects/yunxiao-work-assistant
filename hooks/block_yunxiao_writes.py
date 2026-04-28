#!/usr/bin/env python3
"""拒绝 Claude Code 中的云效 MCP 写工具调用。"""

from __future__ import annotations

import json
import sys


WRITE_TOOL_SUFFIXES = {
    "create_work_item",
    "update_work_item",
    "create_work_item_comment",
    "create_workitem_attachment",
}


def main() -> int:
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
            "已阻止云效写操作：本插件只允许读取云效数据生成计划和周报，不创建、不更新、不评论、不上传附件。",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
